# ADR-0001: Hexagonal architecture with DDD-lite, pragmatic CQRS, event-driven ingestion

- Status: Accepted
- Date: 2026-05-09
- Deciders: @matheusallein

## Context

Vambora's backend ingests a high-frequency upstream feed (SPPO, ~1.5k records every 30 s, validated 2026-05-09), serves a low-latency read API, schedules background work (alerts, snapshot bundles), and will later integrate a routing engine and ML predictions. Read and write paths have very different shapes — writes are continuous bulk inserts; reads are spatial+temporal queries with optional filters. The system must remain testable, swap-friendly (SPPO will be joined or replaced by other feeds; tile and notification providers will change), and approachable for solo development.

A monolithic layered architecture mixed with framework-coupled domain models would be quick now and painful by Phase 2. A purist DDD with full aggregate modeling and inter-context domain events would over-engineer a single-developer project.

## Decision

Adopt **Hexagonal (Ports & Adapters)** as the primary structure with three pragmatic refinements:

1. **DDD-lite**: bounded contexts (`tracking`, `catalog`, `routing`, `predictions`, `alerts`, `user`) with a ubiquitous language documented in the codebase, but no aggregate roots and no inter-context domain events. Cross-context coordination happens at the application layer.
2. **Pragmatic CQRS**: separate `application/commands/` and `application/queries/` modules sharing a single database. The shared store keeps deployment simple; the code split lets writes and reads optimize independently (bulk upsert vs. spatial DISTINCT ON).
3. **Event-driven ingestion**: the ingestion command emits a single in-process event (`vehicle.position.received`) consumed by the alerts worker and (later) the cache update path. Implementation starts as an in-process bus; it migrates to Redis pub/sub when the alerts worker moves to a separate process. No Kafka.

Dependency rule: `domain` → nothing; `application` → `domain` + `ports`; `adapters` → ports + third-party libs. Enforced by import-linter in CI (later phase).

## Consequences

- **Positive**: domain code is pure, fast to test, and survives library churn. Swapping SPPO for any other GPS feed touches only one adapter. The use case layer is the readable index of behavior.
- **Positive**: read/write split per file makes hotpaths easy to spot. Bulk insert SQL lives next to the dedup contract, not buried in an ORM session manager.
- **Negative**: more files for the same feature compared to a flat layout. Mitigated by keeping the per-context tree shallow.
- **Neutral**: the in-process bus is intentionally simple; revisit (and write a follow-up ADR) when the alerts worker moves out of the API process.

## Alternatives Considered

- **Layered MVC over an ORM**: rejected; binds the domain to SQLAlchemy and to FastAPI request/response shapes, making swap and test cost grow with the codebase.
- **Full DDD with aggregates and a domain-event bus**: rejected; cost exceeds value for a single-developer codebase. Keep the option open if the team grows.
- **Flat scripts (à la the spike)**: rejected for the durable backend. Validated for throwaway exploration only — see `spike/`.
