from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from vambora.ports.outbound.repositories import VehiclePositionRepository
from vambora.shared.time import Clock


@dataclass(frozen=True, slots=True)
class CompactResult:
    rolled_up: int
    purged: int
    skipped: bool


class CompactTrackingData:
    """Roll raw positions into hourly buckets, then purge raw rows past retention.

    On TimescaleDB this is a no-op: the continuous-aggregate refresh policy and
    the retention policy (migration 0008) already do both. On plain Postgres
    there are no such policies, so the scheduled poller calls this to keep
    ``vehicle_positions`` from outgrowing a small free-tier database.

    Order matters: roll up first so a bucket is computed before its raw rows are
    eligible for purge. The rollup window must exceed the retention window for
    that to hold (asserted at call time by the configured defaults:
    rollup looks back a few hours, retention keeps ~24h).
    """

    def __init__(
        self,
        *,
        repository: VehiclePositionRepository,
        clock: Clock,
        timescale: bool,
        retention_hours: int,
        rollup_hours: int = 3,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._timescale = timescale
        self._retention_hours = retention_hours
        self._rollup_hours = rollup_hours

    async def __call__(self) -> CompactResult:
        if self._timescale:
            return CompactResult(rolled_up=0, purged=0, skipped=True)
        rolled_up = await self._repository.refresh_hourly_rollup(hours=self._rollup_hours)
        cutoff = self._clock.now() - timedelta(hours=self._retention_hours)
        purged = await self._repository.purge_raw_before(cutoff=cutoff)
        return CompactResult(rolled_up=rolled_up, purged=purged, skipped=False)
