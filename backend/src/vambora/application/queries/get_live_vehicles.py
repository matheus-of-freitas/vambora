from __future__ import annotations

from vambora.domain.tracking import VehiclePosition
from vambora.ports.outbound.repositories import VehiclePositionRepository


class GetLiveVehicles:
    def __init__(self, *, repository: VehiclePositionRepository) -> None:
        self._repository = repository

    async def __call__(
        self, *, line_id: str | None = None, fresh_seconds: int = 120, limit: int = 2000
    ) -> list[VehiclePosition]:
        return await self._repository.latest_per_vehicle(
            line_id=line_id, fresh_seconds=fresh_seconds, limit=limit
        )
