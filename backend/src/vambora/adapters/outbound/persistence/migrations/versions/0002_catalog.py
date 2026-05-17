"""catalog: gtfs_agencies, gtfs_routes, gtfs_stops, gtfs_imports

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-09
"""

from __future__ import annotations

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE gtfs_agencies (
            agency_id     TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            url           TEXT NOT NULL,
            timezone      TEXT NOT NULL,
            lang          TEXT,
            feed_version  TEXT NOT NULL
        )
        """
    )

    op.execute(
        """
        CREATE TABLE gtfs_routes (
            route_id      TEXT PRIMARY KEY,
            agency_id     TEXT NOT NULL,
            short_name    TEXT NOT NULL,
            long_name     TEXT NOT NULL,
            route_type    INTEGER NOT NULL,
            color         TEXT,
            text_color    TEXT,
            feed_version  TEXT NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX gtfs_routes_short_name_idx ON gtfs_routes (short_name)")
    op.execute("CREATE INDEX gtfs_routes_agency_idx ON gtfs_routes (agency_id)")

    op.execute(
        """
        CREATE TABLE gtfs_stops (
            stop_id              TEXT PRIMARY KEY,
            code                 TEXT,
            name                 TEXT NOT NULL,
            position             geography(Point, 4326) NOT NULL,
            parent_station       TEXT,
            wheelchair_boarding  SMALLINT,
            feed_version         TEXT NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX gtfs_stops_position_gix ON gtfs_stops USING GIST (position)")
    # Trigram name search index lands when /stops/search is added; keeping it out
    # for now avoids the pg_trgm extension dependency until we need it.

    op.execute(
        """
        CREATE TABLE gtfs_imports (
            feed_version  TEXT PRIMARY KEY,
            imported_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
            source_url    TEXT NOT NULL,
            agency_count  INTEGER NOT NULL,
            route_count   INTEGER NOT NULL,
            stop_count    INTEGER NOT NULL
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS gtfs_imports")
    op.execute("DROP TABLE IF EXISTS gtfs_stops")
    op.execute("DROP TABLE IF EXISTS gtfs_routes")
    op.execute("DROP TABLE IF EXISTS gtfs_agencies")
