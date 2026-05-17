"""Forward-only migrations are the contract; reversibility (``downgrade``) is
the safety net. This test would have caught the 0005 ``ALTER TABLE`` bug — a
re-edited migration that no longer matches its applied state.
"""

from __future__ import annotations

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.integration


def _table_names(sync_url: str) -> set[str]:
    engine = create_engine(sync_url)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_round_trip_recreates_schema(alembic_cfg: Config, sync_url: str) -> None:
    """Going head → base → head should leave the schema identical."""
    expected = _table_names(sync_url)

    command.downgrade(alembic_cfg, "base")
    after_down = _table_names(sync_url)
    # Spatial reference and alembic version are the only tables we expect to
    # remain (PostGIS extension data + alembic bookkeeping).
    leftovers = after_down - {"spatial_ref_sys", "alembic_version"}
    assert leftovers == set(), f"downgrade left tables behind: {leftovers}"

    command.upgrade(alembic_cfg, "head")
    after_up = _table_names(sync_url)
    assert after_up == expected, (
        f"upgrade after downgrade produced different tables: "
        f"missing={expected - after_up} extra={after_up - expected}"
    )


def test_trips_has_shape_id(sync_url: str) -> None:
    """Regression test for the broken 0005 + missed-edit scenario.

    The original 0005 migration was edited after applying without a follow-up
    revision; production then 500'd because gtfs_trips.shape_id never landed.
    A real schema check via inspector catches this.
    """
    engine = create_engine(sync_url)
    try:
        cols = {c["name"] for c in inspect(engine).get_columns("gtfs_trips")}
    finally:
        engine.dispose()
    assert "shape_id" in cols, "gtfs_trips.shape_id missing — see 0006 migration"
