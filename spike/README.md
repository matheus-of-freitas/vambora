# Vambora — SPPO Spike

Throwaway spike validating the backend stack against the live SPPO real-time bus feed for Rio de Janeiro. See `../plan.md` for the full project plan; see `/Users/matheus/.claude/plans/let-s-work-on-the-snoopy-eagle.md` for this spike's design.

**This is not the seed of `vambora-backend`.** No hexagonal layering, no Alembic, no tests beyond a fixture sanity. The point is to learn fast.

## What this validates

- Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) + asyncpg against the chosen DB.
- TimescaleDB hypertable + PostGIS `geography(Point, 4326)` from `timescale/timescaledb-ha:pg16`.
- Real SPPO payload shape, cadence, and quirks.
- End-to-end ingestion → `GET /vehicles` query path.

## Run

Prereqs: Docker, [`uv`](https://github.com/astral-sh/uv).

```bash
cd spike
cp .env.example .env

docker compose up -d
docker compose ps                                  # wait for "healthy"

uv sync
uv run python -m src.main
```

In another shell:

```bash
curl -s localhost:8000/health
curl -s 'localhost:8000/vehicles' | jq 'length'
curl -s 'localhost:8000/vehicles?line_id=485' | jq
curl -s localhost:8000/vehicles/B11622 | jq
```

## SPPO API — confirmed shape (2026-05-08)

- Endpoint: `https://dados.mobilidade.rio/gps/sppo`
- Date range filter via query params: `dataInicial`, `dataFinal`. Format **must be ISO** `YYYY-MM-DD HH:MM:SS` (BRT). `DD-MM-YYYY` returns `[]`.
- Without filters: ~90MB dump (unusable). With a 30s `dataInicial`/`dataFinal` window: ~750KB, ~4000 records, ~3000 unique vehicles, ~360 lines.
- Filter applies to `datahoraenvio` (server-side arrival), **not** `datahora` (GPS fix time). Some `datahora` values can be hours stale within a "fresh" window.
- Content-Type header lies: `text/html`, body is JSON.
- Per record:
  - `ordem` — vehicle ID (e.g. `B11622`)
  - `linha` — line ID, mixed format (`007`, `485`, `SV669`, `LECD147`)
  - `latitude`, `longitude` — strings with comma decimal (`"-22,89623"`)
  - `datahora` — ms-epoch string, GPS fix time
  - `datahoraenvio` — ms-epoch string, vehicle→server send time
  - `datahoraservidor` — ms-epoch string, server arrival
  - `velocidade` — km/h, integer string
  - **No** heading field (drop from schema)

## Findings (2026-05-09, first short live run)

End-to-end is green. Stack validated. Notes for `../plan.md`:

- **Throughput per tick** (45s window, 30s cadence): ~1.3k–1.6k records, ~1.1k–1.2k unique vehicles, ~310–325 unique lines. Plain JSON over httpx, ~750KB per fetch, fetch latency 1.5–2.4s.
- **Dedup observed**: tick #2 fetched 1364 records, 1336 net new rows persisted → ~2% intra-window overlap caught by `(vehicle_id, recorded_at)` UNIQUE + `ON CONFLICT DO NOTHING`. The same `ordem` can appear with different `datahora` values inside one fetch (multiple GPS fixes), so the unique key has to include `recorded_at`, not just `vehicle_id`.
- **Geographic sanity**: positions land inside Rio's bounding box (~-22.87, -43.28 sample). PostGIS `geography(Point, 4326)` with `ST_MakePoint(lon, lat)` is correct ordering — easy to flip.
- **Speed distribution**: ~47% of records at 0 km/h (stopped buses). Long tail to 90–100 km/h is BRT/expressway, not anomalies. Speed unit is km/h, integer-valued in source.
- **Line ID format is heterogeneous**: numeric (`007`, `292`, `485`), prefixed (`SV669`, `LECD147`), four-digit (`2345`). When we wire GTFS later we'll need a normalization layer between feed `route_short_name` and SPPO `linha`. Not all SPPO lines exist in GTFS and vice versa.
- **Three timestamps, three different uses**:
  - `datahora` (GPS fix) — what we store as `recorded_at`. Use this for trajectory math and ETA extrapolation.
  - `datahoraenvio` (vehicle→server) — `sent_at`. `datahoraservidor` − `datahoraenvio` is upstream queue lag.
  - `datahoraservidor` — `received_at`. The SPPO date-range filter operates on this column, **not** on `datahora`. So a 30s "fresh" window can include GPS fixes that are hours old.
- **Plan delta**: the "Realtime vs scheduled badge" feature in `plan.md` should compare against `received_at`, not `recorded_at`, when deciding "is this bus actually live." Otherwise a vehicle whose `datahora` was 2 hours ago but whose data just arrived will be marked stale incorrectly.
- **API response Content-Type**: `text/html; charset=utf-8` even though body is JSON. `httpx.Response.json()` handles it because it doesn't require the header to match. Anything stricter (e.g. middleware that whitelists by content-type) will need a workaround.
- **Hypertable**: one chunk per day created automatically (`_hyper_1_1_chunk` covering 2026-05-09 00:00 → 2026-05-10 00:00). Plan-mandated 1-day chunk interval is set; retention policy not configured (deferred to Phase 0).

## Open questions for Phase 0

- The 90MB unfiltered response suggests SPPO retains many days of history server-side. Worth investigating whether a longer historical scrape is allowed for backfill before we start the live poller in production.
- `dataInicial`/`dataFinal` returns `[]` for windows whose `datahoraenvio` falls outside the server's retained buffer — what's that retention? Affects whether a lagging poller can catch up after an outage.
- No GTFS-RT feed is published; this REST poll is the only realtime channel. Plan's choice of REST polling over Protobuf is validated.

## Stop & clean up

```bash
docker compose down -v   # -v wipes the volume (the spike is throwaway)
```
