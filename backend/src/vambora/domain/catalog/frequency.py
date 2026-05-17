from __future__ import annotations

from dataclasses import dataclass

from vambora.domain.shared.errors import InvariantViolation


@dataclass(frozen=True, slots=True)
class Frequency:
    """A headway window for a frequency-scheduled trip.

    GTFS feeds (the Rio feed included) often encode only one canonical timing
    per trip in ``stop_times`` and declare the rest via ``frequencies.txt``:
    "between ``start_seconds`` and ``end_seconds`` run every ``headway_secs``."
    To compute actual arrival times for a stop on a frequency-based trip:
    expand ``k = 0, 1, …`` while ``start_seconds + k*headway_secs < end_seconds``,
    then add the canonical offset from the trip's first stop.
    """

    trip_id: str
    start_seconds: int
    end_seconds: int
    headway_secs: int

    def __post_init__(self) -> None:
        if not self.trip_id:
            raise InvariantViolation("trip_id required")
        if self.start_seconds < 0:
            raise InvariantViolation("start_seconds must be >= 0")
        if self.end_seconds <= self.start_seconds:
            raise InvariantViolation("end_seconds must be > start_seconds")
        if self.headway_secs <= 0:
            raise InvariantViolation("headway_secs must be > 0")
