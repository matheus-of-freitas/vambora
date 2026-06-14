"""Scheduled Lambda: one ingest + alert-evaluation + compaction pass.

EventBridge fires this once a minute. Locally the same work runs as the
long-lived ``SppoPoller`` and ``AlertEvaluator`` loops in ``main.py``; here each
invocation does a single pass and exits, which is what a scheduled Lambda wants.

Compaction (rollup + retention) only has work to do on plain Postgres and is
gated to every fifth minute — purging the small trickle of newly-expired rows
in frequent, short-lock batches rather than one big hourly sweep.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from mangum.types import LambdaContext

from vambora.adapters.inbound.http.dependencies import Container, build_container
from vambora.shared.config import load_settings
from vambora.shared.errors import ProviderError
from vambora.shared.logger import configure_logging, get_logger

log = get_logger("poller-lambda")

# Run compaction on minutes divisible by this. Rollup looks back hours, so an
# occasional skipped minute is self-correcting; purge is idempotent.
_COMPACT_EVERY_MINUTES = 5


async def run_once(container: Container, *, now: datetime | None = None) -> None:
    now = now or datetime.now(UTC)
    settings = container.settings

    for _ in range(max(1, settings.polls_per_invocation)):
        try:
            result = await container.ingest()
            log.info("tick.ok", fetched=result.fetched, persisted=result.persisted)
        except ProviderError as exc:
            log.warning("tick.provider_error", error=str(exc))

    try:
        fired = await container.evaluate_alerts()
        if fired:
            log.info("alerts.tick", fired=fired)
    except Exception:
        log.exception("alerts.tick.unhandled")

    if now.minute % _COMPACT_EVERY_MINUTES == 0:
        try:
            compacted = await container.compact_tracking_data()
            if not compacted.skipped:
                log.info("compact.ok", rolled_up=compacted.rolled_up, purged=compacted.purged)
        except Exception:
            log.exception("compact.unhandled")


async def _run() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    container = build_container(settings)
    try:
        await run_once(container)
    finally:
        await container.http_client.aclose()
        await container.db.dispose()


def handler(_event: dict[str, Any], _context: LambdaContext) -> dict[str, str]:
    # Scheduled invocation carries no input we act on.
    asyncio.run(_run())
    return {"status": "ok"}
