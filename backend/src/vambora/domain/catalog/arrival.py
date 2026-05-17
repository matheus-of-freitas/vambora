"""Read-model returned by the arrivals query — joins stop_times + trips + routes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScheduledArrival:
    arrival_seconds: int
    trip_id: str
    headsign: str | None
    route_id: str
    route_short_name: str
    route_long_name: str
    route_color: str | None
