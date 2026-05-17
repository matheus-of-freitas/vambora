-- Vambora SPPO spike — schema bootstrap.
-- Runs once on first container start via /docker-entrypoint-initdb.d.

CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS vehicle_positions (
    vehicle_id   TEXT                       NOT NULL,
    line_id      TEXT                       NOT NULL,
    recorded_at  TIMESTAMPTZ                NOT NULL,  -- datahora (GPS fix time)
    sent_at      TIMESTAMPTZ                NOT NULL,  -- datahoraenvio
    received_at  TIMESTAMPTZ                NOT NULL,  -- datahoraservidor
    position     geography(Point, 4326)     NOT NULL,
    speed_kmh    REAL                       NOT NULL,
    raw          JSONB                      NOT NULL
);

-- Hypertable partitioned by recorded_at, 1-day chunks (matches plan.md).
SELECT create_hypertable(
    'vehicle_positions',
    'recorded_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Dedup: the SPPO feed re-emits old positions inside fresh windows. We rely on
-- this index for upserts (ON CONFLICT DO NOTHING) in the poller.
CREATE UNIQUE INDEX IF NOT EXISTS vehicle_positions_dedup_idx
    ON vehicle_positions (vehicle_id, recorded_at);

CREATE INDEX IF NOT EXISTS vehicle_positions_line_recorded_idx
    ON vehicle_positions (line_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS vehicle_positions_position_gix
    ON vehicle_positions USING GIST (position);
