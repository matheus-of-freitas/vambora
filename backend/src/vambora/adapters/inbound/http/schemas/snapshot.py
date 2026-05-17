from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from vambora.ports.outbound.snapshot_store import SnapshotManifest


class SnapshotLatestDTO(BaseModel):
    version: str
    generated_at: datetime
    size_bytes: int
    sha256: str
    route_count: int
    stop_count: int
    url: str  # where to download the gzipped JSON bundle

    @classmethod
    def from_manifest(cls, m: SnapshotManifest) -> SnapshotLatestDTO:
        return cls(
            version=m.version,
            generated_at=m.generated_at,
            size_bytes=m.size_bytes,
            sha256=m.sha256,
            route_count=m.route_count,
            stop_count=m.stop_count,
            url=f"/snapshots/{m.version}",
        )
