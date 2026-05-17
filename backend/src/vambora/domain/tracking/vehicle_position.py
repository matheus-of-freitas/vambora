from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from vambora.domain.shared.errors import InvariantViolation
from vambora.domain.shared.types import Coordinate


@dataclass(frozen=True, slots=True)
class VehiclePosition:
    """A single GPS observation of a transit vehicle.

    Three timestamps carry distinct meaning (see ``plan.md`` decisions #24-#25):
    ``recorded_at`` is the GPS fix on the bus, ``sent_at`` the vehicle→server
    transmission, and ``received_at`` the server arrival. Liveness checks must
    use ``received_at``; trajectory math uses ``recorded_at``.
    """

    vehicle_id: str
    line_id: str
    recorded_at: datetime
    sent_at: datetime
    received_at: datetime
    coordinate: Coordinate
    speed_kmh: float
    raw: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.vehicle_id:
            raise InvariantViolation("vehicle_id required")
        if not self.line_id:
            raise InvariantViolation("line_id required")
        if self.recorded_at.tzinfo is None:
            raise InvariantViolation("recorded_at must be timezone-aware")
        if self.sent_at.tzinfo is None:
            raise InvariantViolation("sent_at must be timezone-aware")
        if self.received_at.tzinfo is None:
            raise InvariantViolation("received_at must be timezone-aware")
        if self.speed_kmh < 0:
            raise InvariantViolation(f"speed_kmh must be non-negative: {self.speed_kmh}")
