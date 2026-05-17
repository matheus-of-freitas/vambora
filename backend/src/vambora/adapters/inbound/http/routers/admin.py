"""Admin endpoints for one-shot ops while there is no scheduler.

These are unauthenticated in local/dev. Add an auth gate before any non-local
deployment — see Phase 1 ADR slot.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from vambora.adapters.inbound.http.dependencies import Container, container
from vambora.adapters.inbound.http.schemas.catalog import ImportResultDTO
from vambora.adapters.inbound.http.schemas.snapshot import SnapshotLatestDTO

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/catalog/import", response_model=ImportResultDTO)
async def import_catalog(c: Container = Depends(container)) -> ImportResultDTO:
    result = await c.import_gtfs_catalog()
    return ImportResultDTO(
        feed_version=result.feed_version,
        agencies=result.agencies,
        routes=result.routes,
        stops=result.stops,
    )


@router.post("/snapshots/build", response_model=SnapshotLatestDTO)
async def build_snapshot(c: Container = Depends(container)) -> SnapshotLatestDTO:
    """Build the offline bundle now (the weekly cron is deferred)."""
    manifest = await c.build_snapshot()
    return SnapshotLatestDTO.from_manifest(manifest)
