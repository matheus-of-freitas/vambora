from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from vambora.domain.catalog import (
    Agency,
    Frequency,
    Route,
    ServiceCalendar,
    ServiceException,
    Shape,
    Stop,
    StopTime,
    Trip,
)


@dataclass(frozen=True, slots=True)
class GtfsBundle:
    """A single static-GTFS snapshot, as parsed from one source URL."""

    feed_version: str
    source_url: str
    agencies: list[Agency]
    routes: list[Route]
    stops: list[Stop]
    trips: list[Trip]
    stop_times: list[StopTime]
    frequencies: list[Frequency]
    calendars: list[ServiceCalendar]
    exceptions: list[ServiceException]
    shapes: list[Shape]


class GtfsProvider(Protocol):
    """Fetches and parses a static GTFS feed into domain entities."""

    async def load(self) -> GtfsBundle: ...
