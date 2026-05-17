from __future__ import annotations

from dataclasses import dataclass

from vambora.ports.outbound.gtfs_provider import GtfsProvider
from vambora.ports.outbound.repositories import CatalogRepository


@dataclass(frozen=True, slots=True)
class ImportResult:
    feed_version: str
    agencies: int
    routes: int
    stops: int


class ImportGtfsCatalog:
    """Pull a fresh GTFS bundle from the provider and atomically replace the catalog."""

    def __init__(self, *, provider: GtfsProvider, repository: CatalogRepository) -> None:
        self._provider = provider
        self._repository = repository

    async def __call__(self) -> ImportResult:
        bundle = await self._provider.load()
        await self._repository.replace_all(bundle)
        return ImportResult(
            feed_version=bundle.feed_version,
            agencies=len(bundle.agencies),
            routes=len(bundle.routes),
            stops=len(bundle.stops),
        )
