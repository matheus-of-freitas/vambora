"""Local-filesystem snapshot store (dev/MVP).

Layout under ``base_dir``:
  - ``<version>.json.gz`` — one per built bundle
  - ``latest.json``       — manifest pointer to the newest bundle

The R2 adapter (deferred, credential-gated) implements the same port and
additionally returns signed URLs; the API and web don't change when it lands.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from vambora.ports.outbound.snapshot_store import SnapshotManifest

_SAFE_VERSION = re.compile(r"^[A-Za-z0-9._-]+$")


class LocalSnapshotStore:
    def __init__(self, base_dir: Path) -> None:
        self._dir = base_dir

    def _manifest_path(self) -> Path:
        return self._dir / "latest.json"

    def _bundle_path(self, version: str) -> Path:
        return self._dir / f"{version}.json.gz"

    async def save(
        self,
        *,
        version: str,
        generated_at: datetime,
        body: bytes,
        route_count: int,
        stop_count: int,
    ) -> SnapshotManifest:
        manifest = SnapshotManifest(
            version=version,
            generated_at=generated_at,
            size_bytes=len(body),
            sha256=hashlib.sha256(body).hexdigest(),
            route_count=route_count,
            stop_count=stop_count,
        )

        def _write() -> None:
            self._dir.mkdir(parents=True, exist_ok=True)
            self._bundle_path(version).write_bytes(body)
            self._manifest_path().write_text(
                json.dumps(
                    {
                        "version": manifest.version,
                        "generated_at": manifest.generated_at.isoformat(),
                        "size_bytes": manifest.size_bytes,
                        "sha256": manifest.sha256,
                        "route_count": manifest.route_count,
                        "stop_count": manifest.stop_count,
                    }
                )
            )

        await asyncio.to_thread(_write)
        return manifest

    async def latest(self) -> SnapshotManifest | None:
        def _read() -> SnapshotManifest | None:
            path = self._manifest_path()
            if not path.exists():
                return None
            data = json.loads(path.read_text())
            return SnapshotManifest(
                version=data["version"],
                generated_at=datetime.fromisoformat(data["generated_at"]).astimezone(UTC),
                size_bytes=int(data["size_bytes"]),
                sha256=data["sha256"],
                route_count=int(data["route_count"]),
                stop_count=int(data["stop_count"]),
            )

        return await asyncio.to_thread(_read)

    async def read(self, version: str) -> bytes | None:
        if not _SAFE_VERSION.match(version):
            return None  # reject path-traversal / odd input

        def _read() -> bytes | None:
            path = self._bundle_path(version)
            return path.read_bytes() if path.exists() else None

        return await asyncio.to_thread(_read)
