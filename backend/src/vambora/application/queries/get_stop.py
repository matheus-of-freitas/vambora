from __future__ import annotations

from vambora.domain.catalog import Stop
from vambora.ports.outbound.repositories import CatalogRepository


class GetStop:
    def __init__(self, *, repository: CatalogRepository) -> None:
        self._repository = repository

    async def __call__(self, stop_id: str) -> Stop | None:
        return await self._repository.find_stop_by_id(stop_id)
