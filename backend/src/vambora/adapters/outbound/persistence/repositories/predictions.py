"""Naive real-time ETA query (plan.md decision #7).

For a stop, take each *live* vehicle (latest fix, ``received_at`` within the
freshness window — decision #25) whose SPPO ``line_id`` matches a GTFS route
serving the stop. Snap the vehicle and the stop onto the route shape with
``ST_LineLocatePoint`` and take the along-route gap as the remaining distance.
ETA = remaining ÷ speed, where speed is the vehicle's own reading floored by a
fallback so a stopped bus still produces a finite, ordered estimate.

Crude on purpose:
- Fraction x geodesic length assumes ~uniform shape-point spacing.
- A line's many shape variants are disambiguated only by "closest shape to the
  vehicle", which also gives a rough direction filter (a stop not on the
  vehicle's shape within ``max_snap_m`` simply yields no prediction).
- No trip pairing, dwell time, or traffic. Phase 2 swaps in an ML model.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text

from vambora.adapters.outbound.persistence.unit_of_work import Database
from vambora.domain.predictions import ArrivalPrediction

# Numeric binds are CAST explicitly: asyncpg can't infer a param's type when it
# appears only inside an expression (recurring across this codebase).
_PREDICT_SQL = text(
    """
    WITH stop AS (
        SELECT position AS gg, position::geometry AS g
        FROM gtfs_stops
        WHERE stop_id = CAST(:stop_id AS text)
    ),
    line_shapes AS (
        SELECT DISTINCT r.short_name, r.long_name, r.color,
               s.shape_id, s.geom::geometry AS sg
        FROM gtfs_stop_times st
        JOIN gtfs_trips  t USING (trip_id)
        JOIN gtfs_routes r USING (route_id)
        JOIN gtfs_shapes s ON s.shape_id = t.shape_id
        CROSS JOIN stop
        WHERE st.stop_id = CAST(:stop_id AS text)
          AND ST_DWithin(s.geom, stop.gg, CAST(:max_snap_m AS double precision))
    ),
    live AS (
        SELECT DISTINCT ON (vehicle_id)
            vehicle_id, line_id, speed_kmh,
            position::geometry AS vg
        FROM vehicle_positions
        WHERE received_at > NOW() - make_interval(
            secs => CAST(:fresh_seconds AS double precision))
        ORDER BY vehicle_id, recorded_at DESC
    ),
    matched AS (
        SELECT DISTINCT ON (l.vehicle_id)
            l.vehicle_id, ls.short_name, ls.long_name, ls.color,
            l.speed_kmh, ls.sg, l.vg
        FROM live l
        JOIN line_shapes ls ON ls.short_name = l.line_id
        ORDER BY l.vehicle_id, ST_Distance(ls.sg::geography, l.vg::geography)
    ),
    projected AS (
        SELECT
            m.vehicle_id, m.short_name, m.long_name, m.color,
            GREATEST(m.speed_kmh, CAST(:fallback_kmh AS double precision)) AS used_kmh,
            ST_LineLocatePoint(m.sg, m.vg) AS vf,
            ST_LineLocatePoint(m.sg, s.g) AS sf,
            ST_Length(m.sg::geography)    AS total_m,
            ST_Distance(m.sg::geography, m.vg::geography) AS snap_m
        FROM matched m
        CROSS JOIN stop s
    ),
    eta AS (
        SELECT
            short_name, vehicle_id, long_name, color, used_kmh,
            (sf - vf) * total_m AS remaining_m
        FROM projected
        WHERE sf > vf
          AND snap_m <= CAST(:max_snap_m AS double precision)
    )
    SELECT
        short_name,
        vehicle_id,
        remaining_m AS distance_m,
        used_kmh    AS speed_kmh,
        (remaining_m / (used_kmh / 3.6))::int AS eta_seconds,
        NOW() + make_interval(secs => remaining_m / (used_kmh / 3.6)) AS eta_at,
        long_name AS route_long_name,
        color     AS route_color
    FROM eta
    WHERE remaining_m / (used_kmh / 3.6)
          <= CAST(:max_horizon_seconds AS double precision)
    ORDER BY eta_seconds
    LIMIT CAST(:limit AS integer)
    """
)


class PostgresPredictionRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def predict_stop_arrivals(
        self,
        *,
        stop_id: str,
        fresh_seconds: int,
        fallback_kmh: float,
        max_horizon_seconds: int,
        max_snap_m: float,
        limit: int,
    ) -> list[ArrivalPrediction]:
        async with self._db.connection() as conn:
            result = await conn.execute(
                _PREDICT_SQL,
                {
                    "stop_id": stop_id,
                    "fresh_seconds": fresh_seconds,
                    "fallback_kmh": fallback_kmh,
                    "max_horizon_seconds": max_horizon_seconds,
                    "max_snap_m": max_snap_m,
                    "limit": limit,
                },
            )
            return [_to_prediction(dict(row._mapping)) for row in result]


def _to_prediction(row: Mapping[str, Any]) -> ArrivalPrediction:
    eta_at = row["eta_at"]
    if isinstance(eta_at, datetime) and eta_at.tzinfo is None:
        eta_at = eta_at.replace(tzinfo=UTC)
    return ArrivalPrediction(
        line_short_name=row["short_name"],
        vehicle_id=row["vehicle_id"],
        distance_m=float(row["distance_m"]),
        speed_kmh=float(row["speed_kmh"]),
        eta_seconds=int(row["eta_seconds"]),
        eta_at=eta_at,
        route_long_name=row["route_long_name"],
        route_color=row["route_color"],
    )
