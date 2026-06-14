from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text

from vambora.adapters.outbound.persistence.unit_of_work import Database
from vambora.domain.shared.types import Coordinate
from vambora.domain.tracking import HourlyLineStat, VehiclePosition

# How many raw rows one purge DELETE removes before committing and looping.
# Keeps locks short and transactions small on a busy table.
_PURGE_BATCH = 10_000

_HOURLY_STATS_SQL = text(
    """
    SELECT bucket, position_count, vehicle_count, avg_speed_kmh, max_speed_kmh
    FROM vehicle_positions_hourly
    WHERE line_id = :line_id
      AND bucket > NOW() - make_interval(hours => :hours)
    ORDER BY bucket DESC
    """
)

_INSERT_SQL = text(
    """
    INSERT INTO vehicle_positions
        (vehicle_id, line_id, recorded_at, sent_at, received_at, position, speed_kmh, raw)
    VALUES
        (:vehicle_id, :line_id, :recorded_at, :sent_at, :received_at,
         ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
         :speed_kmh, CAST(:raw AS JSONB))
    ON CONFLICT (vehicle_id, recorded_at) DO NOTHING
    RETURNING 1
    """
)

_LATEST_SQL = text(
    """
    SELECT DISTINCT ON (vehicle_id)
        vehicle_id,
        line_id,
        recorded_at,
        sent_at,
        received_at,
        ST_Y(position::geometry) AS latitude,
        ST_X(position::geometry) AS longitude,
        speed_kmh,
        raw
    FROM vehicle_positions
    -- Liveness gates on received_at (server arrival), per plan.md decision #25
    -- and the SPPO appendix: a fresh window can include GPS fixes whose
    -- recorded_at is hours old. We still ORDER BY recorded_at DESC so the
    -- *displayed* position is the most recent actual GPS fix we hold.
    WHERE received_at > NOW() - make_interval(secs => :fresh_seconds)
      AND (CAST(:line_id AS TEXT) IS NULL OR line_id = CAST(:line_id AS TEXT))
    ORDER BY vehicle_id, recorded_at DESC
    LIMIT :limit
    """
)

_HISTORY_SQL = text(
    """
    SELECT vehicle_id, line_id, recorded_at, sent_at, received_at,
           ST_Y(position::geometry) AS latitude,
           ST_X(position::geometry) AS longitude,
           speed_kmh,
           raw
    FROM vehicle_positions
    WHERE vehicle_id = :vehicle_id
    ORDER BY recorded_at DESC
    LIMIT :limit
    """
)

# Recompute the trailing hourly buckets from raw rows and upsert them. The
# plain-Postgres stand-in for the Timescale continuous-aggregate policy; safe
# to run repeatedly since the last (still-filling) buckets get corrected on the
# next pass.
_ROLLUP_SQL = text(
    """
    INSERT INTO vehicle_positions_hourly
        (bucket, line_id, position_count, vehicle_count, avg_speed_kmh, max_speed_kmh)
    SELECT
        date_trunc('hour', recorded_at) AS bucket,
        line_id,
        count(*)                    AS position_count,
        count(DISTINCT vehicle_id)  AS vehicle_count,
        avg(speed_kmh)              AS avg_speed_kmh,
        max(speed_kmh)              AS max_speed_kmh
    FROM vehicle_positions
    WHERE recorded_at > NOW() - make_interval(hours => :hours)
    GROUP BY 1, 2
    ON CONFLICT (bucket, line_id) DO UPDATE SET
        position_count = EXCLUDED.position_count,
        vehicle_count  = EXCLUDED.vehicle_count,
        avg_speed_kmh  = EXCLUDED.avg_speed_kmh,
        max_speed_kmh  = EXCLUDED.max_speed_kmh
    """
)

# ctid-limited batched delete: bound each statement's row count so retention on
# a high-volume table never takes a long lock.
_PURGE_SQL = text(
    """
    DELETE FROM vehicle_positions
    WHERE ctid IN (
        SELECT ctid FROM vehicle_positions
        WHERE recorded_at < :cutoff
        LIMIT :batch
    )
    """
)


