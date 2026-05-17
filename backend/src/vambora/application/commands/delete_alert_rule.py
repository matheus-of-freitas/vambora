from __future__ import annotations

from vambora.ports.outbound.alert_rule_repository import AlertRuleRepository


class DeleteAlertRule:
    def __init__(self, *, rules: AlertRuleRepository) -> None:
        self._rules = rules

    async def __call__(self, rule_id: str) -> bool:
        """``True`` if a rule was removed, ``False`` if no such id."""
        return await self._rules.delete(rule_id)
