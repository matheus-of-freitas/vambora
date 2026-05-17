from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date
from typing import Any

from sqlalchemy import text

from vambora.adapters.outbound.persistence.unit_of_work import Database
from vambora.domain.catalog import Route, ScheduledArrival, Stop
from vambora.domain.shared.types import Coordinate
from vambora.ports.outbound.gtfs_provider import GtfsBundle


class PostgresCatalogRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def replace_all(self, bundle: GtfsBundle) -> None:
        """Atomic full-replace inside one transaction.

        Bulk inserts run in chunks for the large tables (stop_times can have
        ~1M rows in the Rio feed); other tables fit in a single statement.
        """
        async with self._db.connection() as conn:
            await conn.execute(text("DELETE FROM gtfs_shapes"))
            await conn.execute(text("DELETE FROM gtfs_frequencies"))
            await conn.execute(text("DELETE FROM gtfs_stop_times"))
            await conn.execute(text("DELETE FROM gtfs_calendar_dates"))
            await conn.execute(text("DELETE FROM gtfs_calendar"))
            await conn.execute(text("DELETE FROM gtfs_trips"))
            await conn.execute(text("DELETE FROM gtfs_stops"))
            await conn.execute(text("DELETE FROM gtfs_routes"))
            await conn.execute(text("DELETE FROM gtfs_agencies"))
            await conn.execute(
                text("DELETE FROM gtfs_imports WHERE feed_version = :v"),
                {"v": bundle.feed_version},
            )

            if bundle.agencies:
                await conn.execute(
                    text(
                        """
                        INSERT INTO gtfs_agencies
                            (agency_id, name, url, timezone, lang, feed_version)
                        VALUES
                            (:agency_id, :name, :url, :timezone, :lang, :feed_version)
                        """
                    ),
                    [
                        {
                            "agency_id": a.agency_id,
                            "name": a.name,
                            "url": a.url,
                            "timezone": a.timezone,
                            "lang": a.lang,
                            "feed_version": bundle.feed_version,
                        }
                        for a in bundle.agencies
                    ],
                )

            if bundle.routes:
                await conn.execute(
                    text(
                        """
                        INSERT INTO gtfs_routes
                            (route_id, agency_id, short_name, long_name, route_type,
                             color, text_color, feed_version)
                        VALUES
                            (:route_id, :agency_id, :short_name, :long_name, :route_type,
                             :color, :text_color, :feed_version)
                        """
                    ),
                    [
                        {
                            "route_id": r.route_id,
                            "agency_id": r.agency_id,
                            "short_name": r.short_name,
                            "long_name": r.long_name,
                            "route_type": r.route_type,
                            "color": r.color,
                            "text_color": r.text_color,
                            "feed_version": bundle.feed_version,
                        }
                        for r in bundle.routes
                    ],
                )

            if bundle.stops:
                await conn.execute(
                    text(
                        """
                        INSERT INTO gtfs_stops
                            (stop_id, code, name, position, parent_station,
                             wheelchair_boarding, feed_version)
                        VALUES
                            (:stop_id, :code, :name,
                             ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                             :parent_station, :wheelchair_boarding, :feed_version)
                        """
                    ),
                    [
                        {
                            "stop_id": s.stop_id,
                            "code": s.code,
                            "name": s.name,
                            "lat": s.coordinate.latitude,
                            "lon": s.coordinate.longitude,
                            "parent_station": s.parent_station,
                            "wheelchair_boarding": s.wheelchair_boarding,
                            "feed_version": bundle.feed_version,
                        }
                        for s in bundle.stops
                    ],
                )

            if bundle.trips:
                await conn.execute(
                    text(
                        """
                        INSERT INTO gtfs_trips
                            (trip_id, route_id, service_id, headsign,
                             direction_id, shape_id, feed_version)
                        VALUES
                            (:trip_id, :route_id, :service_id, :headsign,
                             :direction_id, :shape_id, :feed_version)
                        """
                    ),
                    [
                        {
                            "trip_id": t.trip_id,
                            "route_id": t.route_id,
                            "service_id": t.service_id,
                            "headsign": t.headsign,
                            "direction_id": t.direction_id,
                            "shape_id": t.shape_id,
                            "feed_version": bundle.feed_version,
                        }
                        for t in bundle.trips
                    ],
                )

            if bundle.calendars:
                await conn.execute(
                    text(
                        """
                        INSERT INTO gtfs_calendar
                            (service_id, monday, tuesday, wednesday, thursday,
                             friday, saturday, sunday, start_date, end_date,
                             feed_version)
                        VALUES
                            (:service_id, :monday, :tuesday, :wednesday, :thursday,
                             :friday, :saturday, :sunday, :start_date, :end_date,
                             :feed_version)
                        """
                    ),
                    [
                        {
                            "service_id": c.service_id,
                            "monday": c.monday,
                            "tuesday": c.tuesday,
                            "wednesday": c.wednesday,
                            "thursday": c.thursday,
                            "friday": c.friday,
                            "saturday": c.saturday,
                            "sunday": c.sunday,
                            "start_date": c.start_date,
                            "end_date": c.end_date,
                            "feed_version": bundle.feed_version,
                        }
                        for c in bundle.calendars
                    ],
                )

            if bundle.exceptions:
                await conn.execute(
                    text(
                        """
                        INSERT INTO gtfs_calendar_dates
                            (service_id, calendar_date, exception_type, feed_version)
                        VALUES
                            (:service_id, :calendar_date, :exception_type, :feed_version)
                        """
                    ),
                    [
                        {
                            "service_id": e.service_id,
                            "calendar_date": e.calendar_date,
                            "exception_type": e.exception_type,
                            "feed_version": bundle.feed_version,
                        }
                        for e in bundle.exceptions
                    ],
                )

            if bundle.stop_times:
                # ~1M rows for the Rio feed — batch to keep the param bind
                # surface manageable.
                stmt = text(
                    """
                    INSERT INTO gtfs_stop_times
                        (trip_id, stop_sequence, stop_id,
                         arrival_seconds, departure_seconds, feed_version)
                    VALUES
                        (:trip_id, :stop_sequence, :stop_id,
                         :arrival_seconds, :departure_seconds, :feed_version)
                    """
                )
                batch_size = 5000
                for start in range(0, len(bundle.stop_times), batch_size):
                    end = start + batch_size
                    chunk = bundle.stop_times[start:end]
                    await conn.execute(
                        stmt,
                        [
                            {
                                "trip_id": st.trip_id,
                                "stop_sequence": st.stop_sequence,
                                "stop_id": st.stop_id,
                                "arrival_seconds": st.arrival_seconds,
                                "departure_seconds": st.departure_seconds,
                                "feed_version": bundle.feed_version,
                            }
                            for st in chunk
                        ],
                    )

            if bundle.frequencies:
                await conn.execute(
                    text(
                        """
                        INSERT INTO gtfs_frequencies
                            (trip_id, start_seconds, end_seconds, headway_secs, feed_version)
                        VALUES
                            (:trip_id, :start_seconds, :end_seconds, :headway_secs, :feed_version)
                        """
                    ),
                    [
                        {
                            "trip_id": f.trip_id,
                            "start_seconds": f.start_seconds,
                            "end_seconds": f.end_seconds,
                            "headway_secs": f.headway_secs,
                            "feed_version": bundle.feed_version,
                        }
                        for f in bundle.frequencies
                    ],
                )

            if bundle.shapes:
                # Build LineString WKT in Python; one row per shape.
                stmt = text(
                    """
                    INSERT INTO gtfs_shapes (shape_id, geom, feed_version)
                    VALUES (:shape_id, ST_GeogFromText(:wkt), :feed_version)
                    """
                )
                batch_size = 200
                rows: list[dict[str, str]] = []
                for shape in bundle.shapes:
                    coords = ", ".join(f"{p.longitude} {p.latitude}" for p in shape.points)
                    rows.append(
                        {
                            "shape_id": shape.shape_id,
                            "wkt": f"SRID=4326;LINESTRING({coords})",
                            "feed_version": bundle.feed_version,
                        }
                    )
                for start in range(0, len(rows), batch_size):
                    await conn.execute(stmt, rows[start : start + batch_size])

            await conn.execute(
                text(
                    """
                    INSERT INTO gtfs_imports
                        (feed_version, source_url, agency_count, route_count, stop_count)
                    VALUES
                        (:v, :u, :a, :r, :s)
                    """
                ),
                {
                    "v": bundle.feed_version,
                    "u": bundle.source_url,
                    "a": len(bundle.agencies),
                    "r": len(bundle.routes),
                    "s": len(bundle.stops),
                },
            )

    async def find_stop_by_id(self, stop_id: str) -> Stop | None:
        sql = text(
            """
            SELECT stop_id, code, name,
                   ST_Y(position::geometry) AS latitude,
                   ST_X(position::geometry) AS longitude,
                   parent_station, wheelchair_boarding
            FROM gtfs_stops
            WHERE stop_id = :stop_id
            """
        )
        async with self._db.connection() as conn:
            result = await conn.execute(sql, {"stop_id": stop_id})
            row = result.first()
            if row is None:
                return None
            return _to_stop(dict(row._mapping))

    async def stops_within(self, *, center: Coordinate, radius_m: int, limit: int) -> list[Stop]:
        sql = text(
            """
            SELECT stop_id, code, name,
                   ST_Y(position::geometry) AS latitude,
                   ST_X(position::geometry) AS longitude,
                   parent_station, wheelchair_boarding
            FROM gtfs_stops
            WHERE ST_DWithin(
                position,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                :radius
            )
            ORDER BY position <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
            LIMIT :limit
            """
        )
        async with self._db.connection() as conn:
            result = await conn.execute(
                sql,
                {
                    "lat": center.latitude,
                    "lon": center.longitude,
                    "radius": radius_m,
                    "limit": limit,
                },
            )
            return [_to_stop(dict(row._mapping)) for row in result]

    async def list_routes(self, *, agency_id: str | None, limit: int) -> list[Route]:
        sql = text(
            """
            SELECT route_id, agency_id, short_name, long_name, route_type, color, text_color
            FROM gtfs_routes
            WHERE (CAST(:agency_id AS TEXT) IS NULL OR agency_id = CAST(:agency_id AS TEXT))
            ORDER BY short_name
            LIMIT :limit
            """
        )
        async with self._db.connection() as conn:
            result = await conn.execute(sql, {"agency_id": agency_id, "limit": limit})
            return [_to_route(dict(row._mapping)) for row in result]

    async def arrivals_at_stop(
        self,
        *,
        stop_id: str,
        the_date: date,
        from_seconds: int,
        limit: int,
    ) -> list[ScheduledArrival]:
        # Frequency-based GTFS feeds (the Rio feed is one) encode only one
        # canonical timing per trip in stop_times, then declare headway windows
        # in frequencies. We expand at query time:
        #   - Trips WITH a frequency entry: for each k where
        #     start_seconds + k*headway_secs < end_seconds, the effective
        #     arrival at this stop is freq.start + k*headway + delta, where
        #     delta = stop_time.arrival_seconds - first_stop.arrival_seconds.
        #   - Trips WITHOUT a frequency entry: use the canonical arrival_seconds.
        sql = text(
            """
            WITH active_services AS (
                SELECT service_id
                FROM gtfs_calendar
                WHERE start_date <= :the_date
                  AND end_date   >= :the_date
                  AND CASE EXTRACT(DOW FROM CAST(:the_date AS DATE))::int
                        WHEN 0 THEN sunday
                        WHEN 1 THEN monday
                        WHEN 2 THEN tuesday
                        WHEN 3 THEN wednesday
                        WHEN 4 THEN thursday
                        WHEN 5 THEN friday
                        WHEN 6 THEN saturday
                      END
                  AND service_id NOT IN (
                      SELECT service_id FROM gtfs_calendar_dates
                      WHERE calendar_date = :the_date AND exception_type = 2
                  )
                UNION
                SELECT service_id FROM gtfs_calendar_dates
                WHERE calendar_date = :the_date AND exception_type = 1
            ),
            trip_starts AS (
                SELECT trip_id, MIN(arrival_seconds) AS canonical_start
                FROM gtfs_stop_times
                GROUP BY trip_id
            ),
            stop_visits AS (
                SELECT
                    st.trip_id,
                    st.arrival_seconds AS canonical_arrival,
                    t.headsign,
                    t.route_id,
                    r.short_name,
                    r.long_name,
                    r.color
                FROM gtfs_stop_times st
                JOIN gtfs_trips  t USING (trip_id)
                JOIN gtfs_routes r USING (route_id)
                WHERE st.stop_id = :stop_id
                  AND t.service_id IN (SELECT service_id FROM active_services)
            ),
            expanded AS (
                -- Trips driven by frequencies: enumerate every (trip, departure k)
                SELECT
                    sv.trip_id,
                    f.start_seconds + k * f.headway_secs
                        + (sv.canonical_arrival - ts.canonical_start) AS effective_arrival,
                    sv.headsign, sv.route_id, sv.short_name, sv.long_name, sv.color
                FROM stop_visits sv
                JOIN gtfs_frequencies f USING (trip_id)
                JOIN trip_starts     ts USING (trip_id)
                CROSS JOIN LATERAL generate_series(
                    0,
                    GREATEST(0, (f.end_seconds - f.start_seconds) / f.headway_secs - 1)
                ) AS k
                UNION ALL
                -- Trips without frequencies: keep canonical arrival as-is.
                SELECT
                    sv.trip_id,
                    sv.canonical_arrival AS effective_arrival,
                    sv.headsign, sv.route_id, sv.short_name, sv.long_name, sv.color
                FROM stop_visits sv
                WHERE NOT EXISTS (
                    SELECT 1 FROM gtfs_frequencies f WHERE f.trip_id = sv.trip_id
                )
            )
            SELECT
                effective_arrival AS arrival_seconds,
                trip_id, headsign, route_id, short_name, long_name, color
            FROM expanded
            WHERE effective_arrival >= :from_seconds
            ORDER BY effective_arrival
            LIMIT :limit
            """
        )
        async with self._db.connection() as conn:
            result = await conn.execute(
                sql,
                {
                    "stop_id": stop_id,
                    "the_date": the_date,
                    "from_seconds": from_seconds,
                    "limit": limit,
                },
            )
            return [_to_arrival(dict(row._mapping)) for row in result]

    async def shapes_for_line(self, short_name: str) -> list[list[Coordinate]]:
        sql = text(
            """
            SELECT DISTINCT s.shape_id,
                   ST_AsGeoJSON(s.geom::geometry) AS geojson
            FROM gtfs_trips  t
            JOIN gtfs_routes r USING (route_id)
            JOIN gtfs_shapes s ON s.shape_id = t.shape_id
            WHERE r.short_name = :short_name
            """
        )
        async with self._db.connection() as conn:
            result = await conn.execute(sql, {"short_name": short_name})
            shapes: list[list[Coordinate]] = []
            for row in result:
                geo = json.loads(row._mapping["geojson"])
                if geo.get("type") != "LineString":
                    continue
                pts = [Coordinate(latitude=lat, longitude=lon) for lon, lat in geo["coordinates"]]
                shapes.append(pts)
            return shapes

    async def find_routes_by_short_name(self, short_name: str) -> list[Route]:
        sql = text(
            """
            SELECT route_id, agency_id, short_name, long_name, route_type, color, text_color
            FROM gtfs_routes
            WHERE short_name = :short_name
            ORDER BY agency_id
            """
        )
        async with self._db.connection() as conn:
            result = await conn.execute(sql, {"short_name": short_name})
            return [_to_route(dict(row._mapping)) for row in result]

    async def all_stops(self, *, limit: int) -> list[Stop]:
        sql = text(
            """
            SELECT stop_id, code, name,
                   ST_Y(position::geometry) AS latitude,
                   ST_X(position::geometry) AS longitude,
                   parent_station, wheelchair_boarding
            FROM gtfs_stops
            ORDER BY stop_id
            LIMIT :limit
            """
        )
        async with self._db.connection() as conn:
            result = await conn.execute(sql, {"limit": limit})
            return [_to_stop(dict(row._mapping)) for row in result]

    async def all_line_shapes(self) -> dict[str, list[list[Coordinate]]]:
        sql = text(
            """
            SELECT DISTINCT r.short_name,
                   ST_AsGeoJSON(s.geom::geometry) AS geojson
            FROM gtfs_trips  t
            JOIN gtfs_routes r USING (route_id)
            JOIN gtfs_shapes s ON s.shape_id = t.shape_id
            """
        )
        out: dict[str, list[list[Coordinate]]] = {}
        async with self._db.connection() as conn:
            result = await conn.execute(sql)
            for row in result:
                geo = json.loads(row._mapping["geojson"])
                if geo.get("type") != "LineString":
                    continue
                pts = [Coordinate(latitude=lat, longitude=lon) for lon, lat in geo["coordinates"]]
                out.setdefault(row._mapping["short_name"], []).append(pts)
        return out

    async def line_headways(self) -> dict[str, int]:
        sql = text(
            """
            SELECT r.short_name,
                   percentile_cont(0.5) WITHIN GROUP (ORDER BY f.headway_secs) AS median
            FROM gtfs_frequencies f
            JOIN gtfs_trips  t USING (trip_id)
            JOIN gtfs_routes r USING (route_id)
            GROUP BY r.short_name
            """
        )
        async with self._db.connection() as conn:
            result = await conn.execute(sql)
            return {
                row._mapping["short_name"]: int(row._mapping["median"])
                for row in result
                if row._mapping["median"] is not None
            }

    async def latest_feed_version(self) -> str | None:
        sql = text(
            "SELECT feed_version FROM gtfs_imports ORDER BY imported_at DESC LIMIT 1"
        )
        async with self._db.connection() as conn:
            result = await conn.execute(sql)
            row = result.first()
            return None if row is None else str(row._mapping["feed_version"])

    async def stop_line_index(self) -> dict[str, list[str]]:
        sql = text(
            """
            SELECT DISTINCT st.stop_id, r.short_name
            FROM gtfs_stop_times st
            JOIN gtfs_trips  t USING (trip_id)
            JOIN gtfs_routes r USING (route_id)
            """
        )
        out: dict[str, list[str]] = {}
        async with self._db.connection() as conn:
            result = await conn.execute(sql)
            for row in result:
                out.setdefault(row._mapping["stop_id"], []).append(row._mapping["short_name"])
        return {stop_id: sorted(set(lines)) for stop_id, lines in out.items()}


def _to_stop(row: Mapping[str, Any]) -> Stop:
    return Stop(
        stop_id=row["stop_id"],
        code=row["code"],
        name=row["name"],
        coordinate=Coordinate(latitude=float(row["latitude"]), longitude=float(row["longitude"])),
        parent_station=row["parent_station"],
        wheelchair_boarding=row["wheelchair_boarding"],
    )


def _to_route(row: Mapping[str, Any]) -> Route:
    return Route(
        route_id=row["route_id"],
        agency_id=row["agency_id"],
        short_name=row["short_name"],
        long_name=row["long_name"],
        route_type=row["route_type"],
        color=row["color"],
        text_color=row["text_color"],
    )


def _to_arrival(row: Mapping[str, Any]) -> ScheduledArrival:
    return ScheduledArrival(
        arrival_seconds=int(row["arrival_seconds"]),
        trip_id=row["trip_id"],
        headsign=row["headsign"],
        route_id=row["route_id"],
        route_short_name=row["short_name"],
        route_long_name=row["long_name"],
        route_color=row["color"],
    )
