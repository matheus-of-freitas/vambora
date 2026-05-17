"""GTFS scheduling entities.

`StopTime.arrival_seconds` and `departure_seconds` are seconds-since-midnight,
permitting the GTFS-spec values past 24:00:00 (used for service that crosses
midnight, e.g. the last trip of the night labeled `25:30:00`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from vambora.domain.shared.errors import InvariantViolation


@dataclass(frozen=True, slots=True)
class Trip:
    trip_id: str
    route_id: str
    service_id: str
    headsign: str | None
    direction_id: int | None
    shape_id: str | None

    def __post_init__(self) -> None:
        if not self.trip_id:
            raise InvariantViolation("trip_id required")
        if not self.route_id:
            raise InvariantViolation("route_id required")
        if not self.service_id:
            raise InvariantViolation("service_id required")


@dataclass(frozen=True, slots=True)
class StopTime:
    trip_id: str
    stop_sequence: int
    stop_id: str
    arrival_seconds: int
    departure_seconds: int

    def __post_init__(self) -> None:
        if not self.trip_id:
            raise InvariantViolation("trip_id required")
        if not self.stop_id:
            raise InvariantViolation("stop_id required")
        if self.stop_sequence < 0:
            raise InvariantViolation("stop_sequence must be >= 0")
        if self.arrival_seconds < 0:
            raise InvariantViolation("arrival_seconds must be >= 0")
        if self.departure_seconds < 0:
            raise InvariantViolation("departure_seconds must be >= 0")


@dataclass(frozen=True, slots=True)
class ServiceCalendar:
    service_id: str
    monday: bool
    tuesday: bool
    wednesday: bool
    thursday: bool
    friday: bool
    saturday: bool
    sunday: bool
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if not self.service_id:
            raise InvariantViolation("service_id required")
        if self.end_date < self.start_date:
            raise InvariantViolation("end_date must be >= start_date")


@dataclass(frozen=True, slots=True)
class ServiceException:
    service_id: str
    calendar_date: date
    exception_type: int  # 1 = added, 2 = removed

    def __post_init__(self) -> None:
        if not self.service_id:
            raise InvariantViolation("service_id required")
        if self.exception_type not in (1, 2):
            raise InvariantViolation(f"exception_type must be 1 or 2, got {self.exception_type}")
