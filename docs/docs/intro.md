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

## Layout

A single monorepo (`vambora`):

| Path | Purpose |
|---|---|
| `backend/` | API + ingestion/alert workers (Python 3.12 + FastAPI + TimescaleDB + PostGIS) |
| `web/` | Next.js 15 PWA |
| `docs/` | This site (Docusaurus 3) |

A native Android app (Kotlin + Compose) is planned. This site is the
navigable documentation for the architecture and decisions.

## Goals

- Real-time tracking of buses, BRT, and VLT in Rio.
- Multi-modal route planning with transfers.
- Configurable proximity push notifications.
- Robust offline mode (downloaded GTFS bundle).
- Web + Android, sharing one backend.
- Hexagonal architecture extensible to other cities.
- Strong typing, high test coverage, excellent documentation.
- Open-source, MIT-licensed, ~$0/month hosting.
