from __future__ import annotations

from vambora.domain.alerts import AlertError, AlertRule
from vambora.ports.outbound.alert_rule_repository import AlertRuleRepository
from vambora.ports.outbound.repositories import CatalogRepository


class RegisterAlertRule:
    """Validate the stop/line exist (good feedback for a bad request) then
    persist the device-scoped rule."""

    def __init__(
        self,
        *,
        rules: AlertRuleRepository,
        catalog: CatalogRepository,
    ) -> None:
        self._rules = rules
        self._catalog = catalog

    async def __call__(
        self,
        *,
        device_id: str,
        line_short_name: str,
        stop_id: str,
        threshold_minutes: int,
    ) -> AlertRule:
        if await self._catalog.find_stop_by_id(stop_id) is None:
            raise AlertError(f"unknown stop_id: {stop_id}")
        if not await self._catalog.find_routes_by_short_name(line_short_name):
            raise AlertError(f"unknown line: {line_short_name}")
        return await self._rules.add(
            device_id=device_id,
            line_short_name=line_short_name,
            stop_id=stop_id,
            threshold_minutes=threshold_minutes,
        )
