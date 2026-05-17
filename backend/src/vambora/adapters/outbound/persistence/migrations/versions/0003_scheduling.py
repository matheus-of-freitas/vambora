"""scheduling: gtfs_trips, gtfs_stop_times, gtfs_calendar, gtfs_calendar_dates

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-09
"""

from __future__ import annotations

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE gtfs_trips (
            trip_id        TEXT PRIMARY KEY,
            route_id       TEXT NOT NULL,
            service_id     TEXT NOT NULL,
            headsign       TEXT,
            direction_id   SMALLINT,
            feed_version   TEXT NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX gtfs_trips_route_idx ON gtfs_trips (route_id)")
    op.execute("CREATE INDEX gtfs_trips_service_idx ON gtfs_trips (service_id)")

    # arrival/departure stored as INTEGER seconds since midnight, which lets us
    # represent past-midnight values (e.g. "25:30:00" → 91800) per GTFS spec.
    op.execute(
        """
        CREATE TABLE gtfs_stop_times (
            trip_id            TEXT NOT NULL,
            stop_sequence      INTEGER NOT NULL,
            stop_id            TEXT NOT NULL,
            arrival_seconds    INTEGER NOT NULL,
            departure_seconds  INTEGER NOT NULL,
            feed_version       TEXT NOT NULL,
            PRIMARY KEY (trip_id, stop_sequence)
        )
        """
    )
    op.execute(
        "CREATE INDEX gtfs_stop_times_stop_arrival_idx "
        "ON gtfs_stop_times (stop_id, arrival_seconds)"
    )

    op.execute(
        """
        CREATE TABLE gtfs_calendar (
            service_id    TEXT PRIMARY KEY,
            monday        BOOLEAN NOT NULL,
            tuesday       BOOLEAN NOT NULL,
            wednesday     BOOLEAN NOT NULL,
            thursday      BOOLEAN NOT NULL,
            friday        BOOLEAN NOT NULL,
            saturday      BOOLEAN NOT NULL,
            sunday        BOOLEAN NOT NULL,
            start_date    DATE NOT NULL,
            end_date      DATE NOT NULL,
            feed_version  TEXT NOT NULL
        )
        """
    )

    op.execute(
        """
        CREATE TABLE gtfs_calendar_dates (
            service_id      TEXT NOT NULL,
            calendar_date   DATE NOT NULL,
            exception_type  SMALLINT NOT NULL,
            feed_version    TEXT NOT NULL,
            PRIMARY KEY (service_id, calendar_date)
        )
        """
    )
    op.execute("CREATE INDEX gtfs_calendar_dates_date_idx ON gtfs_calendar_dates (calendar_date)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS gtfs_calendar_dates")
    op.execute("DROP TABLE IF EXISTS gtfs_calendar")
    op.execute("DROP TABLE IF EXISTS gtfs_stop_times")
    op.execute("DROP TABLE IF EXISTS gtfs_trips")
