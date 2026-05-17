from __future__ import annotations

import pytest

from vambora.adapters.outbound.routing.otp_client import _Plan, decode_polyline
from vambora.domain.routing import TravelMode

pytestmark = pytest.mark.unit


def test_decode_polyline_classic_vector() -> None:
    # Google's reference polyline -> (38.5,-120.2),(40.7,-120.95),(43.252,-126.453)
    coords = decode_polyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@")
    assert len(coords) == 3
    assert coords[0].latitude == pytest.approx(38.5)
    assert coords[0].longitude == pytest.approx(-120.2)
    assert coords[2].latitude == pytest.approx(43.252)
    assert coords[2].longitude == pytest.approx(-126.453)


def test_travel_mode_parse_known_and_fallback() -> None:
    assert TravelMode.parse("subway") is TravelMode.SUBWAY
    assert TravelMode.parse("BUS") is TravelMode.BUS
    # Anything OTP throws at us that we don't model degrades to TRANSIT.
    assert TravelMode.parse("CABLE_CAR") is TravelMode.TRANSIT


_PLAN = {
    "itineraries": [
        {
            "startTime": 1715166000000,
            "endTime": 1715169600000,
            "walkDistance": 350.0,
            "legs": [
                {
                    "mode": "WALK",
                    "startTime": 1715166000000,
                    "endTime": 1715166300000,
                    "distance": 250.0,
                    "from": {"name": "Origin", "lat": -22.9711, "lon": -43.1822},
                    "to": {"name": "Parada A", "lat": -22.97, "lon": -43.18},
                    "route": None,
                    "trip": None,
                    "legGeometry": {"points": "_p~iF~ps|U_ulLnnqC_mqNvxq`@"},
                },
                {
                    "mode": "BUS",
                    "startTime": 1715166300000,
                    "endTime": 1715169600000,
                    "distance": 5000.0,
                    "from": {"name": "Parada A", "lat": -22.97, "lon": -43.18},
                    "to": {"name": "Destino", "lat": -22.9068, "lon": -43.1795},
                    "route": {"shortName": "485", "longName": "Gávea - Centro"},
                    "trip": {"tripHeadsign": "Centro"},
                    "legGeometry": {"points": ""},
                },
            ],
        }
    ],
    "routingErrors": [],
}


def test_plan_response_maps_to_domain() -> None:
    plan = _Plan.model_validate(_PLAN)
    itineraries = [it.to_domain() for it in plan.itineraries]
    assert len(itineraries) == 1

    it = itineraries[0]
    assert it.duration_s == 3600
    assert it.walk_distance_m == pytest.approx(350.0)
    assert it.transfers == 0  # one transit leg -> no transfer
    assert len(it.legs) == 2

    walk, bus = it.legs
    assert walk.mode is TravelMode.WALK
    assert walk.is_transit is False
    assert walk.from_name == "Origin"
    assert len(walk.geometry) == 3

    assert bus.mode is TravelMode.BUS
    assert bus.is_transit is True
    assert bus.route_short_name == "485"
    assert bus.headsign == "Centro"
    assert bus.duration_s == 3300
    assert bus.geometry == ()  # empty polyline -> no coords


def test_plan_handles_missing_optional_fields() -> None:
    raw = {
        "itineraries": [
            {
                "startTime": 1715166000000,
                "endTime": 1715166600000,
                "legs": [
                    {
                        "mode": "WALK",
                        "startTime": 1715166000000,
                        "endTime": 1715166600000,
                        "distance": 600.0,
                        "from": {"lat": -22.97, "lon": -43.18},
                        "to": {"lat": -22.96, "lon": -43.17},
                    }
                ],
            }
        ],
    }
    it = _Plan.model_validate(raw).itineraries[0].to_domain()
    assert it.walk_distance_m == 0.0
    leg = it.legs[0]
    assert leg.from_name == ""
    assert leg.route_short_name is None
    assert leg.headsign is None
    assert leg.geometry == ()
