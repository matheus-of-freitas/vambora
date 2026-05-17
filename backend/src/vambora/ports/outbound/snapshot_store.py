from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SnapshotManifest:
    """Metadata for one built offline bundle. The bytes live in the store;
    this is what ``GET /snapshots/latest`` returns (plus a download URL)."""

    version: str
    generated_at: datetime
    size_bytes: int
    sha256: str
    route_count: int
    stop_count: int


class SnapshotStore(Protocol):
    """Where built bundles live. The local-filesystem adapter is the dev/MVP
    implementation; an R2 adapter is the deferred, credential-gated swap
    behind this same port (it would also issue signed URLs)."""

    async def save(
        self,
        *,
        version: str,
        generated_at: datetime,
        body: bytes,
        route_count: int,
        stop_count: int,
    ) -> SnapshotManifest:
        """Persist ``body`` (gzipped JSON) and mark it the latest."""
        ...

    async def latest(self) -> SnapshotManifest | None:
        """Manifest of the most recently saved bundle, or ``None``."""
        ...

    async def read(self, version: str) -> bytes | None:
        """The gzipped bytes for ``version``, or ``None`` if absent."""
        ...
