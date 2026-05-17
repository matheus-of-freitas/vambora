from __future__ import annotations

from typing import Protocol


class EventBus(Protocol):
    """In-process or Redis pub/sub bus for cross-context event fan-out."""

    async def publish(self, channel: str, payload: dict[str, object]) -> None: ...
