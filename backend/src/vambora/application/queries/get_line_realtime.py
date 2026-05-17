from __future__ import annotations

from dataclasses import dataclass

from vambora.domain.catalog import Route
from vambora.domain.tracking import VehiclePosition
from vambora.ports.outbound.repositories import CatalogRepository, VehiclePositionRepository


@dataclass(frozen=True, slots=True)
class LineRealtime:
    routes: list[Route]
    vehicles: list[VehiclePosition]


class GetLineRealtime:
    """Joins catalog (line metadata) and tracking (live vehicles).

    Resolves a user-facing ``short_name`` (e.g. ``"485"``) against the GTFS
    catalog. Multiple routes can share a short_name across agencies; we return
    all of them and the union of their currently-running vehicles.

    SPPO ``linha`` values that aren't in the catalog (``GARAGEM``, special
    service codes like ``SV669``) return an empty list of routes — caller
    decides whether that's a 404 or an empty payload.
    """

    def __init__(
        self,
        *,
        catalog: CatalogRepository,
        tracking: VehiclePositionRepository,
    ) -> None:
        self._catalog = catalog
        self._tracking = tracking

    async def __call__(
        self, short_name: str, *, fresh_seconds: int = 180, limit: int = 500
    ) -> LineRealtime:
        routes = await self._catalog.find_routes_by_short_name(short_name)
        if not routes:
            return LineRealtime(routes=[], vehicles=[])
        vehicles = await self._tracking.latest_per_vehicle(
            line_id=short_name, fresh_seconds=fresh_seconds, limit=limit
        )
        return LineRealtime(routes=routes, vehicles=vehicles)
