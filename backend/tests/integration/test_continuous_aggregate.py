"""The hourly continuous aggregate (migration 0008) + the stats query path.

``refresh_continuous_aggregate`` cannot run inside a transaction, so we open a
dedicated AUTOCOMMIT connection for the refresh, separate from the ``db``
fixture's transactional scope.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from vambora.adapters.outbound.persistence.repositories.vehicle_positions import (
    PostgresVehiclePositionRepository,
)
from vambora.domain.shared.types import Coordinate
from vambora.domain.tracking import VehiclePosition

pytestmark = pytest.mark.integration


def _pos(vehicle_id: str, recorded_at: datetime, speed: float) -> VehiclePosition:
    return VehiclePosition(
        vehicle_id=vehicle_id,
        line_id="485",
        recorded_at=recorded_at,
        sent_at=recorded_at,
        received_at=recorded_at,
        coordinate=Coordinate(latitude=-22.9, longitude=-43.2),
        speed_kmh=speed,
        raw={"ordem": vehicle_id},
    )


async def test_hourly_aggregate_buckets_and_query(db, async_url: str) -> None:  # type: ignore[no-untyped-def]
    repo = PostgresVehiclePositionRepository(db)

    # Two vehicles, three fixes, all inside one hour two hours ago (so the
    # bucket is closed relative to the aggregate's end_offset window).
    base = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) - timedelta(hours=2)
    await repo.upsert_many(
        [
            _pos("V1", base + timedelta(minutes=5), 10.0),
            _pos("V1", base + timedelta(minutes=35), 30.0),
            _pos("V2", base + timedelta(minutes=15), 50.0),
        ]
    )

    # Refresh the aggregate over a window covering our bucket. AUTOCOMMIT
    # because refresh_continuous_aggregate is not transaction-safe.
    engine = create_async_engine(async_url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as conn:
            await conn.execute(
                text(
                    "CALL refresh_continuous_aggregate("
                    "'vehicle_positions_hourly', "
                    "CAST(:start AS timestamptz), CAST(:end AS timestamptz))"
                ),
                {
                    "start": base - timedelta(hours=1),
                    "end": base + timedelta(hours=2),
                },
            )
    finally:
        await engine.dispose()

    stats = await repo.hourly_stats_for_line(line_id="485", hours=6)
    assert len(stats) == 1
    bucket = stats[0]
    assert bucket.position_count == 3
    assert bucket.vehicle_count == 2
    assert bucket.max_speed_kmh == pytest.approx(50.0)
    assert bucket.avg_speed_kmh == pytest.approx((10.0 + 30.0 + 50.0) / 3, abs=0.01)


async def test_stats_query_empty_for_unknown_line(db) -> None:  # type: ignore[no-untyped-def]
    repo = PostgresVehiclePositionRepository(db)
    assert await repo.hourly_stats_for_line(line_id="NOPE", hours=24) == []
