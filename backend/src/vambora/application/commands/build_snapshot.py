"""Build the offline bundle (plan.md decision #9: full GTFS + aggregates).

Bundle = static catalog the web needs offline (routes, stops, per-line route
shapes) plus the "typical headway" aggregate per line. Deliberately excludes
the ~1M-row stop_times — offline uses typical headways, not the full schedule
(glossary: "downloaded GTFS bundle plus typical headways"). Serialized to
gzipped JSON; the store marks it the latest.

The weekly cron is just this command on a schedule — deferred; trigger
manually via ``POST /admin/snapshots/build`` for now.
"""

from __future__ import annotations

import gzip
import json

from vambora.ports.outbound.repositories import CatalogRepository
from vambora.ports.outbound.snapshot_store import SnapshotManifest, SnapshotStore
from vambora.shared.errors import VamboraError
from vambora.shared.time import Clock

# The Rio catalog is ~479 routes / ~7.5k stops; generous ceilings.
_ROUTE_LIMIT = 10_000
_STOP_LIMIT = 50_000


class BuildSnapshot:
    def __init__(
        self,
        *,
        repository: CatalogRepository,
        store: SnapshotStore,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._store = store
        self._clock = clock

    async def __call__(self) -> SnapshotManifest:
        feed_version = await self._repository.latest_feed_version()
        if feed_version is None:
            raise VamboraError("no GTFS catalog imported yet; cannot build a snapshot")

        generated_at = self._clock.now()
        version = f"{feed_version}.{generated_at:%Y%m%d%H%M%S}"
        routes = await self._repository.list_routes(agency_id=None, limit=_ROUTE_LIMIT)
        stops = await self._repository.all_stops(limit=_STOP_LIMIT)
        line_shapes = await self._repository.all_line_shapes()
        headways = await self._repository.line_headways()
        stop_lines = await self._repository.stop_line_index()

        bundle = {
            "meta": {
                "version": version,
                "feed_version": feed_version,
                "generated_at": generated_at.isoformat(),
                "route_count": len(routes),
                "stop_count": len(stops),
            },
            "routes": [
                {
                    "route_id": r.route_id,
                    "short_name": r.short_name,
                    "long_name": r.long_name,
                    "color": r.color,
                }
                for r in routes
            ],
            "stops": [
                {
                    "stop_id": s.stop_id,
                    "name": s.name,
                    "code": s.code,
                    "lat": s.coordinate.latitude,
                    "lon": s.coordinate.longitude,
                }
                for s in stops
            ],
            # short_name -> list of polylines; each polyline is [[lon,lat],...]
            # (GeoJSON order), mirroring GET /lines/{short}/shape exactly.
            "line_shapes": {
                short: [[[p.longitude, p.latitude] for p in poly] for poly in polys]
                for short, polys in line_shapes.items()
            },
            "headways": headways,
            # stop_id -> sorted serving line short_names; the offline
            # substitute for stop_times (with `headways` for "~N min").
            "stop_lines": stop_lines,
        }

        body = gzip.compress(json.dumps(bundle, separators=(",", ":")).encode("utf-8"))
        return await self._store.save(
            version=version,
            generated_at=generated_at,
            body=body,
            route_count=len(routes),
            stop_count=len(stops),
        )
