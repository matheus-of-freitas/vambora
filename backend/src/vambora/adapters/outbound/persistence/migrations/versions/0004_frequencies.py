"""frequencies: gtfs_frequencies (trip headway windows)

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-09
"""

from __future__ import annotations

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE gtfs_frequencies (
            trip_id          TEXT NOT NULL,
            start_seconds    INTEGER NOT NULL,
            end_seconds      INTEGER NOT NULL,
            headway_secs     INTEGER NOT NULL,
            feed_version     TEXT NOT NULL,
            PRIMARY KEY (trip_id, start_seconds)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS gtfs_frequencies")
