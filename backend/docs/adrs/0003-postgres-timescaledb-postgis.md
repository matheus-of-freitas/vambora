# ADR-0003: PostgreSQL 16 + TimescaleDB + PostGIS as the single store

- Status: Accepted
- Date: 2026-05-09
- Deciders: @matheusallein

## Context

Vambora has three storage shapes: time-series ingestion (`vehicle_positions`, ~1.5k rows / 30 s sustained), GTFS catalog (routes, stops, schedules — versioned), and small relational state (alert rules, favorites). Spike measurements on 2026-05-09 confirm sustained insert + dedup + spatial query patterns hit a single table hot. Operating multiple specialized stores adds complexity disproportionate to the team size.

The `timescale/timescaledb-ha:pg16` image bundles PostGIS, validated end-to-end during the spike (extensions present, hypertable created, GiST and unique indexes functioning, ON CONFLICT dedup confirmed).

## Decision

Use **PostgreSQL 16** as the only OLTP store, with **TimescaleDB** for the `vehicle_positions` hypertable and continuous aggregates, and **PostGIS** for all spatial columns (`geography(Point, 4326)` for points, GiST indexes everywhere they help). Image: `timescale/timescaledb-ha:pg16`.

Retention policy: keep raw `vehicle_positions` for 14 days, downsample to 5-minute aggregates after that (configured in a later migration once the policy stabilizes).

`vehicle_positions` uses `UNIQUE (vehicle_id, recorded_at)` + `ON CONFLICT DO NOTHING` for dedup; SPPO re-emits the same fix across overlapping fetch windows (~2 % intra-window overlap measured during the spike).

## Consequences

- **Positive**: one backup story, one connection pool, one query language, one operational profile. Joins between time-series and catalog stay native SQL.
- **Positive**: TimescaleDB compression and continuous aggregates handle the only known scale-out concern (90-day history for ML features) inside the same engine.
- **Negative**: PostGIS query plans need attention for spatial filters at scale. Mitigated by always-indexed geography columns and by avoiding denormalized geo joins in hot paths.
- **Negative**: TimescaleDB Cloud's licensing is restrictive; we host ourselves on Oracle Cloud Free Tier. Acceptable for a portfolio project.

## Alternatives Considered

- **ClickHouse for positions, Postgres for catalog**: rejected for solo project; doubles operational surface, splits transactions, and slows joins.
- **InfluxDB**: rejected; weaker ad-hoc query story, weaker spatial story, weaker SQL ergonomics.
- **Vanilla Postgres (no Timescale)**: rejected; raw partitioning works but Timescale's chunk policies and continuous aggregates are exactly the features we need at zero extra ops cost.
