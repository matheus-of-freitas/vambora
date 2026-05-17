"""Integration coverage for the naive-ETA PostGIS query (plan.md decision #7).

Until now `predict_stop_arrivals` was only verified manually against the live
SPPO feed. This pins the spatial behaviour against a real
Postgres+TimescaleDB+PostGIS: shape snapping, the `received_at` freshness
gate, the speed floor, direction (vehicles past the stop excluded), the
off-shape and horizon filters, and ETA ordering.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from vambora.adapters.outbound.persistence.repositories.catalog import (
    PostgresCatalogRepository,
)
from vambora.adapters.outbound.persistence.repositories.predictions import (
    PostgresPredictionRepository,
)
from vambora.adapters.outbound.persistence.repositories.vehicle_positions import (
    PostgresVehiclePositionRepository,
)
from vambora.domain.catalog import Agency, Route, Shape, Stop, StopTime, Trip
from vambora.domain.shared.types import Coordinate
from vambora.domain.tracking import VehiclePosition
from vambora.ports.outbound.gtfs_provider import GtfsBundle

pytestmark = pytest.mark.integration

# Straight shape due south along lon -43.20, lat -22.90 (fraction 0) → -22.95
# (fraction 1). The query stop sits at the midpoint (fraction ~0.5), so a
# vehicle north of it is "approaching" and one south of it is "past".
_LON = -43.20
_STOP_LAT = -22.925


def _bundle() -> GtfsBundle:
    pts = [Coordinate(latitude=-22.90 - i * 0.01, longitude=_LON) for i in range(6)]
    return GtfsBundle(
        feed_version="pred-01",
        source_url="memory://",
        agencies=[
            Agency(
                agency_id="A1",
                name="Internorte",
                url="http://x",
                timezone="America/Sao_Paulo",
                lang="pt",
            )
        ],
        routes=[
            Route(
                route_id="O639",
                agency_id="A1",
                short_name="639",
                long_name="Jardim América - Saens Peña",
                route_type=700,
                color="1B5E20",
                text_color="FFFFFF",
            )
        ],
        stops=[
            Stop(
                stop_id="S_MID",
                code=None,
                name="Meio do trajeto",
                coordinate=Coordinate(latitude=_STOP_LAT, longitude=_LON),
                parent_station=None,
                wheelchair_boarding=None,
            )
        ],
        trips=[
            Trip(
                trip_id="T1",
                route_id="O639",
                service_id="WEEKDAY",
                headsign="Saens Peña",
                direction_id=0,
                shape_id="SH1",
            )
        ],
        stop_times=[
            StopTime(
                trip_id="T1",
                stop_sequence=1,
                stop_id="S_MID",
                arrival_seconds=0,
                departure_seconds=0,
            )
        ],
        frequencies=[],
        calendars=[],
        exceptions=[],
        shapes=[Shape(shape_id="SH1", points=pts)],
    )


def _pos(
    *,
    vehicle_id: str,
    lat: float,
    lon: float = _LON,
    line_id: str = "639",
    speed_kmh: float = 0.0,
    age_seconds: int = 5,
) -> VehiclePosition:
    now = datetime.now(UTC)
    ts = now - timedelta(seconds=age_seconds)
    return VehiclePosition(
        vehicle_id=vehicle_id,
        line_id=line_id,
        recorded_at=ts,
        sent_at=ts,
        received_at=ts,
        coordinate=Coordinate(latitude=lat, longitude=lon),
        speed_kmh=speed_kmh,
        raw={"ordem": vehicle_id},
    )


_FALLBACK_KMH = 18.0
_KW = {
    "fresh_seconds": 180,
    "fallback_kmh": _FALLBACK_KMH,
    "max_horizon_seconds": 3600,
    "max_snap_m": 150.0,
    "limit": 10,
}


async def test_predicts_only_fresh_approaching_on_shape_vehicles(db) -> None:  # type: ignore[no-untyped-def]
    await PostgresCatalogRepository(db).replace_all(_bundle())
    await PostgresVehiclePositionRepository(db).upsert_many(
        [
            # Approaching, stopped → speed floored to the fallback.
            _pos(vehicle_id="V_APPROACH", lat=-22.91, speed_kmh=0.0),
            # Approaching but further from the stop, moving fast → soonest ETA.
            _pos(vehicle_id="V_FAST", lat=-22.905, speed_kmh=60.0),
            # Past the stop (fraction > stop) → excluded (sf ≤ vf).
            _pos(vehicle_id="V_PAST", lat=-22.94, speed_kmh=20.0),
            # Would approach, but stale beyond the freshness window.
            _pos(vehicle_id="V_STALE", lat=-22.91, age_seconds=3600),
            # On the line but ~10 km off the shape → snap filter.
            _pos(vehicle_id="V_OFFSHAPE", lat=-22.91, lon=-43.10),
            # Different SPPO line with no matching route → never joined.
            _pos(vehicle_id="V_WRONGLINE", lat=-22.91, line_id="999"),
        ]
    )

    preds = await PostgresPredictionRepository(db).predict_stop_arrivals(
        stop_id="S_MID", **_KW
    )

    ids = [p.vehicle_id for p in preds]
    # Only the two fresh, on-shape, approaching 639 vehicles, soonest first.
    assert ids == ["V_FAST", "V_APPROACH"]

    by_id = {p.vehicle_id: p for p in preds}
    # Stopped bus: reported 0 km/h → floored to the fallback.
    assert by_id["V_APPROACH"].speed_kmh == pytest.approx(_FALLBACK_KMH)
    # Moving bus: its own (faster) speed is used, not the floor.
    assert by_id["V_FAST"].speed_kmh == pytest.approx(60.0)
    # Farther vehicle has more remaining distance but a sooner ETA (faster).
    assert by_id["V_FAST"].distance_m > by_id["V_APPROACH"].distance_m
    assert by_id["V_FAST"].eta_seconds < by_id["V_APPROACH"].eta_seconds
    for p in preds:
        assert p.line_short_name == "639"
        assert p.route_long_name == "Jardim América - Saens Peña"
        assert p.distance_m > 0
        assert p.eta_seconds > 0
        assert p.eta_at > datetime.now(UTC)


async def test_horizon_filter_excludes_far_etas(db) -> None:  # type: ignore[no-untyped-def]
    await PostgresCatalogRepository(db).replace_all(_bundle())
    await PostgresVehiclePositionRepository(db).upsert_many(
        [_pos(vehicle_id="V_APPROACH", lat=-22.91, speed_kmh=0.0)]
    )

    # ~1.6 km at the 18 km/h floor ≈ 330 s — a 60 s horizon drops it.
    preds = await PostgresPredictionRepository(db).predict_stop_arrivals(
        stop_id="S_MID",
        fresh_seconds=180,
        fallback_kmh=_FALLBACK_KMH,
        max_horizon_seconds=60,
        max_snap_m=150.0,
        limit=10,
    )
    assert preds == []


async def test_unknown_stop_returns_empty(db) -> None:  # type: ignore[no-untyped-def]
    await PostgresCatalogRepository(db).replace_all(_bundle())
    preds = await PostgresPredictionRepository(db).predict_stop_arrivals(
        stop_id="NOPE", **_KW
    )
    assert preds == []
