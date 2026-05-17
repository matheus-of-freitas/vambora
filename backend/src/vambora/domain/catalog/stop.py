from __future__ import annotations

from dataclasses import dataclass

from vambora.domain.shared.errors import InvariantViolation
from vambora.domain.shared.types import Coordinate


@dataclass(frozen=True, slots=True)
class Stop:
    stop_id: str
    code: str | None
    name: str
    coordinate: Coordinate
    parent_station: str | None
    wheelchair_boarding: int | None  # GTFS: 0 unknown, 1 accessible, 2 not accessible

    def __post_init__(self) -> None:
        if not self.stop_id:
            raise InvariantViolation("stop_id required")
        if not self.name:
            raise InvariantViolation("stop name required")
