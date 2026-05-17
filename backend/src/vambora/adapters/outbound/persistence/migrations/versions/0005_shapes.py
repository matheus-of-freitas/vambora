"""shapes: gtfs_shapes (per-route polylines)

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-09
"""

from __future__ import annotations

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE gtfs_shapes (
            shape_id      TEXT PRIMARY KEY,
            geom          geography(LineString, 4326) NOT NULL,
            feed_version  TEXT NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX gtfs_shapes_gix ON gtfs_shapes USING GIST (geom)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS gtfs_shapes")
