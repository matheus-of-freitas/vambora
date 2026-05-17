# Vambora

> Real-time tracking, multi-modal routing, and proximity alerts for Rio de Janeiro public transit. Open-source, near-zero hosting cost.

Vambora ingests Rio's live bus feed (SPPO / RJ-SMTR) and the static GTFS
catalog, and serves a fast PWA: buses moving on a map, line/stop pages,
naive real-time ETAs, a trip planner, and geofence alerts — with a full
offline mode.

## Status

- **Web + docs**: deployed to Cloudflare Pages.
- **Backend**: runs locally (Docker Compose); a public always-on host is
  deferred (free-tier ARM VM capacity), so the hosted web shell has no live
  data until a backend is provisioned. Everything works end-to-end locally.
- Feature-complete for the credential-free MVP scope; unit + integration
  tested; CI runs on every push.

## Monorepo layout

| Path | What |
|---|---|
| `backend/` | API + ingestion/alert workers — Python 3.12, FastAPI, SQLAlchemy (async), TimescaleDB + PostGIS, Alembic. Hexagonal / DDD-lite. |
| `web/` | Next.js 15 PWA — React 19, MapLibre GL, TanStack Query, next-intl (pt-BR), shadcn-style design system. |
| `docs/` | Docusaurus 3 site — architecture, ADRs, domain language, design tokens, data-source notes. |
| `spike/` | Throwaway SPPO-feed spike (findings folded into the backend). |
| `.github/workflows/` | Path-filtered CI: backend (ruff, mypy, unit + testcontainers integration, image build), web (lint, typecheck, test, build), docs (build). |

## Features

- **Live tracking** — SPPO poller, TimescaleDB hypertable, liveness gated on
  server-arrival time; map of current vehicles per line.
- **Catalog** — GTFS lines/stops/route shapes; frequency-expanded scheduled
  arrivals.
- **Naive ETAs** — PostGIS linear-extrapolation predictions from the latest
  live GPS along the route geometry; realtime-vs-scheduled badge.
- **Trip planning** — OpenTripPlanner v2; itineraries with derived
  connection-reliability hints (Rio's GTFS has no `transfers.txt`).
- **Alerts** — device-scoped geofence rules, server-side evaluation worker
  (push delivery is credential-gated and stubbed).
- **Offline** — downloadable GTFS + typical-headway bundle; the web degrades
  gracefully to it when the network is unavailable. Installable PWA.
- **Typed API** — web API types generated from the backend OpenAPI schema.

## Quickstart (local)

Everything runs locally with no cloud accounts. Per-component setup:

- Backend: [`backend/README.md`](backend/README.md) — `docker compose up -d`
  (Postgres+TimescaleDB+PostGIS, Redis, OpenTripPlanner) + `uv` + Alembic.
- Web: [`web/README.md`](web/README.md) — `pnpm install && pnpm dev`.
- Docs site: [`docs/README.md`](docs/README.md) — `pnpm install && pnpm start`.

## Tests

- Backend: `cd backend && uv run pytest -m unit` and (Docker required)
  `uv run pytest -m integration` (real Postgres+TimescaleDB+PostGIS via
  testcontainers).
- Web: `cd web && pnpm test` (Vitest) and `pnpm e2e` (Playwright; needs the
  backend running).

## License

MIT — see [`LICENSE`](LICENSE).
