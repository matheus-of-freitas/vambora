# ADR-0004: Redis for cache and pub/sub

- Status: Accepted
- Date: 2026-05-09
- Deciders: @matheusallein

## Context

Two cross-cutting concerns appear early: (1) caching the latest position per vehicle for sub-second `GET /lines/{id}/realtime` responses without hammering the hypertable, and (2) fanning out `vehicle.position.received` events from the ingestion worker to the alerts worker and (later) the cache updater and a WebSocket broadcaster. We don't need durable message queueing, exactly-once semantics, partition replay, or schema evolution.

## Decision

Use **Redis 7** for both caching and lightweight pub/sub. Single instance (`redis:7-alpine` in dev). Keys are prefixed with `vambora:` per `plan.md`. The event bus port has a Redis adapter that lands when the alerts worker moves to its own process; until then an in-process bus satisfies the same `EventBus` Protocol so no application code changes at the cutover.

## Consequences

- **Positive**: zero-ceremony setup, well-known operational profile, low memory footprint at our scale.
- **Positive**: the same Redis instance later hosts rate limiters, idempotency keys, and short-lived signed-link state for the "share live trip" feature.
- **Negative**: pub/sub is fire-and-forget. A worker that's offline misses events. Acceptable for alerts (they only fire on fresh positions anyway); explicitly **not** acceptable for cross-context consistency, which we don't have.
- **Negative**: Redis adds a service to the deployment. Mitigated by keeping it on the same VPS as the API; failure mode is degraded freshness, not data loss.

## Alternatives Considered

- **RabbitMQ**: rejected; durable queueing isn't needed and adds a dependency we'd nurse for years.
- **Kafka / Redpanda**: rejected; gross overkill for this scale and budget.
- **NATS**: tempting (smaller, simpler than RabbitMQ), but Redis already earns its keep as a cache; doubling up on infrastructure isn't justified.
- **Postgres LISTEN/NOTIFY**: rejected; adds load to the same DB the hot path writes to, and payload size limits make event evolution awkward.
