from __future__ import annotations

from vambora.domain.catalog import Route
from vambora.ports.outbound.repositories import CatalogRepository


class ListRoutes:
    def __init__(self, *, repository: CatalogRepository) -> None:
        self._repository = repository

    async def __call__(self, *, agency_id: str | None = None, limit: int = 1000) -> list[Route]:
        return await self._repository.list_routes(agency_id=agency_id, limit=limit)
