"""In-process no-op event bus.

A real Redis pub/sub adapter lands when the alerts worker arrives. For now the
ingestion path needs an ``EventBus`` shape so wiring code can stay stable.
"""

from __future__ import annotations

from vambora.shared.logger import get_logger

log = get_logger("event_bus")


class InProcEventBus:
    async def publish(self, channel: str, payload: dict[str, object]) -> None:
        log.debug("event.published", channel=channel, payload=payload)
