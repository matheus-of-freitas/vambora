from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from vambora.adapters.outbound.persistence.repositories.vehicle_positions import (
    PostgresVehiclePositionRepository,
)
from vambora.domain.shared.types import Coordinate
from vambora.domain.tracking import VehiclePosition

pytestmark = pytest.mark.integration


def _pos(
    *,
    vehicle_id: str = "B11622",
    line_id: str = "485",
    recorded_at: datetime,
    received_at: datetime | None = None,
    speed_kmh: float = 30.0,
    lat: float = -22.9,
    lon: float = -43.2,
) -> VehiclePosition:
    return VehiclePosition(
        vehicle_id=vehicle_id,
        line_id=line_id,
        recorded_at=recorded_at,
        sent_at=recorded_at,
        received_at=received_at if received_at is not None else recorded_at,
        coordinate=Coordinate(latitude=lat, longitude=lon),
        speed_kmh=speed_kmh,
        raw={"ordem": vehicle_id},
    )


async def test_upsert_dedups_on_vehicle_and_recorded_at(db) -> None:  # type: ignore[no-untyped-def]
    repo = PostgresVehiclePositionRepository(db)
    ts = datetime.now(UTC)

    first = await repo.upsert_many([_pos(recorded_at=ts)])
    assert first == 1

    # Same key — UNIQUE(vehicle_id, recorded_at) + ON CONFLICT DO NOTHING means 0 new rows.
    again = await repo.upsert_many([_pos(recorded_at=ts)])
    assert again == 0

    # Different timestamp on the same vehicle is a new row.
    later = await repo.upsert_many([_pos(recorded_at=ts + timedelta(seconds=30))])
    assert later == 1


async def test_latest_per_vehicle_returns_newest_and_filters_by_line(db) -> None:  # type: ignore[no-untyped-def]
    repo = PostgresVehiclePositionRepository(db)
    now = datetime.now(UTC)

    await repo.upsert_many(
        [
            _pos(vehicle_id="A1", line_id="485", recorded_at=now - timedelta(seconds=60)),
            _pos(
                vehicle_id="A1",
                line_id="485",
                recorded_at=now - timedelta(seconds=10),
                speed_kmh=42.0,
            ),
            _pos(vehicle_id="A2", line_id="007", recorded_at=now - timedelta(seconds=20)),
        ]
    )

    fresh = await repo.latest_per_vehicle(line_id=None, fresh_seconds=120, limit=10)
    assert len(fresh) == 2
    a1 = next(p for p in fresh if p.vehicle_id == "A1")
    assert a1.speed_kmh == pytest.approx(42.0)

    on_line_485 = await repo.latest_per_vehicle(line_id="485", fresh_seconds=120, limit=10)
    assert {p.vehicle_id for p in on_line_485} == {"A1"}


async def test_history_for_returns_descending(db) -> None:  # type: ignore[no-untyped-def]
    repo = PostgresVehiclePositionRepository(db)
    now = datetime.now(UTC)
    await repo.upsert_many(
        [
            _pos(recorded_at=now - timedelta(seconds=60)),
            _pos(recorded_at=now - timedelta(seconds=30)),
            _pos(recorded_at=now),
        ]
    )

    history = await repo.history_for("B11622", limit=10)
    assert [p.recorded_at for p in history] == sorted(
        [p.recorded_at for p in history], reverse=True
    )
    assert len(history) == 3


async def test_liveness_gates_on_received_at_not_recorded_at(db) -> None:  # type: ignore[no-untyped-def]
    """plan.md decision #25 / SPPO appendix: a vehicle whose GPS fix is hours
    old but whose data just arrived IS live. The inverse — a recent GPS fix we
    haven't received in a while — cannot happen (received_at >= recorded_at),
    so the only meaningful case is stale-recorded / fresh-received."""
    repo = PostgresVehiclePositionRepository(db)
    now = datetime.now(UTC)

    await repo.upsert_many(
        [
            # GPS fix 3h old, but the server just received it → LIVE.
            _pos(
                vehicle_id="STALE_FIX",
                recorded_at=now - timedelta(hours=3),
                received_at=now - timedelta(seconds=5),
            ),
            # Everything 10 minutes old, including arrival → NOT live (>120s).
            _pos(
                vehicle_id="GONE",
                recorded_at=now - timedelta(minutes=10),
                received_at=now - timedelta(minutes=10),
            ),
        ]
    )

    fresh = await repo.latest_per_vehicle(line_id=None, fresh_seconds=120, limit=10)
    ids = {p.vehicle_id for p in fresh}
    assert "STALE_FIX" in ids, "stale GPS but freshly received must count as live"
    assert "GONE" not in ids, "vehicle not heard from in 10 min must not be live"
