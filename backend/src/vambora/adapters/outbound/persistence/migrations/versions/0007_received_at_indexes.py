"""vehicle_positions: indexes on received_at to support liveness queries

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-15

`latest_per_vehicle` now gates liveness on ``received_at`` (plan.md decision
#25). Without these the query sequential-scans a multi-million-row hypertable
(~10 s observed at 28M rows). Mirror the existing ``recorded_at`` indexes.
"""

from __future__ import annotations

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX vehicle_positions_received_at_idx ON vehicle_positions (received_at DESC)"
    )
    op.execute(
        "CREATE INDEX vehicle_positions_line_received_idx "
        "ON vehicle_positions (line_id, received_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS vehicle_positions_line_received_idx")
    op.execute("DROP INDEX IF EXISTS vehicle_positions_received_at_idx")
