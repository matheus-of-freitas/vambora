# vambora-backend

API and ingestion workers for Vambora. Hexagonal layout with DDD-lite bounded contexts; see `docs/adrs/0001-hexagonal-architecture.md`.

## Layout

```
src/vambora/
├── domain/              # Pure Python. Zero deps on frameworks.
├── application/         # Use cases (commands + queries).
├── ports/               # Interfaces (typing.Protocol).
└── adapters/
    ├── inbound/         # FastAPI HTTP, async workers.
    └── outbound/        # Persistence, providers, event bus, cache.
shared/                  # Cross-cutting: config, logging, errors, time.
```

The dependency rule: `domain` depends on nothing; `application` depends only on `domain` and `ports`; `adapters` implement `ports` and may depend on third-party libs.

## Run locally

Prereqs: Docker, [`uv`](https://github.com/astral-sh/uv).

```bash
cp .env.example .env
docker compose up -d
uv sync
uv run alembic upgrade head
uv run python -m vambora.main
```

## Quality gates

```bash
uv run ruff format --check
uv run ruff check
uv run mypy src
uv run pytest -m unit
uv run pytest -m integration   # spins up Postgres+Timescale+PostGIS via testcontainers
```

Pre-commit hooks installed via `lefthook install`.

## ADRs

Decisions live in `docs/adrs/`. Every non-trivial architecture choice has an entry.
