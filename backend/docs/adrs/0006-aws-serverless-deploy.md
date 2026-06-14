# ADR-0006: AWS serverless deployment (Lambda + managed Postgres)

- Status: Accepted
- Date: 2026-06-14
- Deciders: @matheusallein
- Supersedes the hosting half of ADR-0011 (Oracle Cloud + Coolify); narrows the
  production scope of ADR-0003 (TimescaleDB), ADR-0004 (Redis), and ADR-0005
  (OpenTripPlanner) — see Consequences.

## Context

The original plan (decision #15 / ADR-0011) hosted the whole stack — API,
ingestion worker, Postgres+TimescaleDB+PostGIS, Redis, OpenTripPlanner — on a
single Oracle Cloud Always-Free A1 VM via Coolify, for ~$0/month. Oracle A1
capacity (`Out of capacity for VM.Standard.A1.Flex`) never freed, blocking the
public demo for weeks.

The user has an existing AWS account but a hard budget: even ~$15/mo (~R$100) is
too much, so a persistent VM (no AWS free-tier compute fits this stack) was out.
The requirement: get the backend publicly reachable for as close to $0 as
possible, ideally on AWS.

## Decision

Deploy the backend **serverlessly**:

- **API**: FastAPI on **AWS Lambda** (arm64) behind a **Lambda function URL**
  (no API Gateway), adapted with **Mangum**. New inbound adapter
  `adapters/inbound/aws/api_handler.py`.
- **Ingestion**: a **scheduled Lambda** (EventBridge Scheduler, `rate(1 minute)`)
  that does one SPPO poll + alert evaluation + data compaction per invocation.
  New adapter `adapters/inbound/aws/poller_handler.py`. One poll per invocation
  (not two-with-sleep) keeps it inside the Lambda free tier; `SPPO_WINDOW_SECONDS`
  widens to 90 so the 60 s cadence misses no fixes.
- **Database**: managed **Postgres + PostGIS** (Supabase free tier, São Paulo),
  reached through the IPv4 **session pooler**. No TimescaleDB.
- **Packaging/IaC**: zip-packaged Lambdas (deps ≈ 70 MB ≪ 250 MB limit, so no
  ECR) via **AWS SAM** (`backend/template.yaml`), deployed by GitHub Actions
  using an **OIDC role** (no static keys).
- **Region**: `sa-east-1` (free tier is region-agnostic; São Paulo is ~10 ms
  from Rio and colocated with the database).

Hosting choices are kept out of the domain/application layers: the two handlers
are thin inbound adapters that build the same `Container` as every other
entrypoint.

## Consequences

- **Positive**: ~$0/month within AWS + Cloudflare free tiers; no server to
  patch; deploys are a push to `main`.
- **Positive**: the hexagonal boundary paid off — production needs only new
  adapters plus config flags, no domain/application changes.
- **Negative — TimescaleDB (ADR-0003) not in production.** The free Postgres has
  PostGIS but no Timescale. Migrations detect this per-connection
  (`migrations/_timescale.py`) and create plain tables; `CompactTrackingData`
  (run from the poller) does the hourly rollup + raw retention that the
  continuous-aggregate and retention policies do locally. The read path is
  unchanged (the stats query reads the same relation name).
- **Negative — Redis (ADR-0004) dropped in production.** It was config-only
  already (the event bus is in-process); a Lambda can't share an in-process
  queue anyway. `REDIS_URL` is now optional.
- **Negative — routing (ADR-0005) deferred in production.** OTP is memory-hungry
  and has no serverless home, so `ROUTING_ENABLED=false` makes `POST /trips/plan`
  return 503. OTP stays a local-dev service.
- **Negative — smaller history.** To fit a 500 MB database the raw payload is
  dropped (`STORE_RAW_PAYLOAD=false`) and raw retention is ~24h (vs 14 days).
  Hourly aggregates persist.
- **Negative — public, unauthenticated function URL.** Mitigated by reserved
  concurrency (10) as a throttle and a required `X-Admin-Token` on `/admin/*`.
- **Operational**: GTFS catalog import runs locally against the cloud database
  (one-shot, too heavy for the 15-minute Lambda cap).

## Alternatives Considered

- **Retry Oracle via PAYG upgrade**: the path that already failed; still
  capacity-gated.
- **Hetzner CAX21 (~€6.49/mo)**: keeps the full stack (incl. OTP/Timescale) with
  zero code changes, but isn't free and isn't AWS. Documented as the fallback if
  the serverless concessions become unacceptable.
- **AWS Fargate / small EC2**: a VM-shaped cost (~$15+/mo) the budget rules out.
- **Container-image Lambdas (ECR)**: unnecessary — deps fit the zip limit, and
  ECR adds a 500 MB free-tier cap and image housekeeping.
