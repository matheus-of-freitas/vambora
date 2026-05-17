---
sidebar_position: 1
---

# Ubiquitous language

Terms used consistently across code, docs, conversations, and PR descriptions. If a name conflicts here, this page wins.

## Transit primitives

- **GTFS** — General Transit Feed Specification. Open standard for static transit data (routes, stops, schedules).
- **GTFS-RT** — GTFS Realtime. Protocol Buffers-based extension. Not provided by RJ-SMTR; we use SPPO REST instead.
- **SPPO** — Sistema de Transporte Público por Ônibus. Rio's bus operator data system. Provides REST JSON GPS feed for buses and BRT.
- **BRT** — Bus Rapid Transit. In Rio: TransOeste, TransCarioca, TransOlimpica, TransBrasil.
- **VLT** — Veículo Leve sobre Trilhos. Modern light rail in downtown Rio.
- **MetroRio** — Rio's subway. Privately operated. No public real-time API. Phase 2 synthetic GTFS only.
- **SuperVia** — Rio's commuter rail. Privately operated. No public real-time API. Phase 2 synthetic GTFS only.
- **OTP** — OpenTripPlanner v2. Open-source multi-modal trip planner.

## Data shapes

- **Hypertable** — TimescaleDB's time-partitioned table abstraction. `vehicle_positions` is one, partitioned by `recorded_at` with 1-day chunks.
- **Continuous aggregate** — TimescaleDB's incrementally maintained materialized view.
- **Bundle** — the offline data package downloaded by clients (GTFS plus precomputed aggregates).
- **Headway** — time between consecutive vehicles on the same line.
- **Dwell time** — time a vehicle spends stopped at a stop.
- **Geofence** — virtual perimeter around a location used to trigger alerts.

## Identity and timing

- **Device ID** — anonymous UUID generated on first app launch. Scopes favorites and alert rules before optional Phase 2 login.
- **`recorded_at`** — GPS fix time on the vehicle (SPPO `datahora`). Source-of-truth for trajectory math.
- **`sent_at`** — vehicle→server transmission time (SPPO `datahoraenvio`).
- **`received_at`** — server arrival time (SPPO `datahoraservidor`). **Source-of-truth for "is this vehicle live now."**

## Other

- **FCM** — Firebase Cloud Messaging. Push delivery channel.
