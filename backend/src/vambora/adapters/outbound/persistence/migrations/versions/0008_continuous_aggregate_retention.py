"""vehicle_positions: hourly continuous aggregate + 14-day raw retention

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-15

plan.md ADR-0017: keep raw vehicle_positions for 14 days, downsample to
aggregates after. The raw hypertable grows unbounded (~28M rows / week);
this caps it and pre-computes per-line hourly stats.

TimescaleDB continuous-aggregate DDL cannot run inside a transaction, so we
use Alembic's autocommit_block.
"""

from __future__ import annotations

from alembic import op

from vambora.adapters.outbound.persistence.migrations._timescale import timescale_enabled

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

CAGG = "vehicle_positions_hourly"


def upgrade() -> None:
    if not timescale_enabled(op.get_bind()):
        _upgrade_plain()
        return
    with op.get_context().autocommit_block():
        op.execute(
            f"""
            CREATE MATERIALIZED VIEW {CAGG}
            WITH (timescaledb.continuous) AS
            SELECT
                time_bucket('1 hour', recorded_at) AS bucket,
                line_id,
                count(*)                    AS position_count,
                count(DISTINCT vehicle_id)  AS vehicle_count,
                avg(speed_kmh)              AS avg_speed_kmh,
                max(speed_kmh)              AS max_speed_kmh
            FROM vehicle_positions
            GROUP BY bucket, line_id
            WITH NO DATA
            """
        )
        # Refresh the trailing window each hour; leave the last hour open so
        # in-flight buckets aren't prematurely frozen.
        op.execute(
            f"""
            SELECT add_continuous_aggregate_policy(
                '{CAGG}',
                start_offset => INTERVAL '3 hours',
                end_offset   => INTERVAL '1 hour',
                schedule_interval => INTERVAL '1 hour',
                if_not_exists => true
            )
            """
        )
        # Drop raw chunks older than 14 days. The materialized aggregate is
        # independent and survives — its already-computed buckets remain.
        op.execute(
            """
            SELECT add_retention_policy(
                'vehicle_positions',
                INTERVAL '14 days',
                if_not_exists => true
            )
            """
        )


def _upgrade_plain() -> None:
    # Plain Postgres has no continuous aggregate. Create an ordinary table with
    # the identical shape so _HOURLY_STATS_SQL is unchanged; CompactTrackingData
    # (run from the poller Lambda) populates it and enforces raw retention,
    # standing in for the continuous-aggregate and retention policies above.
    op.execute(
        f"""
        CREATE TABLE {CAGG} (
            bucket          TIMESTAMPTZ  NOT NULL,
            line_id         TEXT         NOT NULL,
            position_count  BIGINT       NOT NULL,
            vehicle_count   BIGINT       NOT NULL,
            avg_speed_kmh   DOUBLE PRECISION,
            max_speed_kmh   DOUBLE PRECISION,
            PRIMARY KEY (bucket, line_id)
        )
        """
    )


def downgrade() -> None:
    if not timescale_enabled(op.get_bind()):
        op.execute(f"DROP TABLE IF EXISTS {CAGG}")
        return
    with op.get_context().autocommit_block():
        op.execute("SELECT remove_retention_policy('vehicle_positions', if_exists => true)")
        # Dropping the materialized view also removes its refresh policy.
        op.execute(f"DROP MATERIALIZED VIEW IF EXISTS {CAGG}")
