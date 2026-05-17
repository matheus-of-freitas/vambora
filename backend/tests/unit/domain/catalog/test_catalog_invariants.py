import pytest

from vambora.domain.catalog import Agency, Route, Stop
from vambora.domain.shared.errors import InvariantViolation
from vambora.domain.shared.types import Coordinate

pytestmark = pytest.mark.unit


def test_agency_requires_id_name_timezone() -> None:
    Agency(
        agency_id="22002", name="Intersul", url="http://x", timezone="America/Sao_Paulo", lang="pt"
    )
    with pytest.raises(InvariantViolation):
        Agency(agency_id="", name="x", url="", timezone="America/Sao_Paulo", lang=None)
    with pytest.raises(InvariantViolation):
        Agency(agency_id="x", name="", url="", timezone="America/Sao_Paulo", lang=None)
    with pytest.raises(InvariantViolation):
        Agency(agency_id="x", name="x", url="", timezone="", lang=None)


def test_route_requires_ids_and_short_name() -> None:
    Route(
        route_id="O0006AAA0A",
        agency_id="22002",
        short_name="006",
        long_name="Silvestre - Castelo",
        route_type=700,
        color="FCC417",
        text_color="000000",
    )
    with pytest.raises(InvariantViolation):
        Route(
            route_id="",
            agency_id="x",
            short_name="x",
            long_name="",
            route_type=3,
            color=None,
            text_color=None,
        )
    with pytest.raises(InvariantViolation):
        Route(
            route_id="x",
            agency_id="",
            short_name="x",
            long_name="",
            route_type=3,
            color=None,
            text_color=None,
        )
    with pytest.raises(InvariantViolation):
        Route(
            route_id="x",
            agency_id="y",
            short_name="",
            long_name="",
            route_type=3,
            color=None,
            text_color=None,
        )


def test_stop_requires_id_and_name() -> None:
    Stop(
        stop_id="1002O00010C0",
        code=None,
        name="AquaRio",
        coordinate=Coordinate(latitude=-22.89331, longitude=-43.1926),
        parent_station=None,
        wheelchair_boarding=None,
    )
    with pytest.raises(InvariantViolation):
        Stop(
            stop_id="",
            code=None,
            name="x",
            coordinate=Coordinate(latitude=0.0, longitude=0.0),
            parent_station=None,
            wheelchair_boarding=None,
        )
    with pytest.raises(InvariantViolation):
        Stop(
            stop_id="x",
            code=None,
            name="",
            coordinate=Coordinate(latitude=0.0, longitude=0.0),
            parent_station=None,
            wheelchair_boarding=None,
        )
