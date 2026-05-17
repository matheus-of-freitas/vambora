"""Static GTFS loader (zip download + parse).

The Rio feed is a standard GTFS bundle plus extended bus types (700-series).
We parse only `agency.txt`, `routes.txt`, `stops.txt`, and `feed_info.txt`
right now; trips/stop_times/shapes/calendar arrive when their use cases land.

Quirks observed against the TUMI mirror on 2026-05-09 (see
``plan.md`` Appendix: GTFS Quirks):

- Connection is flaky on the only working mirror; we use httpx with retries
  and an aggressive total timeout.
- ``stop_lat`` / ``stop_lon`` are dot-decimal floats here (unlike SPPO's
  comma-decimal strings). Standard GTFS shape.
- ``route_type`` includes 700 (bus, GTFS extended); we accept any int.
- ``feed_version`` lives in ``feed_info.txt`` (single-row file).
"""

from __future__ import annotations

import csv
import io
import zipfile
from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import date

import httpx

from vambora.domain.catalog import (
    Agency,
    Frequency,
    Route,
    ServiceCalendar,
    ServiceException,
    Shape,
    Stop,
    StopTime,
    Trip,
)
from vambora.domain.shared.types import Coordinate
from vambora.ports.outbound.gtfs_provider import GtfsBundle
from vambora.shared.errors import ProviderError
from vambora.shared.logger import get_logger

log = get_logger("gtfs")

_DOWNLOAD_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)
_MAX_ATTEMPTS = 5


class GtfsLoader:
    def __init__(self, *, source_url: str, http_client: httpx.AsyncClient) -> None:
        self._url = source_url
        self._http = http_client

    async def load(self) -> GtfsBundle:
        log.info("gtfs.fetch.start", url=self._url)
        zip_bytes = await self._download_with_retry()

        try:
            archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
        except zipfile.BadZipFile as exc:
            raise ProviderError(f"gtfs response was not a valid zip: {exc}") from exc

        agencies = list(_parse_agencies(_read_csv(archive, "agency.txt")))
        routes = list(_parse_routes(_read_csv(archive, "routes.txt")))
        stops = list(_parse_stops(_read_csv(archive, "stops.txt")))
        trips = list(_parse_trips(_read_csv(archive, "trips.txt")))
        stop_times = list(_parse_stop_times(_read_csv(archive, "stop_times.txt")))
        frequencies = list(_parse_frequencies(_read_csv(archive, "frequencies.txt")))
        calendars = list(_parse_calendar(_read_csv(archive, "calendar.txt")))
        exceptions = list(_parse_calendar_dates(_read_csv(archive, "calendar_dates.txt")))
        shapes = list(_parse_shapes(_read_csv(archive, "shapes.txt")))
        feed_version = _read_feed_version(archive)

        log.info(
            "gtfs.fetch.ok",
            feed_version=feed_version,
            agencies=len(agencies),
            routes=len(routes),
            stops=len(stops),
            trips=len(trips),
            stop_times=len(stop_times),
            frequencies=len(frequencies),
            calendars=len(calendars),
            exceptions=len(exceptions),
            shapes=len(shapes),
        )
        return GtfsBundle(
            feed_version=feed_version,
            source_url=self._url,
            agencies=agencies,
            routes=routes,
            stops=stops,
            trips=trips,
            stop_times=stop_times,
            frequencies=frequencies,
            calendars=calendars,
            exceptions=exceptions,
            shapes=shapes,
        )

    async def _download_with_retry(self) -> bytes:
        """The TUMI mirror frequently closes the connection mid-transfer.
        Retry the whole fetch up to ``_MAX_ATTEMPTS`` times before giving up."""
        last_exc: Exception | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                async with self._http.stream(
                    "GET", self._url, timeout=_DOWNLOAD_TIMEOUT
                ) as response:
                    response.raise_for_status()
                    expected = response.headers.get("content-length")
                    chunks: list[bytes] = []
                    async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
                        chunks.append(chunk)
                    body = b"".join(chunks)
                    if expected and len(body) != int(expected):
                        raise httpx.RemoteProtocolError(
                            f"truncated body: got {len(body)} of {expected} bytes",
                            request=response.request,
                        )
                    log.info("gtfs.fetch.attempt_ok", attempt=attempt, bytes=len(body))
                    return body
            except (httpx.HTTPError, httpx.RemoteProtocolError) as exc:
                log.warning("gtfs.fetch.attempt_failed", attempt=attempt, error=str(exc))
                last_exc = exc
        raise ProviderError(
            f"gtfs fetch failed after {_MAX_ATTEMPTS} attempts: {last_exc}"
        ) from last_exc


def _read_csv(archive: zipfile.ZipFile, name: str) -> Iterable[dict[str, str]]:
    if name not in archive.namelist():
        raise ProviderError(f"gtfs missing required file: {name}")
    with archive.open(name) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        yield from csv.DictReader(text)


def _read_feed_version(archive: zipfile.ZipFile) -> str:
    if "feed_info.txt" not in archive.namelist():
        return "unknown"
    rows = list(_read_csv(archive, "feed_info.txt"))
    if not rows:
        return "unknown"
    return rows[0].get("feed_version", "unknown") or "unknown"


def _parse_agencies(rows: Iterable[Mapping[str, str]]) -> Iterable[Agency]:
    for row in rows:
        yield Agency(
            agency_id=row["agency_id"],
            name=row["agency_name"],
            url=row.get("agency_url", ""),
            timezone=row.get("agency_timezone", "America/Sao_Paulo"),
            lang=_optional(row.get("agency_lang")),
        )


