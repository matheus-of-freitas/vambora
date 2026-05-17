"""Integration-test fixtures: spin up a real Postgres+TimescaleDB+PostGIS via
testcontainers, apply our Alembic migrations once per session, and hand each
test a freshly-truncated async ``Database``."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import text as sa_text
from testcontainers.postgres import PostgresContainer

from vambora.adapters.outbound.persistence.unit_of_work import Database

# Tables to truncate between tests, in FK-safe order.
_TABLES = [
    "alert_rules",
    "vehicle_positions",
    "gtfs_shapes",
    "gtfs_frequencies",
    "gtfs_stop_times",
    "gtfs_calendar_dates",
    "gtfs_calendar",
    "gtfs_trips",
    "gtfs_stops",
    "gtfs_routes",
    "gtfs_agencies",
    "gtfs_imports",
]


@pytest.fixture(scope="session")
def pg_container() -> Iterator[PostgresContainer]:
    """Spin up a real Postgres+TimescaleDB+PostGIS for the whole test session."""
    image = "timescale/timescaledb-ha:pg16"
    with PostgresContainer(image, username="postgres", password="postgres", dbname="vambora") as pg:
        yield pg


@pytest.fixture(scope="session")
def sync_url(pg_container: PostgresContainer) -> str:
    """Sync URL for Alembic. testcontainers gives us a psycopg2-style URL by
    default; rewrite to psycopg (v3) which we use in dev too."""
    raw = pg_container.get_connection_url()
    if raw.startswith("postgresql+psycopg2://"):
        return raw.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw


@pytest.fixture(scope="session")
def async_url(pg_container: PostgresContainer) -> str:
    """Async URL for the production code path."""
    raw = pg_container.get_connection_url()
    if raw.startswith("postgresql+psycopg2://"):
        return raw.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw


def _alembic_cfg(sync_url: str) -> Config:
    cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", sync_url)
    cfg.set_main_option(
        "script_location",
        "src/vambora/adapters/outbound/persistence/migrations",
    )
    return cfg


@pytest.fixture(scope="session")
def alembic_cfg(sync_url: str) -> Config:
    return _alembic_cfg(sync_url)


@pytest.fixture(scope="session", autouse=True)
def apply_migrations(alembic_cfg: Config) -> None:
    """Run the full upgrade once per session. The Alembic round-trip test runs
    its own downgrade/upgrade against a fresh state, but every other test relies
    on having a migrated schema available."""
    command.upgrade(alembic_cfg, "head")


@pytest_asyncio.fixture
async def db(async_url: str) -> AsyncIterator[Database]:
    """Function-scoped async ``Database`` with truncated tables on entry.

    Truncation is the cheapest reset — keeps schema, drops data. We use it
    rather than DROP/CREATE so that the migrations only run once per session.
    """
    database = Database(async_url)
    async with database.connection() as conn:
        await conn.execute(sa_text(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY CASCADE"))
    try:
        yield database
    finally:
        await database.dispose()
