from __future__ import annotations

from dataclasses import dataclass

from vambora.domain.shared.errors import InvariantViolation


@dataclass(frozen=True, slots=True)
class Coordinate:
    """WGS84 coordinate. Latitude in [-90, 90], longitude in [-180, 180]."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise InvariantViolation(f"latitude out of range: {self.latitude}")
        if not -180.0 <= self.longitude <= 180.0:
            raise InvariantViolation(f"longitude out of range: {self.longitude}")
