from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from vambora.ports.outbound.repositories import VehiclePositionRepository
from vambora.ports.outbound.vehicle_tracking_provider import VehicleTrackingProvider
from vambora.shared.time import Clock


@dataclass(frozen=True, slots=True)
class IngestResult:
    fetched: int
    persisted: int


class IngestVehiclePositions:
    """Pull a fresh window from the upstream provider and persist it.

    Pure orchestration: knows about the domain (``VehiclePosition``) and the two
    ports it depends on. Has no opinion on which provider, which DB, or how the
    poller schedules ticks.
    """

    def __init__(
        self,
        *,
        provider: VehicleTrackingProvider,
        repository: VehiclePositionRepository,
        clock: Clock,
        window_seconds: int,
    ) -> None:
        self._provider = provider
        self._repository = repository
        self._clock = clock
        self._window = timedelta(seconds=window_seconds)

    async def __call__(self) -> IngestResult:
        until = self._clock.now()
        since = until - self._window
        positions = await self._provider.fetch(since=since, until=until)
        persisted = await self._repository.upsert_many(positions)
        return IngestResult(fetched=len(positions), persisted=persisted)
