from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text

from src import db

app = FastAPI(title="Vambora SPPO Spike", version="0.0.1")


@app.get("/health")
async def health() -> dict[str, Any]:
    async with db.connection() as conn:
        result = await conn.execute(text("SELECT 1"))
        ok = result.scalar_one() == 1
    return {"ok": ok}


@app.get("/vehicles")
async def vehicles(
    line_id: str | None = Query(default=None),
    fresh_seconds: int = Query(default=120, ge=10, le=3600),
    limit: int = Query(default=2000, ge=1, le=10000),
) -> list[dict[str, Any]]:
    """Latest position per vehicle within `fresh_seconds`, optionally filtered by line."""
    sql = text(
        """
        SELECT DISTINCT ON (vehicle_id)
            vehicle_id,
            line_id,
            recorded_at,
            sent_at,
            received_at,
            ST_Y(position::geometry) AS latitude,
            ST_X(position::geometry) AS longitude,
            speed_kmh
        FROM vehicle_positions
        WHERE recorded_at > NOW() - make_interval(secs => :fresh_seconds)
          AND (CAST(:line_id AS TEXT) IS NULL OR line_id = CAST(:line_id AS TEXT))
        ORDER BY vehicle_id, recorded_at DESC
        LIMIT :limit
        """
    )
    async with db.connection() as conn:
        result = await conn.execute(
            sql, {"line_id": line_id, "fresh_seconds": fresh_seconds, "limit": limit}
        )
        rows = result.mappings().all()
    return [dict(r) for r in rows]


@app.get("/vehicles/{vehicle_id}")
async def vehicle_history(
    vehicle_id: str,
    limit: int = Query(default=50, ge=1, le=500),
) -> list[dict[str, Any]]:
    sql = text(
        """
        SELECT vehicle_id, line_id, recorded_at, sent_at, received_at,
               ST_Y(position::geometry) AS latitude,
               ST_X(position::geometry) AS longitude,
               speed_kmh
        FROM vehicle_positions
        WHERE vehicle_id = :vehicle_id
        ORDER BY recorded_at DESC
        LIMIT :limit
        """
    )
    async with db.connection() as conn:
        result = await conn.execute(sql, {"vehicle_id": vehicle_id, "limit": limit})
        rows = result.mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="vehicle not found")
    return [dict(r) for r in rows]


@app.get("/stats")
async def stats() -> dict[str, Any]:
    sql = text(
        """
        SELECT
            COUNT(*)                                AS total_rows,
            COUNT(DISTINCT vehicle_id)              AS unique_vehicles,
            COUNT(DISTINCT line_id)                 AS unique_lines,
            MIN(recorded_at)                        AS oldest,
            MAX(recorded_at)                        AS newest
        FROM vehicle_positions
        """
    )
    async with db.connection() as conn:
        result = await conn.execute(sql)
        row = result.mappings().one()
    return dict(row)


def _datetime_default(o: Any) -> str:
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError
