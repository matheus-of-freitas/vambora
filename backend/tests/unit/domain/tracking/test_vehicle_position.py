from datetime import UTC, datetime

import pytest

from vambora.domain.shared.errors import InvariantViolation
from vambora.domain.shared.types import Coordinate
from vambora.domain.tracking import VehiclePosition

pytestmark = pytest.mark.unit


def _ts() -> datetime:
    return datetime(2026, 5, 9, 14, 30, 0, tzinfo=UTC)


def _ok(**overrides: object) -> VehiclePosition:
    defaults: dict[str, object] = {
        "vehicle_id": "B11622",
        "line_id": "363",
        "recorded_at": _ts(),
        "sent_at": _ts(),
        "received_at": _ts(),
        "coordinate": Coordinate(latitude=-22.9, longitude=-43.2),
        "speed_kmh": 30.0,
        "raw": {},
    }
    defaults.update(overrides)
    return VehiclePosition(**defaults)  # type: ignore[arg-type]


def test_constructs_with_valid_inputs() -> None:
    p = _ok()
    assert p.vehicle_id == "B11622"
    assert p.coordinate.latitude == -22.9


def test_rejects_empty_vehicle_id() -> None:
    with pytest.raises(InvariantViolation):
        _ok(vehicle_id="")


def test_rejects_empty_line_id() -> None:
    with pytest.raises(InvariantViolation):
        _ok(line_id="")


def test_rejects_naive_recorded_at() -> None:
    with pytest.raises(InvariantViolation):
        _ok(recorded_at=datetime(2026, 5, 9, 14, 30))


def test_rejects_negative_speed() -> None:
    with pytest.raises(InvariantViolation):
        _ok(speed_kmh=-1.0)


def test_coordinate_validates_range() -> None:
    with pytest.raises(InvariantViolation):
        Coordinate(latitude=91.0, longitude=0.0)
    with pytest.raises(InvariantViolation):
        Coordinate(latitude=0.0, longitude=181.0)
