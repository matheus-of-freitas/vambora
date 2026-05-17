from __future__ import annotations

from dataclasses import dataclass

from vambora.domain.shared.errors import InvariantViolation
from vambora.domain.shared.types import Coordinate


@dataclass(frozen=True, slots=True)
class Shape:
    """A polyline traced by a transit trip, in shape-point order."""

    shape_id: str
    points: list[Coordinate]

    def __post_init__(self) -> None:
        if not self.shape_id:
            raise InvariantViolation("shape_id required")
        if len(self.points) < 2:
            raise InvariantViolation("shape requires at least 2 points")
