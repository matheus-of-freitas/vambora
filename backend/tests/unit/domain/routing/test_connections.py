from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from vambora.domain.routing import ConnectionKind, Itinerary, Leg, TravelMode
from vambora.domain.shared.types import Coordinate

pytestmark = pytest.mark.unit

_T0 = datetime(2026, 5, 16, 8, 0, tzinfo=UTC)
_C = Coordinate(latitude=-22.9, longitude=-43.2)


def _leg(
    mode: TravelMode,
    start_min: int,
    end_min: int,
    *,
    route: str | None = None,
    interline: bool = False,
) -> Leg:
    return Leg(
        mode=mode,
        start_time=_T0 + timedelta(minutes=start_min),
        end_time=_T0 + timedelta(minutes=end_min),
        distance_m=100.0,
        from_name="A",
        from_coordinate=_C,
        to_name="B",
        to_coordinate=_C,
        geometry=(),
        route_short_name=route,
        interline=interline,
    )


def _itin(*legs: Leg) -> Itinerary:
    return Itinerary(
        start_time=legs[0].start_time,
        end_time=legs[-1].end_time,
        walk_distance_m=0.0,
        legs=tuple(legs),
    )


def test_no_transfer_when_single_transit_leg() -> None:
    it = _itin(
        _leg(TravelMode.WALK, 0, 5),
        _leg(TravelMode.BUS, 5, 30, route="639"),
        _leg(TravelMode.WALK, 30, 35),
    )
    assert it.transfers == 0
    assert it.connections(tight_below_seconds=180) == ()


def test_connection_wait_absorbs_the_walk_gap() -> None:
    # Bus 639 ends at 30; walk to next stop until 33; Bus 100 departs at 40.
    it = _itin(
        _leg(TravelMode.BUS, 0, 30, route="639"),
        _leg(TravelMode.WALK, 30, 33),
        _leg(TravelMode.BUS, 40, 60, route="100"),
    )
    conns = it.connections(tight_below_seconds=180)
    assert len(conns) == 1
    c = conns[0]
    assert (c.from_route, c.to_route) == ("639", "100")
    assert c.wait_seconds == 10 * 60  # 40 - 30, includes the 3-min walk
    assert c.wait_minutes == 10
    assert c.kind is ConnectionKind.OK
    assert it.transfers == 1


def test_tight_connection_flagged() -> None:
    it = _itin(
        _leg(TravelMode.BUS, 0, 30, route="639"),
        _leg(TravelMode.BUS, 32, 50, route="100"),  # 2 min slack
    )
    (c,) = it.connections(tight_below_seconds=180)
    assert c.wait_seconds == 120
    assert c.kind is ConnectionKind.TIGHT


def test_interline_is_not_a_transfer() -> None:
    it = _itin(
        _leg(TravelMode.BUS, 0, 30, route="639"),
        _leg(TravelMode.BUS, 30, 55, route="639", interline=True),
    )
    (c,) = it.connections(tight_below_seconds=180)
    assert c.kind is ConnectionKind.INTERLINE
    assert it.transfers == 0  # same vehicle, not a real transfer


def test_multi_transfer_mix() -> None:
    it = _itin(
        _leg(TravelMode.BUS, 0, 20, route="A"),
        _leg(TravelMode.BUS, 21, 40, route="B"),  # 1 min -> tight
        _leg(TravelMode.WALK, 40, 45),
        _leg(TravelMode.BUS, 55, 70, route="C"),  # 15 min -> ok
    )
    kinds = [c.kind for c in it.connections(tight_below_seconds=180)]
    assert kinds == [ConnectionKind.TIGHT, ConnectionKind.OK]
    assert it.transfers == 2
