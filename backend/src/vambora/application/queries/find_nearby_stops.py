from __future__ import annotations

from vambora.domain.catalog import Stop
from vambora.domain.shared.types import Coordinate
from vambora.ports.outbound.repositories import CatalogRepository


class FindNearbyStops:
    def __init__(self, *, repository: CatalogRepository) -> None:
        self._repository = repository

    async def __call__(
        self, *, latitude: float, longitude: float, radius_m: int = 500, limit: int = 200
    ) -> list[Stop]:
        return await self._repository.stops_within(
            center=Coordinate(latitude=latitude, longitude=longitude),
            radius_m=radius_m,
            limit=limit,
        )
