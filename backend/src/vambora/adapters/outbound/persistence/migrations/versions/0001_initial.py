"""initial: extensions, vehicle_positions hypertable, indexes

Revision ID: 0001
Revises:
Create Date: 2026-05-09
"""

from __future__ import annotations

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.execute(
        """
        CREATE TABLE vehicle_positions (
            vehicle_id   TEXT                       NOT NULL,
            line_id      TEXT                       NOT NULL,
            recorded_at  TIMESTAMPTZ                NOT NULL,
            sent_at      TIMESTAMPTZ                NOT NULL,
            received_at  TIMESTAMPTZ                NOT NULL,
            position     geography(Point, 4326)     NOT NULL,
            speed_kmh    REAL                       NOT NULL,
            raw          JSONB                      NOT NULL
        )
        """
    )
    op.execute(
        """
        SELECT create_hypertable(
            'vehicle_positions',
            'recorded_at',
            chunk_time_interval => INTERVAL '1 day'
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX vehicle_positions_dedup_idx "
        "ON vehicle_positions (vehicle_id, recorded_at)"
    )
    op.execute(
        "CREATE INDEX vehicle_positions_line_recorded_idx "
        "ON vehicle_positions (line_id, recorded_at DESC)"
    )
    op.execute(
        "CREATE INDEX vehicle_positions_position_gix ON vehicle_positions USING GIST (position)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS vehicle_positions")
    # Extensions left in place; dropping postgis/timescaledb in a downgrade is
    # disruptive and rarely what an operator wants.