def _parse_routes(rows: Iterable[Mapping[str, str]]) -> Iterable[Route]:
    for row in rows:
        try:
            yield Route(
                route_id=row["route_id"],
                agency_id=row["agency_id"],
                short_name=row["route_short_name"],
                long_name=row.get("route_long_name", ""),
                route_type=int(row["route_type"]),
                color=_optional(row.get("route_color")),
                text_color=_optional(row.get("route_text_color")),
            )
        except (KeyError, ValueError) as exc:
            log.warning("gtfs.route.skipped", row=row, error=str(exc))


def _parse_stops(rows: Iterable[Mapping[str, str]]) -> Iterable[Stop]:
    for row in rows:
        try:
            yield Stop(
                stop_id=row["stop_id"],
                code=_optional(row.get("stop_code")),
                name=row["stop_name"],
                coordinate=Coordinate(
                    latitude=float(row["stop_lat"]),
                    longitude=float(row["stop_lon"]),
                ),
                parent_station=_optional(row.get("parent_station")),
                wheelchair_boarding=_optional_int(row.get("wheelchair_boarding")),
            )
        except (KeyError, ValueError) as exc:
            log.warning("gtfs.stop.skipped", row=row, error=str(exc))


def _parse_trips(rows: Iterable[Mapping[str, str]]) -> Iterable[Trip]:
    for row in rows:
        try:
            yield Trip(
                trip_id=row["trip_id"],
                route_id=row["route_id"],
                service_id=row["service_id"],
                headsign=_optional(row.get("trip_headsign")),
                direction_id=_optional_int(row.get("direction_id")),
                shape_id=_optional(row.get("shape_id")),
            )
        except (KeyError, ValueError) as exc:
            log.warning("gtfs.trip.skipped", row=row, error=str(exc))


def _parse_stop_times(rows: Iterable[Mapping[str, str]]) -> Iterable[StopTime]:
    for row in rows:
        try:
            yield StopTime(
                trip_id=row["trip_id"],
                stop_sequence=int(row["stop_sequence"]),
                stop_id=row["stop_id"],
                arrival_seconds=_hms_to_seconds(row["arrival_time"]),
                departure_seconds=_hms_to_seconds(row["departure_time"]),
            )
        except (KeyError, ValueError) as exc:
            log.warning("gtfs.stop_time.skipped", error=str(exc))


def _parse_shapes(rows: Iterable[Mapping[str, str]]) -> Iterable[Shape]:
    """Group shapes.txt rows by shape_id, sort by sequence, yield ``Shape``s."""
    by_id: dict[str, list[tuple[int, float, float]]] = defaultdict(list)
    for row in rows:
        try:
            sid = row["shape_id"]
            seq = int(row["shape_pt_sequence"])
            lat = float(row["shape_pt_lat"])
            lon = float(row["shape_pt_lon"])
        except (KeyError, ValueError) as exc:
            log.warning("gtfs.shape_point.skipped", error=str(exc))
            continue
        by_id[sid].append((seq, lon, lat))
    for sid, pts in by_id.items():
        pts.sort()
        coords = [Coordinate(latitude=lat, longitude=lon) for _, lon, lat in pts]
        if len(coords) < 2:
            log.warning("gtfs.shape.too_short", shape_id=sid, point_count=len(coords))
            continue
        yield Shape(shape_id=sid, points=coords)


def _parse_frequencies(rows: Iterable[Mapping[str, str]]) -> Iterable[Frequency]:
    for row in rows:
        try:
            yield Frequency(
                trip_id=row["trip_id"],
                start_seconds=_hms_to_seconds(row["start_time"]),
                end_seconds=_hms_to_seconds(row["end_time"]),
                headway_secs=int(row["headway_secs"]),
            )
        except (KeyError, ValueError) as exc:
            log.warning("gtfs.frequency.skipped", row=row, error=str(exc))


def _parse_calendar(rows: Iterable[Mapping[str, str]]) -> Iterable[ServiceCalendar]:
    for row in rows:
        try:
            yield ServiceCalendar(
                service_id=row["service_id"],
                monday=row["monday"] == "1",
                tuesday=row["tuesday"] == "1",
                wednesday=row["wednesday"] == "1",
                thursday=row["thursday"] == "1",
                friday=row["friday"] == "1",
                saturday=row["saturday"] == "1",
                sunday=row["sunday"] == "1",
                start_date=_yyyymmdd(row["start_date"]),
                end_date=_yyyymmdd(row["end_date"]),
            )
        except (KeyError, ValueError) as exc:
            log.warning("gtfs.calendar.skipped", row=row, error=str(exc))


def _parse_calendar_dates(rows: Iterable[Mapping[str, str]]) -> Iterable[ServiceException]:
    for row in rows:
        try:
            yield ServiceException(
                service_id=row["service_id"],
                calendar_date=_yyyymmdd(row["date"]),
                exception_type=int(row["exception_type"]),
            )
        except (KeyError, ValueError) as exc:
            log.warning("gtfs.calendar_date.skipped", row=row, error=str(exc))


def _hms_to_seconds(value: str) -> int:
    """Parse GTFS time strings ``HH:MM:SS`` to seconds-since-midnight.
    Handles past-midnight hours like ``25:30:00`` (returns 91800).
    """
    h, m, s = value.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


def _yyyymmdd(value: str) -> date:
    return date(int(value[0:4]), int(value[4:6]), int(value[6:8]))


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _optional_int(value: str | None) -> int | None:
    s = _optional(value)
    if s is None:
        return None
    try:
        return int(s)
    except ValueError:
        return None
