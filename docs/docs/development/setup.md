---
sidebar_position: 1
---

# Local setup

You need: Docker, [`uv`](https://github.com/astral-sh/uv), Node 20+, [`pnpm`](https://pnpm.io/).

## Backend

```bash
cd backend
cp .env.example .env
docker compose up -d                  # postgres+timescale+postgis, redis
uv sync
uv run alembic upgrade head
uv run python -m vambora.main         # API on :8000 (or HTTP_PORT in .env), poller in same process
```

Verify:

```bash
curl -s localhost:8000/health
curl -s 'localhost:8000/vehicles?fresh_seconds=120' | jq 'length'
```

## Web

```bash
cd web
cp .env.example .env.local
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000). The map should show ~1k yellow dots over Rio after the first backend tick (~30 s). If the backend is on a non-default port, set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8002` (or whatever) in `.env.local`.

## Quality gates

Each repo runs the same shape locally as in CI:

| Gate | Backend | Web |
|---|---|---|
| Format | `uv run ruff format --check` | `pnpm lint` (Biome) |
| Lint | `uv run ruff check` | `pnpm lint` |
| Types | `uv run mypy src` (strict) | `pnpm typecheck` (tsc --noEmit) |
| Unit tests | `uv run pytest -m unit` | `pnpm test` (Vitest) |
| Integration | `uv run pytest -m integration` (testcontainers) | — |
| E2E | `uv run pytest -m e2e` | `pnpm e2e` (Playwright) |

## Tearing down

```bash
cd backend && docker compose down -v   # -v wipes the volume
```
