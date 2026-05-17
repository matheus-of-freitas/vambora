---
sidebar_position: 2
---

# C4 — System context

```mermaid
C4Context
title System Context - Vambora

Person(user, "User", "Public transit rider in Rio de Janeiro")

System(vambora, "Vambora", "Real-time tracking, routing, and alerts for public transit")

System_Ext(sppo, "SPPO API", "Real-time GPS data for buses and BRT")
System_Ext(dataRio, "data.rio", "Static GTFS feed: lines, stops, schedules")
System_Ext(fcm, "Firebase Cloud Messaging", "Push notification delivery")
System_Ext(tiles, "Tile Provider", "Vector / raster map tiles")

Rel(user, vambora, "Uses via web or Android")
Rel(vambora, sppo, "Polls every 30s", "HTTPS")
Rel(vambora, dataRio, "Daily GTFS sync", "HTTPS")
Rel(vambora, fcm, "Dispatches alerts", "HTTPS")
Rel(vambora, tiles, "Fetches tiles", "HTTPS")
```

The user interacts with Vambora through a Next.js PWA or a native Android app. Both clients share one backend. The backend depends on four external systems: SPPO (live GPS feed), data.rio (static GTFS catalog), FCM (push delivery), and a tile provider (Carto in dev, self-hosted Protomaps in prod).
