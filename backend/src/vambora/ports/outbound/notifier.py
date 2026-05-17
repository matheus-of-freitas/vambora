from __future__ import annotations

from typing import Protocol

from vambora.domain.alerts import AlertTrigger


class Notifier(Protocol):
    """Push dispatch. The logging adapter is the MVP/dev implementation; an
    FCM adapter (credential-gated, see ``credentials.md``) is the deferred
    swap behind this same port — the evaluator never changes."""

    async def notify(self, trigger: AlertTrigger) -> None: ...
