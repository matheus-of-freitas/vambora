"""The no-Timescale path end to end, on a plain ``postgis/postgis`` container.

Proves the serverless database story: the same Alembic migrations run on plain
Postgres+PostGIS (taking their non-Timescale branches), and CompactTrackingData
fills the hourly rollup and purges raw rows — the work that Timescale's
continuous-aggregate and retention policies do locally.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from testcontainers.postgres import PostgresContainer

from vambora.adapters.outbound.persistence.repositories.vehicle_positions import (
    PostgresVehiclePositionRepository,
)
from vambora.adapters.outbound.persistence.unit_of_work import Database
from vambora.application.commands.compact_tracking_data import CompactTrackingData
from vambora.domain.shared.types import Coordinate
from vambora.domain.tracking import VehiclePosition

pytestmark = pytest.mark.integration


class _FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


@pytest.fixture(scope="module")
def plain_pg() -> Iterator[PostgresContainer]:
    # No TimescaleDB extension available → migrations take the plain branch.
    image = "postgis/postgis:16-3.4"
    with PostgresContainer(
        image, username="postgres", password="postgres", dbname="vambora"
    ) as pg:
        yield pg


def _to_driver(raw: str, driver: str) -> str:
    for prefix in ("postgresql+psycopg2://", "postgresql://"):
        if raw.startswith(prefix):
            return raw.replace(prefix, f"postgresql+{driver}://", 1)
    return raw


@pytest.fixture(scope="module")
def plain_async_url(plain_pg: PostgresContainer) -> str:
    return _to_driver(plain_pg.get_connection_url(), "asyncpg")


@pytest.fixture(scope="module", autouse=True)
def _migrate_plain(plain_pg: PostgresContainer) -> None:
    sync_url = _to_driver(plain_pg.get_connection_url(), "psycopg")
    cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", sync_url)
    cfg.set_main_option(
        "script_location", "src/vambora/adapters/outbound/persistence/migrations"
    )
    command.upgrade(cfg, "head")


@pytest_asyncio.fixture
async def plain_db(plain_async_url: str) -> AsyncIterator[Database]:
    database = Database(plain_async_url)
    yield database
    await database.dispose()


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


async def test_compaction_rolls_up_and_purges_on_plain_postgres(plain_db: Database) -> None:
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    repo = PostgresVehiclePositionRepository(plain_db, store_raw=False)

    # Recent fixes (kept) inside one hour, plus an old fix (past retention).
    recent_hour = now - timedelta(hours=1)
    await repo.upsert_many(
        [
            _pos("V1", recent_hour + timedelta(minutes=5), 10.0),
            _pos("V1", recent_hour + timedelta(minutes=35), 30.0),
            _pos("V2", recent_hour + timedelta(minutes=15), 50.0),
            _pos("V9", now - timedelta(hours=48), 20.0),
        ]
    )

    compact = CompactTrackingData(
        repository=repo,
        clock=_FixedClock(now),
        timescale=False,
        retention_hours=24,
        rollup_hours=3,
    )
    result = await compact()

    assert not result.skipped
    assert result.purged == 1  # only the 48h-old row

    # Rollup table is readable through the unchanged stats query.
    stats = await repo.hourly_stats_for_line(line_id="485", hours=6)
    assert len(stats) == 1
    assert stats[0].position_count == 3
    assert stats[0].vehicle_count == 2
    assert stats[0].max_speed_kmh == pytest.approx(50.0)
