from __future__ import annotations

from datetime import UTC, datetime

import pytest

from vambora.adapters.inbound.http.schemas.prediction import PredictionDTO
from vambora.domain.predictions import ArrivalPrediction

pytestmark = pytest.mark.unit


def _pred(eta_seconds: int, distance_m: float, speed_kmh: float) -> ArrivalPrediction:
    return ArrivalPrediction(
        line_short_name="639",
        vehicle_id="B27005",
        distance_m=distance_m,
        speed_kmh=speed_kmh,
        eta_seconds=eta_seconds,
        eta_at=datetime(2026, 5, 16, 12, 0, tzinfo=UTC),
        route_long_name="Jardim América - Saens Peña",
        route_color="1B5E20",
    )


def test_eta_minutes_rounds_and_has_floor_of_one() -> None:
    # 39 s -> rounds to ~1 min, but never below 1.
    assert PredictionDTO.from_domain(_pred(39, 567.0, 53.0)).eta_minutes == 1
    assert PredictionDTO.from_domain(_pred(5, 10.0, 50.0)).eta_minutes == 1
    # 227 s -> ~4 min.
    assert PredictionDTO.from_domain(_pred(227, 946.0, 15.0)).eta_minutes == 4
    # 1543 s -> ~26 min.
    assert PredictionDTO.from_domain(_pred(1543, 6429.0, 15.0)).eta_minutes == 26


def test_distance_and_speed_are_rounded() -> None:
    dto = PredictionDTO.from_domain(_pred(227, 946.349, 15.04))
    assert dto.distance_m == 946.3
    assert dto.speed_kmh == 15.0
    assert dto.line_short_name == "639"
    assert dto.route_color == "1B5E20"
    assert dto.eta_at.tzinfo is not None
