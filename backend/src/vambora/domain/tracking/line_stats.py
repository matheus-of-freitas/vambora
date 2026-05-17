from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class HourlyLineStat:
    """One hourly bucket of activity for a line, from the continuous aggregate."""

    bucket: datetime
    position_count: int
    vehicle_count: int
    avg_speed_kmh: float
    max_speed_kmh: float
