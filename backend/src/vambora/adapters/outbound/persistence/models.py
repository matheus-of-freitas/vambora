from __future__ import annotations

from geoalchemy2 import Geography
from sqlalchemy import Column, Float, Index, MetaData, String, Table
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP

metadata = MetaData()

vehicle_positions = Table(
    "vehicle_positions",
    metadata,
    Column("vehicle_id", String, nullable=False),
    Column("line_id", String, nullable=False),
    Column("recorded_at", TIMESTAMP(timezone=True), nullable=False),
    Column("sent_at", TIMESTAMP(timezone=True), nullable=False),
    Column("received_at", TIMESTAMP(timezone=True), nullable=False),
    Column("position", Geography(geometry_type="POINT", srid=4326), nullable=False),
    Column("speed_kmh", Float, nullable=False),
    Column("raw", JSONB, nullable=False),
    Index("vehicle_positions_dedup_idx", "vehicle_id", "recorded_at", unique=True),
    Index("vehicle_positions_line_recorded_idx", "line_id", "recorded_at"),
)