class PostgresVehiclePositionRepository:
    def __init__(self, db: Database, *, store_raw: bool = True) -> None:
        self._db = db
        self._store_raw = store_raw

    async def upsert_many(self, positions: list[VehiclePosition]) -> int:
        if not positions:
            return 0
        rows = [
            {
                "vehicle_id": p.vehicle_id,
                "line_id": p.line_id,
                "recorded_at": p.recorded_at,
                "sent_at": p.sent_at,
                "received_at": p.received_at,
                "lat": p.coordinate.latitude,
                "lon": p.coordinate.longitude,
                "speed_kmh": p.speed_kmh,
                # Dropping the raw payload (store_raw=False) is the biggest size
                # lever on a small free-tier database; parsed columns are
                # untouched.
                "raw": json.dumps(p.raw) if self._store_raw else "{}",
            }
            for p in positions
        ]
        # asyncpg's executemany rowcount is unreliable; count actual returns instead.
        inserted = 0
        async with self._db.connection() as conn:
            for row in rows:
                result = await conn.execute(_INSERT_SQL, row)
                inserted += len(result.fetchall())
        return inserted

    async def latest_per_vehicle(
        self, *, line_id: str | None, fresh_seconds: int, limit: int
    ) -> list[VehiclePosition]:
        async with self._db.connection() as conn:
            result = await conn.execute(
                _LATEST_SQL,
                {"line_id": line_id, "fresh_seconds": fresh_seconds, "limit": limit},
            )
            return [_row_to_domain(dict(row._mapping)) for row in result]

    async def history_for(self, vehicle_id: str, *, limit: int) -> list[VehiclePosition]:
        async with self._db.connection() as conn:
            result = await conn.execute(_HISTORY_SQL, {"vehicle_id": vehicle_id, "limit": limit})
            return [_row_to_domain(dict(row._mapping)) for row in result]

    async def hourly_stats_for_line(self, *, line_id: str, hours: int) -> list[HourlyLineStat]:
        async with self._db.connection() as conn:
            result = await conn.execute(_HOURLY_STATS_SQL, {"line_id": line_id, "hours": hours})
            return [
                HourlyLineStat(
                    bucket=_aware(r._mapping["bucket"]),
                    position_count=int(r._mapping["position_count"]),
                    vehicle_count=int(r._mapping["vehicle_count"]),
                    avg_speed_kmh=float(r._mapping["avg_speed_kmh"] or 0.0),
                    max_speed_kmh=float(r._mapping["max_speed_kmh"] or 0.0),
                )
                for r in result
            ]

    async def refresh_hourly_rollup(self, *, hours: int) -> int:
        async with self._db.connection() as conn:
            result = await conn.execute(_ROLLUP_SQL, {"hours": hours})
            return result.rowcount

    async def purge_raw_before(self, *, cutoff: datetime) -> int:
        total = 0
        while True:
            # Each batch is its own transaction (connection() wraps engine.begin),
            # so committed deletes free space even if a later batch is interrupted.
            async with self._db.connection() as conn:
                result = await conn.execute(_PURGE_SQL, {"cutoff": cutoff, "batch": _PURGE_BATCH})
            deleted = result.rowcount
            total += deleted
            if deleted < _PURGE_BATCH:
                break
        return total


def _row_to_domain(row: Mapping[str, Any]) -> VehiclePosition:
    return VehiclePosition(
        vehicle_id=row["vehicle_id"],
        line_id=row["line_id"],
        recorded_at=_aware(row["recorded_at"]),
        sent_at=_aware(row["sent_at"]),
        received_at=_aware(row["received_at"]),
        coordinate=Coordinate(
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
        ),
        speed_kmh=float(row["speed_kmh"]),
        raw=row["raw"],
    )


def _aware(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    raise TypeError(f"expected datetime, got {type(value).__name__}")
