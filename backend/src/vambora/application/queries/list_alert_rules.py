from __future__ import annotations

from vambora.domain.alerts import AlertRule
from vambora.ports.outbound.alert_rule_repository import AlertRuleRepository


class ListAlertRules:
    def __init__(self, *, rules: AlertRuleRepository) -> None:
        self._rules = rules

    async def __call__(self, device_id: str) -> list[AlertRule]:
        return await self._rules.list_for_device(device_id)
