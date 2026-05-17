# Architecture Decision Records

Each non-trivial architecture choice for `vambora-backend` lives here as a numbered Markdown file. Format follows `plan.md` §"Architecture Decision Records (ADRs)".

| # | Status | Title |
|---|---|---|
| [0001](0001-hexagonal-architecture.md) | Accepted | Hexagonal architecture with DDD-lite, pragmatic CQRS, event-driven ingestion |
| [0002](0002-python-fastapi.md) | Accepted | Python 3.12 + FastAPI for the backend |
| [0003](0003-postgres-timescaledb-postgis.md) | Accepted | PostgreSQL 16 + TimescaleDB + PostGIS as the single store |
| [0004](0004-redis-cache-pubsub.md) | Accepted | Redis for cache and pub/sub |
| [0005](0005-opentripplanner-routing.md) | Accepted | OpenTripPlanner v2 for multi-modal routing |

## When to write a new ADR

Write one when:

- Choosing among materially different libraries, languages, services, or patterns.
- Reversing or superseding a prior decision.
- Introducing a constraint that future contributors will silently bump into (timezone, retention, dedup strategy, etc.).

Don't write one for trivial dependency bumps, formatting choices, or anything already settled in `plan.md`.
