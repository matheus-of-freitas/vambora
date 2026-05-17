---
sidebar_position: 1
---

# Architectural overview

Vambora's backend follows **Hexagonal (Ports & Adapters)** with three pragmatic refinements: DDD-lite (bounded contexts, no full aggregate modeling), pragmatic CQRS (commands and queries split in code, single database), and event-driven ingestion (in-process pub/sub now, Redis later).

The full rationale lives in [ADR-0001](../adrs/index.md).

## Bounded contexts

| Context | Responsibility |
|---|---|
| `tracking` | Live vehicle positions, GPS ingestion, current state |
| `catalog` | Static GTFS data: routes, stops, trips, schedules, agencies |
| `routing` | Multi-modal itineraries, transfers, walking legs |
| `predictions` | ETAs, headways, punctuality, derived signals |
| `alerts` | User-defined rules and notification dispatch |
| `user` | Device identity, preferences, favorites |

Only `tracking` is implemented today. The rest are placeholders that will fill in across Phase 1 and beyond.

## Dependency rule

```
domain      → nothing (pure Python / pure Kotlin)
application → domain + ports
adapters    → ports + third-party libraries
```

Code that ingests SPPO, persists to Postgres, calls Firebase, or talks to OpenTripPlanner all lives behind ports. Swapping any one of those touches only an adapter.
