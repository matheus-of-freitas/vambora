"""Plan a multi-modal trip via the routing engine (OTP).

The Rio TUMI GTFS mirror is stale (calendar 2023-06-11..2025-05-31). Like
``GetStopArrivals``, when ``GTFS_DATE_OVERRIDE`` is set we project the
departure onto that date (keeping the requested time-of-day) so OTP finds
transit service during local development. See plan.md "Appendix: GTFS Quirks".
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from vambora.domain.routing import Itinerary
from vambora.domain.shared.types import Coordinate
from vambora.ports.outbound.routing_engine import RoutingEngine
from vambora.shared.config import Settings

BRT = timezone(timedelta(hours=-3), name="America/Sao_Paulo")


class PlanTrip:
    def __init__(self, *, engine: RoutingEngine, settings: Settings) -> None:
        self._engine = engine
        self._settings = settings

    async def __call__(
        self,
        *,
        origin: Coordinate,
        destination: Coordinate,
        depart_at: datetime | None = None,
        max_itineraries: int = 3,
    ) -> list[Itinerary]:
        return await self._engine.plan_trip(
            origin=origin,
            destination=destination,
            depart_at=self._resolve_depart(depart_at),
            max_itineraries=max_itineraries,
        )

    def _resolve_depart(self, depart_at: datetime | None) -> datetime:
        base = depart_at.astimezone(BRT) if depart_at else datetime.now(BRT)
        override = self._settings.gtfs_date_override
        if override:
            d = date.fromisoformat(override)
            base = base.replace(year=d.year, month=d.month, day=d.day)
        return base
