---
sidebar_position: 1
title: Index
---

# Architecture Decision Records

Decisions are recorded close to the code they affect. Backend ADRs live in `vambora-backend/docs/adrs/`; web, Android, and cross-cutting ADRs land here as they're written.

## Backend ADRs

| # | Status | Title |
|---|---|---|
| 0001 | Accepted | Hexagonal architecture with DDD-lite, pragmatic CQRS, event-driven ingestion |
| 0002 | Accepted | Python 3.12 + FastAPI for the backend |
| 0003 | Accepted | PostgreSQL 16 + TimescaleDB + PostGIS as the single store |
| 0004 | Accepted | Redis for cache and pub/sub |
| 0005 | Accepted | OpenTripPlanner v2 for multi-modal routing |

Read them in `vambora-backend/docs/adrs/`. They will be embedded here once the backend is published to GitHub and a build-time include is wired up.

## Format

Every ADR uses the template documented in `plan.md` §"Architecture Decision Records (ADRs)":

```markdown
# ADR-NNNN: <Title>
- Status: Proposed | Accepted | Superseded by ADR-XXXX | Deprecated
- Date: YYYY-MM-DD
- Deciders: @username

## Context
## Decision
## Consequences (Positive / Negative / Neutral)
## Alternatives Considered
```

## When to write a new one

Write an ADR when picking among materially different libraries, languages, services, or patterns; when reversing a prior decision; or when introducing a constraint future contributors will silently bump into. Don't write one for trivial dependency bumps or anything `plan.md` already settles.
