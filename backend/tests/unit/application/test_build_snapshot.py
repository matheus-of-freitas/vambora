from __future__ import annotations

import gzip
import json
from datetime import UTC, datetime

import pytest

from vambora.application.commands.build_snapshot import BuildSnapshot
from vambora.domain.catalog import Route
from vambora.domain.shared.types import Coordinate
from vambora.ports.outbound.snapshot_store import SnapshotManifest
from vambora.shared.errors import VamboraError

pytestmark = pytest.mark.unit


def _route(short: str) -> Route:
    return Route(
        route_id=f"R-{short}",
        agency_id="A1",
        short_name=short,
        long_name=f"Linha {short}",
        route_type=700,
        color="FCC417",
        text_color="000000",
    )


class _FakeCatalog:
    def __init__(self, *, feed_version: str | None) -> None:
        self._feed_version = feed_version

    async def latest_feed_version(self) -> str | None:
        return self._feed_version

    async def list_routes(self, *, agency_id: str | None, limit: int) -> list[Route]:
        return [_route("485"), _route("100")]

    async def all_stops(self, *, limit: int):  # type: ignore[no-untyped-def]
        from vambora.domain.catalog import Stop

        return [
            Stop(
                stop_id="S1",
                code=None,
                name="Centro",
                coordinate=Coordinate(latitude=-22.9, longitude=-43.18),
                parent_station=None,
                wheelchair_boarding=None,
            )
        ]

    async def all_line_shapes(self) -> dict[str, list[list[Coordinate]]]:
        return {
            "485": [[Coordinate(latitude=-22.9, longitude=-43.2),
                     Coordinate(latitude=-22.91, longitude=-43.21)]]
        }

    async def line_headways(self) -> dict[str, int]:
        return {"485": 1200}

    async def stop_line_index(self) -> dict[str, list[str]]:
        return {"S1": ["100", "485"]}


class _FakeStore:
    def __init__(self) -> None:
        self.saved_body: bytes | None = None

    async def save(
        self,
        *,
        version: str,
        generated_at: datetime,
        body: bytes,
        route_count: int,
        stop_count: int,
    ) -> SnapshotManifest:
        self.saved_body = body
        return SnapshotManifest(
            version=version,
            generated_at=generated_at,
            size_bytes=len(body),
            sha256="deadbeef",
            route_count=route_count,
            stop_count=stop_count,
        )


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 5, 16, 14, 5, 40, tzinfo=UTC)


async def test_build_snapshot_assembles_gzipped_bundle() -> None:
    store = _FakeStore()
    cmd = BuildSnapshot(
        repository=_FakeCatalog(feed_version="01Q0424"),  # type: ignore[arg-type]
        store=store,  # type: ignore[arg-type]
        clock=_FixedClock(),
    )

    manifest = await cmd()

    assert manifest.version == "01Q0424.20260516140540"
    assert manifest.route_count == 2
    assert manifest.stop_count == 1
    assert store.saved_body is not None

    bundle = json.loads(gzip.decompress(store.saved_body))
    assert bundle["meta"]["feed_version"] == "01Q0424"
    assert {r["short_name"] for r in bundle["routes"]} == {"485", "100"}
    assert bundle["stops"][0]["stop_id"] == "S1"
    # [lon, lat] order, GeoJSON-ready, mirroring /lines/{short}/shape.
    assert bundle["line_shapes"]["485"][0][0] == [-43.2, -22.9]
    assert bundle["headways"]["485"] == 1200
    assert bundle["stop_lines"]["S1"] == ["100", "485"]


async def test_build_snapshot_requires_imported_catalog() -> None:
    cmd = BuildSnapshot(
        repository=_FakeCatalog(feed_version=None),  # type: ignore[arg-type]
        store=_FakeStore(),  # type: ignore[arg-type]
        clock=_FixedClock(),
    )
    with pytest.raises(VamboraError):
        await cmd()
