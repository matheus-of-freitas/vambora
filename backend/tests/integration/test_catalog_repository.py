"""Integration coverage for the catalog repository: replace_all atomicity,
arrivals frequency expansion, shape persistence and retrieval."""

from __future__ import annotations

from datetime import date

import pytest

from vambora.adapters.outbound.persistence.repositories.catalog import (
    PostgresCatalogRepository,
)
from vambora.domain.catalog import (
    Agency,
    Frequency,
    Route,
    ServiceCalendar,
    ServiceException,
    Shape,
    Stop,
    StopTime,
    Trip,
)
from vambora.domain.shared.types import Coordinate
from vambora.ports.outbound.gtfs_provider import GtfsBundle

pytestmark = pytest.mark.integration


def _bundle() -> GtfsBundle:
    """A minimal but realistic bundle. One route (485), two stops, one trip
    that runs on weekdays from 06:00-07:00 every 10 min, with a 60-second
    travel time between the two stops. Plus one shape covering both."""
    return GtfsBundle(
        feed_version="test-01",
        source_url="memory://",
        agencies=[
            Agency(
                agency_id="22003",
                name="Internorte",
                url="http://x",
                timezone="America/Sao_Paulo",
                lang="pt",
            )
        ],
        routes=[
            Route(
                route_id="O0485",
                agency_id="22003",
                short_name="485",
                long_name="Fundão - General Osório",
                route_type=700,
                color="A2B71A",
                text_color="000000",
            )
        ],
        stops=[
            Stop(
                stop_id="S1",
                code=None,
                name="Fundão",
                coordinate=Coordinate(latitude=-22.857, longitude=-43.231),
                parent_station=None,
                wheelchair_boarding=None,
            ),
            Stop(
                stop_id="S2",
                code=None,
                name="General Osório",
                coordinate=Coordinate(latitude=-22.984, longitude=-43.198),
                parent_station=None,
                wheelchair_boarding=None,
            ),
        ],
        trips=[
            Trip(
                trip_id="T1",
                route_id="O0485",
                service_id="WEEKDAY",
                headsign="General Osório",
                direction_id=0,
                shape_id="SH1",
            )
        ],
        stop_times=[
            StopTime(
                trip_id="T1", stop_sequence=1, stop_id="S1", arrival_seconds=0, departure_seconds=0
            ),
            StopTime(
                trip_id="T1",
                stop_sequence=2,
                stop_id="S2",
                arrival_seconds=60,
                departure_seconds=60,
            ),
        ],
        # 06:00-07:00 every 600 s => k = 0..5 => 6 departures expected per stop.
        frequencies=[
            Frequency(
                trip_id="T1",
                start_seconds=21600,  # 06:00
                end_seconds=25200,  # 07:00
                headway_secs=600,
            )
        ],
        calendars=[
            ServiceCalendar(
                service_id="WEEKDAY",
                monday=True,
                tuesday=True,
                wednesday=True,
                thursday=True,
                friday=True,
                saturday=False,
                sunday=False,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
            )
        ],
        exceptions=[
            ServiceException(
                service_id="WEEKDAY",
                calendar_date=date(2024, 5, 9),  # Thursday: removed (holiday)
                exception_type=2,
            )
        ],
        shapes=[
            Shape(
                shape_id="SH1",
                points=[
                    Coordinate(latitude=-22.857, longitude=-43.231),
                    Coordinate(latitude=-22.984, longitude=-43.198),
                ],
            )
        ],
    )


async def test_replace_all_round_trips(db) -> None:  # type: ignore[no-untyped-def]
    repo = PostgresCatalogRepository(db)
    await repo.replace_all(_bundle())

    routes = await repo.find_routes_by_short_name("485")
    assert [r.route_id for r in routes] == ["O0485"]
    assert routes[0].long_name == "Fundão - General Osório"

    stop = await repo.find_stop_by_id("S1")
    assert stop is not None
    assert stop.name == "Fundão"

    nearby = await repo.stops_within(
        center=Coordinate(latitude=-22.857, longitude=-43.231),
        radius_m=1000,
        limit=10,
    )
    assert {s.stop_id for s in nearby} == {"S1"}

    shapes = await repo.shapes_for_line("485")
    assert len(shapes) == 1
    assert len(shapes[0]) == 2


async def test_arrivals_expand_frequencies_on_active_day(db) -> None:  # type: ignore[no-untyped-def]
    """On a regular Wednesday inside the calendar window, the 06:00-07:00
    frequency window with 10-min headway should yield 6 arrivals at S2 (which
    is 60 s after S1 along the trip)."""
    repo = PostgresCatalogRepository(db)
    await repo.replace_all(_bundle())

    arrivals = await repo.arrivals_at_stop(
        stop_id="S2",
        the_date=date(2024, 5, 8),  # Wednesday — not the May 9 exception date.
        from_seconds=0,
        limit=20,
    )
    assert len(arrivals) == 6
    expected_seconds = [21660, 22260, 22860, 23460, 24060, 24660]
    assert [a.arrival_seconds for a in arrivals] == expected_seconds
    assert all(a.route_short_name == "485" for a in arrivals)


async def test_arrivals_respects_calendar_dates_exceptions(db) -> None:  # type: ignore[no-untyped-def]
    """The exception removes WEEKDAY service on 2024-05-09 — arrivals must be empty."""
    repo = PostgresCatalogRepository(db)
    await repo.replace_all(_bundle())

    arrivals = await repo.arrivals_at_stop(
        stop_id="S2",
        the_date=date(2024, 5, 9),  # exception_type=2 strips this date.
        from_seconds=0,
        limit=20,
    )
    assert arrivals == []


async def test_arrivals_filter_by_from_seconds(db) -> None:  # type: ignore[no-untyped-def]
    """Arrivals before ``from_seconds`` are filtered out."""
    repo = PostgresCatalogRepository(db)
    await repo.replace_all(_bundle())

    arrivals = await repo.arrivals_at_stop(
        stop_id="S2",
        the_date=date(2024, 5, 8),
        from_seconds=23000,  # after the 3rd departure
        limit=20,
    )
    assert [a.arrival_seconds for a in arrivals] == [23460, 24060, 24660]


async def test_snapshot_bulk_reads(db) -> None:  # type: ignore[no-untyped-def]
    """The offline-bundle bulk reads (only fakes-tested via BuildSnapshot)
    against a real DB: all stops, per-line shapes, median headways, the
    stop→lines index, and the latest feed version."""
    repo = PostgresCatalogRepository(db)
    await repo.replace_all(_bundle())

    stops = await repo.all_stops(limit=1000)
    assert {s.stop_id for s in stops} == {"S1", "S2"}
    assert {s.name for s in stops} == {"Fundão", "General Osório"}

    line_shapes = await repo.all_line_shapes()
    assert set(line_shapes) == {"485"}
    assert len(line_shapes["485"]) == 1  # one distinct shape on the line
    assert len(line_shapes["485"][0]) == 2  # two shape points
    first = line_shapes["485"][0][0]
    assert first.latitude == pytest.approx(-22.857, abs=1e-3)
    assert first.longitude == pytest.approx(-43.231, abs=1e-3)

    # _bundle: one frequency, headway_secs=600 → median 600.
    assert await repo.line_headways() == {"485": 600}

    # Both stops are served by line 485 (sorted serving short_names).
    assert await repo.stop_line_index() == {"S1": ["485"], "S2": ["485"]}

    assert await repo.latest_feed_version() == "test-01"
