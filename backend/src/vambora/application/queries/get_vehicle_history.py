from __future__ import annotations

from vambora.domain.tracking import VehiclePosition
from vambora.ports.outbound.repositories import VehiclePositionRepository


class GetVehicleHistory:
    def __init__(self, *, repository: VehiclePositionRepository) -> None:
        self._repository = repository

    async def __call__(self, vehicle_id: str, *, limit: int = 50) -> list[VehiclePosition]:
        return await self._repository.history_for(vehicle_id, limit=limit)
