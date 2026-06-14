from __future__ import annotations

from datetime import date, datetime
from typing import Protocol

from vambora.domain.catalog import Route, ScheduledArrival, Stop
from vambora.domain.shared.types import Coordinate
from vambora.domain.tracking import HourlyLineStat, VehiclePosition
from vambora.ports.outbound.gtfs_provider import GtfsBundle


class VehiclePositionRepository(Protocol):
    """Persistence port for ``VehiclePosition``.

    The ``upsert_many`` contract: implementations MUST silently skip rows that
    collide on ``(vehicle_id, recorded_at)``. SPPO re-emits the same fix across
    overlapping fetch windows, so duplicates are normal traffic.
    """

    async def upsert_many(self, positions: list[VehiclePosition]) -> int:
        """Return the number of rows actually inserted (excluding duplicates)."""
        ...

    async def latest_per_vehicle(
        self, *, line_id: str | None, fresh_seconds: int, limit: int
    ) -> list[VehiclePosition]:
        """Latest position per vehicle whose ``recorded_at`` is within the window."""
        ...

    async def history_for(self, vehicle_id: str, *, limit: int) -> list[VehiclePosition]:
        """Most recent ``limit`` positions for a single vehicle, newest first."""
        ...

    async def hourly_stats_for_line(self, *, line_id: str, hours: int) -> list[HourlyLineStat]:
        """Hourly aggregate buckets for a line, newest first, read from the
        ``vehicle_positions_hourly`` continuous aggregate."""
        ...

    async def refresh_hourly_rollup(self, *, hours: int) -> int:
        """Recompute ``vehicle_positions_hourly`` over the trailing ``hours``
        from raw rows (upsert by bucket+line). Stands in for the Timescale
        continuous-aggregate policy on plain Postgres. Returns rows written."""
        ...

    async def purge_raw_before(self, *, cutoff: datetime) -> int:
        """Delete raw ``vehicle_positions`` recorded before ``cutoff``. Stands
        in for the Timescale retention policy on plain Postgres. Returns rows
        deleted."""
        ...


class CatalogRepository(Protocol):
    """Persistence port for the static GTFS catalog.

    Imports are atomic batch replacements: ``replace_all`` deletes every row
    in agencies/routes/stops and writes the new bundle in one transaction.
    Single-version model for now — Phase 2 may introduce versioned imports.
    """

    async def replace_all(self, bundle: GtfsBundle) -> None: ...

    async def stops_within(
        self, *, center: Coordinate, radius_m: int, limit: int
    ) -> list[Stop]: ...

    async def list_routes(self, *, agency_id: str | None, limit: int) -> list[Route]: ...

    async def find_routes_by_short_name(self, short_name: str) -> list[Route]:
        """Multiple agencies can share a ``route_short_name``; return all matches."""
        ...

    async def find_stop_by_id(self, stop_id: str) -> Stop | None: ...

    async def arrivals_at_stop(
        self,
        *,
        stop_id: str,
        the_date: date,
        from_seconds: int,
        limit: int,
    ) -> list[ScheduledArrival]: ...

    async def shapes_for_line(self, short_name: str) -> list[list[Coordinate]]:
        """All distinct route shapes (polylines) for routes matching the
        ``short_name``. Each inner list is one ordered LineString."""
        ...

    # --- bulk reads for the offline snapshot bundle ---

    async def all_stops(self, *, limit: int) -> list[Stop]:
        """Every stop in the catalog (offline bundle)."""
        ...

    async def all_line_shapes(self) -> dict[str, list[list[Coordinate]]]:
        """``short_name`` → its distinct route shapes (each an ordered
        LineString). Mirrors ``shapes_for_line`` for every line at once."""
        ...

    async def line_headways(self) -> dict[str, int]:
        """``short_name`` → median ``headway_secs`` across the line's
        frequency windows. The offline "typical headway" hint."""
        ...

    async def latest_feed_version(self) -> str | None:
        """The most recently imported GTFS ``feed_version``, or ``None`` if
        the catalog has never been imported."""
        ...

    async def stop_line_index(self) -> dict[str, list[str]]:
        """``stop_id`` → sorted distinct route ``short_name``s serving it.
        The offline substitute for ``stop_times`` (bundle + typical headways)."""
        ...
