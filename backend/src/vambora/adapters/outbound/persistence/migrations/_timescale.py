"""Decide whether migrations should emit TimescaleDB-specific DDL.

Local dev runs on ``timescale/timescaledb-ha`` (hypertables, continuous
aggregates, retention policies). The serverless deployment runs on plain
Postgres + PostGIS (Supabase free tier), where that DDL doesn't exist — there
the same migrations create ordinary tables and CompactTrackingData handles
rollup and retention instead.

The choice is made per-connection at migration time so one migration set works
on both, and the alembic round-trip test can exercise each branch.
"""

from __future__ import annotations

import os

from sqlalchemy import text
from sqlalchemy.engine import Connection


def timescale_enabled(connection: Connection) -> bool:
    """True when this database should use TimescaleDB DDL.

    Set ``VAMBORA_DISABLE_TIMESCALE=1`` to force the plain-Postgres branch even
    where the extension is installable (used by the plain-Postgres test against
    a postgis-only container, and as an escape hatch). Otherwise we probe
    ``pg_available_extensions`` so a fresh Supabase database transparently takes
    the plain branch.
    """
    if os.environ.get("VAMBORA_DISABLE_TIMESCALE") == "1":
        return False
    row = connection.execute(
        text("SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb'")
    ).first()
    return row is not None
