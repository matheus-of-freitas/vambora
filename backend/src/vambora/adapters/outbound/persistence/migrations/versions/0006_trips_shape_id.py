"""trips: add shape_id column for joining to gtfs_shapes

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-09
"""

from __future__ import annotations

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE gtfs_trips ADD COLUMN shape_id TEXT")
    op.execute("CREATE INDEX gtfs_trips_shape_idx ON gtfs_trips (shape_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS gtfs_trips_shape_idx")
    op.execute("ALTER TABLE gtfs_trips DROP COLUMN IF EXISTS shape_id")
