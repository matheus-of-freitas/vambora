# ADR-0005: OpenTripPlanner v2 for multi-modal routing

- Status: Accepted
- Date: 2026-05-09
- Deciders: @matheusallein

## Context

The MVP must compute multi-modal itineraries (walk + bus + BRT + VLT) with transfers, walking legs, and "guaranteed connections" surfaced in the UI. Building this from scratch is a year of work. We need an off-the-shelf engine that ingests our GTFS feed, accepts an OSM extract for walking, and exposes a queryable HTTP API.

## Decision

Use **OpenTripPlanner v2** (Java) as a separate container, fed daily by our GTFS importer and weekly by a Brazil-region OSM PBF extract from Geofabrik. The backend talks to OTP over HTTP via a single outbound adapter (`adapters/outbound/routing/otp_client.py`, lands in Phase 1). OTP's GraphQL is wrapped behind our REST `POST /trips/plan`.

## Consequences

- **Positive**: production-grade multi-modal routing including transfers, fare-aware paths (later), and accessibility filters with effectively no implementation cost.
- **Positive**: GTFS-RT updates (when available) plug in natively. SPPO's REST feed is mapped to GTFS-RT-shaped `TripUpdate`/`VehiclePosition` messages in Phase 2 if needed.
- **Negative**: separate JVM container. Memory footprint at Rio's network size is moderate (~2 GB resident). Acceptable on Oracle Cloud Free Tier (24 GB shared budget).
- **Negative**: graph builds are slow (minutes); managed via a build-then-swap deploy pattern, not in-process reload.
- **Neutral**: OTP's JSON response shape leaks through the REST API only via our DTO, so we can swap to a different engine later without changing clients.

## Alternatives Considered

- **GraphHopper (Java/CLI)**: strong on car/bike, weaker on transit; requires more glue for multi-modal scheduling.
- **Valhalla**: excellent road routing, transit support is younger; would require self-built schedule integration.
- **Custom routing on Postgres + pgRouting**: rejected; multi-modal scheduling is a research-grade problem and not what this project is for.
- **Google Directions API**: rejected by `plan.md` non-goals (cost, scraping/ToS risk).
