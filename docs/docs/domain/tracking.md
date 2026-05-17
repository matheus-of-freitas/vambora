---
sidebar_position: 2
---

# Tracking context

The `tracking` bounded context owns "where are the vehicles right now."

## Aggregate

- **`VehiclePosition`** — a single GPS observation. Immutable. Validated at construction (lat/lon range, timezone-aware timestamps, non-negative speed).

The implementation is in `vambora-backend/src/vambora/domain/tracking/vehicle_position.py`.

## Ports

- **`VehicleTrackingProvider.fetch(since, until)`** — pulls positions whose server-arrival time is in the window. Implemented by the SPPO adapter; the same interface will accept a future GTFS-RT adapter when one becomes available.
- **`VehiclePositionRepository`** — persistence with three operations:
  - `upsert_many(positions)` — bulk insert with dedup on `(vehicle_id, recorded_at)`.
  - `latest_per_vehicle(line_id?, fresh_seconds, limit)` — current state for the map.
  - `history_for(vehicle_id, limit)` — recent trajectory for one vehicle.

## Use cases

- **`IngestVehiclePositions`** (command) — fetch a window from the provider, persist via the repository, return a count summary.
- **`GetLiveVehicles`** (query) — DISTINCT ON per vehicle within a freshness window, optionally filtered by line.
- **`GetVehicleHistory`** (query) — trajectory for one vehicle.

## What's deliberately not here

- No notion of "trip" (that's `catalog`).
- No ETA computation (that's `predictions`).
- No event publishing yet — when the alerts worker lands, `IngestVehiclePositions` will publish `vehicle.position.received` to the in-process bus and (later) Redis pub/sub.
