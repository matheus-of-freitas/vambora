# ADR-0002: Python 3.12 + FastAPI for the backend

- Status: Accepted
- Date: 2026-05-09
- Deciders: @matheusallein

## Context

The backend must ingest a JSON feed every 30 s, expose a REST API with sensible OpenAPI docs, run async I/O, and integrate with PostGIS, TimescaleDB, Alembic, ML libraries (Phase 2), and OpenTripPlanner via HTTP. A solo developer needs a stack with strong typing, a vibrant geospatial/ML ecosystem, and a low cognitive overhead for routine work.

## Decision

Use **Python 3.12+** as the language and **FastAPI** as the HTTP framework, with `uv` as the package manager, `ruff` as the formatter and linter, `mypy --strict` as the type checker, and `pydantic v2` for validation.

Async I/O is the default for handlers and workers. CPU-bound work (rare in this codebase) may be sync, justified inline.

## Consequences

- **Positive**: world-class geospatial and ML libraries (GeoAlchemy2, Shapely, scikit-learn, XGBoost) reduce future-Phase risk.
- **Positive**: FastAPI's auto-generated OpenAPI feeds the web client and the docs site without hand-maintenance.
- **Positive**: `uv` makes dependency resolution and Python version management fast and reproducible.
- **Negative**: GIL constraints mean CPU-bound paths need process pools or native extensions. Acceptable: ingestion is I/O-bound; routing is delegated to OTP (separate JVM); ML batch jobs run offline.
- **Negative**: async + ORM has rough edges (greenlet, transaction scoping). Mitigated by Core-level SQL in hot paths (see `repositories/vehicle_positions.py`).

## Alternatives Considered

- **Go (chi/echo + sqlc)**: rejected; weaker geospatial/ML library story, more code to write for the same surface, no automatic OpenAPI from handler types.
- **Node.js (Fastify + Prisma)**: rejected; slower numeric work for Phase 2 ML, and our async story is no better than Python's.
- **Rust (axum + sqlx)**: rejected; excellent runtime, but learning + iteration cost is a poor trade for a solo MVP. Reconsider only if a specific perf wall is hit.
