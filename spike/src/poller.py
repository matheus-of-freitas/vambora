from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, timedelta

import httpx
import structlog
from sqlalchemy import text

from src import db, sppo
from src.config import settings

log = structlog.get_logger("poller")

INSERT_SQL = text(
    """
    INSERT INTO vehicle_positions
        (vehicle_id, line_id, recorded_at, sent_at, received_at, position, speed_kmh, raw)
    VALUES
        (:vehicle_id, :line_id, :recorded_at, :sent_at, :received_at,
         ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
         :speed_kmh, CAST(:raw AS JSONB))
    ON CONFLICT (vehicle_id, recorded_at) DO NOTHING
    """
)


async def _persist(positions: list[sppo.VehiclePosition]) -> int:
    if not positions:
        return 0
    import json
    rows = [
        {
            "vehicle_id": p.vehicle_id,
            "line_id": p.line_id,
            "recorded_at": p.recorded_at,
            "sent_at": p.sent_at,
            "received_at": p.received_at,
            "lat": p.latitude,
            "lon": p.longitude,
            "speed_kmh": p.speed_kmh,
            "raw": json.dumps(p.raw),
        }
        for p in positions
    ]
    async with db.connection() as conn:
        result = await conn.execute(INSERT_SQL, rows)
    # rowcount on multi-row execute is driver-specific; treat as best-effort.
    return result.rowcount if result.rowcount and result.rowcount > 0 else len(rows)


async def _tick(client: httpx.AsyncClient, until: datetime) -> None:
    since = until - timedelta(seconds=settings.window_seconds)
    started = time.perf_counter()
    try:
        positions = await sppo.fetch(client, since=since, until=until)
    except httpx.HTTPError as exc:
        log.warning("sppo.fetch_failed", error=str(exc))
        return
    fetch_ms = (time.perf_counter() - started) * 1000

    persisted = await _persist(positions)
    total_ms = (time.perf_counter() - started) * 1000

    log.info(
        "tick.ok",
        records=len(positions),
        persisted=persisted,
        unique_vehicles=len({p.vehicle_id for p in positions}),
        unique_lines=len({p.line_id for p in positions}),
        fetch_ms=round(fetch_ms, 1),
        total_ms=round(total_ms, 1),
        window_s=settings.window_seconds,
    )


async def run_forever() -> None:
    log.info(
        "poller.start",
        url=settings.sppo_url,
        interval=settings.poll_interval_seconds,
        window=settings.window_seconds,
    )
    async with httpx.AsyncClient() as client:
        while True:
            await _tick(client, datetime.now(UTC))
            await asyncio.sleep(settings.poll_interval_seconds)
