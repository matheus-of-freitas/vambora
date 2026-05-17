from __future__ import annotations

from vambora.domain.tracking import HourlyLineStat
from vambora.ports.outbound.repositories import VehiclePositionRepository


class GetLineStats:
    def __init__(self, *, repository: VehiclePositionRepository) -> None:
        self._repository = repository

    async def __call__(self, line_id: str, *, hours: int = 24) -> list[HourlyLineStat]:
        return await self._repository.hourly_stats_for_line(line_id=line_id, hours=hours)
