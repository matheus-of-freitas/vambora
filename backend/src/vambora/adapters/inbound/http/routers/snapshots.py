from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from vambora.adapters.inbound.http.dependencies import Container, container
from vambora.adapters.inbound.http.schemas.snapshot import SnapshotLatestDTO

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.get("/latest", response_model=SnapshotLatestDTO)
async def latest_snapshot(c: Container = Depends(container)) -> SnapshotLatestDTO:
    manifest = await c.snapshot_store.latest()
    if manifest is None:
        raise HTTPException(status_code=404, detail="no snapshot built yet")
    return SnapshotLatestDTO.from_manifest(manifest)


@router.get("/{version}")
async def download_snapshot(
    version: str,
    c: Container = Depends(container),
) -> Response:
    body = await c.snapshot_store.read(version)
    if body is None:
        raise HTTPException(status_code=404, detail="snapshot not found")
    # Body is gzipped JSON. Declaring Content-Encoding lets the browser
    # transparently inflate it, so the web client can call response.json().
    return Response(
        content=body,
        media_type="application/json",
        headers={
            "Content-Encoding": "gzip",
            "Cache-Control": "public, max-age=86400",
        },
    )
