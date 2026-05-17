from __future__ import annotations

from datetime import datetime
from typing import Protocol

from vambora.domain.alerts import AlertRule


class AlertRuleRepository(Protocol):
    """Persistence port for device-scoped alert rules."""

    async def add(
        self,
        *,
        device_id: str,
        line_short_name: str,
        stop_id: str,
        threshold_minutes: int,
    ) -> AlertRule: ...

    async def delete(self, rule_id: str) -> bool:
        """``True`` if a row was deleted, ``False`` if no such id."""
        ...

    async def list_for_device(self, device_id: str) -> list[AlertRule]: ...

    async def all_rules(self) -> list[AlertRule]:
        """Every rule — the evaluator's working set."""
        ...

    async def mark_triggered(self, rule_id: str, at: datetime) -> None: ...
