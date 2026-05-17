"""alerts: alert_rules

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-16

Device-scoped geofence alert rules (plan.md decision #4, bounded context
``alerts``). ``last_triggered_at`` backs the cooldown so a rule doesn't
re-fire every evaluation cycle while a bus stays within threshold.
"""

from __future__ import annotations

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE alert_rules (
            id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            device_id          TEXT NOT NULL,
            line_short_name    TEXT NOT NULL,
            stop_id            TEXT NOT NULL,
            threshold_minutes  INTEGER NOT NULL,
            created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_triggered_at  TIMESTAMPTZ
        )
        """
    )
    op.execute("CREATE INDEX alert_rules_device_idx ON alert_rules (device_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS alert_rules")
