"""Admin endpoints for one-shot ops while there is no scheduler.

These are unauthenticated when ENVIRONMENT is "local". In any other
environment they require an ``X-Admin-Token`` header matching ADMIN_TOKEN;
if that secret is unset the endpoints are disabled (503), since a public
function URL must not expose them open.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from vambora.adapters.inbound.http.dependencies import Container, container
from vambora.adapters.inbound.http.schemas.catalog import ImportResultDTO
from vambora.adapters.inbound.http.schemas.snapshot import SnapshotLatestDTO

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(
    c: Container = Depends(container),
    x_admin_token: str | None = Header(default=None),
) -> None:
    if c.settings.environment == "local":
        return
    if not c.settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin endpoints are disabled",
        )
    if x_admin_token != c.settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="invalid admin token",
        )


@router.post(
    "/catalog/import",
    response_model=ImportResultDTO,
    dependencies=[Depends(require_admin)],
)
async def import_catalog(c: Container = Depends(container)) -> ImportResultDTO:
    result = await c.import_gtfs_catalog()
    return ImportResultDTO(
        feed_version=result.feed_version,
        agencies=result.agencies,
        routes=result.routes,
        stops=result.stops,
    )


@router.post(
    "/snapshots/build",
    response_model=SnapshotLatestDTO,
    dependencies=[Depends(require_admin)],
)
async def build_snapshot(c: Container = Depends(container)) -> SnapshotLatestDTO:
    """Build the offline bundle now (the weekly cron is deferred)."""
    manifest = await c.build_snapshot()
    return SnapshotLatestDTO.from_manifest(manifest)
