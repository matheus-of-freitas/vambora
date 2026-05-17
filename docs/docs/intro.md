---
slug: /
title: Introduction
sidebar_position: 1
---

# Vambora

> Real-time tracking, multi-modal routing, and proximity alerts for Rio de Janeiro public transit. Multi-platform (Web + Android), open-source, near-zero hosting cost.

## What lives in this site

- **Architecture** — the system's structure, sequence diagrams, and design rationale.
- **ADRs** — every non-trivial decision recorded with context and alternatives.
- **Domain** — the ubiquitous language and the bounded contexts of the model.
- **Data sources** — every external feed we depend on, with quirks and integration notes.
- **Development** — how to run the stack locally and what conventions apply.

## Repos

| Repo | Purpose |
|---|---|
| `vambora-backend` | API + ingestion workers (Python 3.12 + FastAPI + TimescaleDB + PostGIS) |
| `vambora-web` | Next.js 15 PWA |
| `vambora-android` | Native Android (Kotlin + Compose) |
| `vambora-docs` | This site |

The single source of truth for the product is the top-level `plan.md` in the parent project. This site dereferences it into focused, navigable documentation.

## Goals (from `plan.md`)

- Real-time tracking of buses, BRT, and VLT in Rio.
- Multi-modal route planning with transfers.
- Configurable proximity push notifications.
- Robust offline mode (downloaded GTFS bundle).
- Web + Android, sharing one backend.
- Hexagonal architecture extensible to other cities.
- Strong typing, high test coverage, excellent documentation.
- Open-source, MIT-licensed, ~$0/month hosting.
