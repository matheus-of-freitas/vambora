"""Resolve "next scheduled arrivals at this stop" against the GTFS catalog.

The Rio TUMI GTFS mirror is stale (calendar runs through 2025-05-31, while we
are well past that). Without an override the query returns empty for the
current date. Set the ``GTFS_DATE_OVERRIDE`` environment variable
(``YYYY-MM-DD``) to project arrivals against a date inside the calendar window
for local development. See plan.md "Appendix: GTFS Quirks".
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from vambora.domain.catalog import ScheduledArrival
from vambora.ports.outbound.repositories import CatalogRepository
from vambora.shared.config import Settings

BRT = timezone(timedelta(hours=-3), name="America/Sao_Paulo")


class GetStopArrivals:
    def __init__(self, *, repository: CatalogRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def __call__(self, stop_id: str, *, limit: int = 10) -> list[ScheduledArrival]:
        target_date, from_seconds = self._resolve_clock()
        return await self._repository.arrivals_at_stop(
            stop_id=stop_id,
            the_date=target_date,
            from_seconds=from_seconds,
            limit=limit,
        )

    def _resolve_clock(self) -> tuple[date, int]:
        override = self._settings.gtfs_date_override
        now_brt = datetime.now(BRT)
        from_seconds = now_brt.hour * 3600 + now_brt.minute * 60 + now_brt.second
        target = date.fromisoformat(override) if override else now_brt.date()
        return target, from_seconds
