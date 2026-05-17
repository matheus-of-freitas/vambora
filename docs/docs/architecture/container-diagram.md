---
sidebar_position: 3
---

# C4 — Containers

```mermaid
C4Container
title Container Diagram - Vambora

Person(user, "User")

System_Boundary(clients, "Clients") {
    Container(web, "Web App", "Next.js 15, TypeScript, MapLibre GL JS", "PWA with map, search, routing")
    Container(android, "Android App", "Kotlin, Compose, MapLibre Native", "Native mobile app")
}

System_Boundary(edge, "Edge") {
    Container(cloudflare, "Cloudflare", "CDN, DNS, Pages, R2", "Hosts web app, proxies API, stores offline bundles")
}

System_Boundary(server, "Backend (Oracle Cloud Free Tier VPS)") {
    Container(api, "API", "FastAPI, Python 3.12", "REST and WebSocket endpoints")
    Container(otp, "Routing Engine", "OpenTripPlanner v2, Java 21", "Multi-modal routing")
    Container(workerIngest, "Ingestion Worker", "Python asyncio", "SPPO polling and GTFS sync")
    Container(workerAlerts, "Alerts Worker", "Python asyncio", "Rule evaluation and FCM dispatch")
    Container(workerSnapshots, "Snapshots Worker", "Python", "Builds offline bundles weekly")

    ContainerDb(postgres, "PostgreSQL 16", "TimescaleDB, PostGIS", "History, GTFS, alert rules")
    ContainerDb(redis, "Redis 7", "Cache, Pub/Sub", "Current positions, events")
}

System_Ext(sppo, "SPPO API")
System_Ext(dataRio, "data.rio")
System_Ext(fcm, "Firebase Cloud Messaging")

Rel(user, web, "HTTPS")
Rel(user, android, "HTTPS")
Rel(web, cloudflare, "")
Rel(android, cloudflare, "")
Rel(cloudflare, api, "Proxies requests")

Rel(api, postgres, "SQL")
Rel(api, redis, "Cache reads")
Rel(api, otp, "HTTP (internal)")

Rel(workerIngest, sppo, "Polls every 30s")
Rel(workerIngest, dataRio, "Syncs GTFS daily")
Rel(workerIngest, postgres, "Persists positions")
Rel(workerIngest, redis, "Publishes events")

Rel(workerAlerts, redis, "Subscribes to events")
Rel(workerAlerts, postgres, "Reads active rules")
Rel(workerAlerts, fcm, "Sends push")

Rel(workerSnapshots, postgres, "Aggregates history")
Rel(workerSnapshots, cloudflare, "Uploads bundle to R2")
```

In Phase 0 the API container and the SPPO ingestion worker run together in one process (see `vambora-backend/src/vambora/main.py`). They split into separate processes when the alerts worker arrives. Until then the in-process bus described in [ADR-0001](../adrs/index.md) and [ADR-0004](../adrs/index.md) is sufficient.
