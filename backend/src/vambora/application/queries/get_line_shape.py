from __future__ import annotations

from vambora.domain.shared.types import Coordinate
from vambora.ports.outbound.repositories import CatalogRepository


class GetLineShape:
    def __init__(self, *, repository: CatalogRepository) -> None:
        self._repository = repository

    async def __call__(self, short_name: str) -> list[list[Coordinate]]:
        return await self._repository.shapes_for_line(short_name)
