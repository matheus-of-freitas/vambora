"""Evaluate every alert rule against the live feed (server-side, decision #4).

Reuses the naive ETA (predictions context): for each rule, ask the prediction
repository for arrivals at the rule's stop and fire if a vehicle on the rule's
line is within ``threshold_minutes``. A per-rule cooldown
(``last_triggered_at`` + ``alert_cooldown_seconds``) stops a bus that dwells
within the threshold from re-firing every cycle.

A periodic evaluator (not the in-process event bus) is intentional for the
MVP: it reuses verified prediction code and is trivial to reason about. Moving
to event-driven evaluation is a documented future optimization.
"""

from __future__ import annotations

from datetime import timedelta

from vambora.domain.alerts import AlertTrigger
from vambora.ports.outbound.alert_rule_repository import AlertRuleRepository
from vambora.ports.outbound.notifier import Notifier
from vambora.ports.outbound.prediction_repository import PredictionRepository
from vambora.shared.config import Settings
from vambora.shared.time import Clock


class EvaluateAlerts:
    def __init__(
        self,
        *,
        rules: AlertRuleRepository,
        predictions: PredictionRepository,
        notifier: Notifier,
        clock: Clock,
        settings: Settings,
    ) -> None:
        self._rules = rules
        self._predictions = predictions
        self._notifier = notifier
        self._clock = clock
        self._settings = settings

    async def __call__(self) -> int:
        """Return how many rules fired this cycle."""
        now = self._clock.now()
        cooldown = timedelta(seconds=self._settings.alert_cooldown_seconds)
        fired = 0

        for rule in await self._rules.all_rules():
            if (
                rule.last_triggered_at is not None
                and now - rule.last_triggered_at < cooldown
            ):
                continue

            predictions = await self._predictions.predict_stop_arrivals(
                stop_id=rule.stop_id,
                fresh_seconds=self._settings.eta_fresh_seconds,
                fallback_kmh=self._settings.eta_fallback_kmh,
                max_horizon_seconds=self._settings.eta_max_horizon_seconds,
                max_snap_m=self._settings.eta_max_snap_m,
                limit=20,
            )
            # predictions are sorted by ETA; first line match is the soonest.
            match = next(
                (
                    p
                    for p in predictions
                    if p.line_short_name == rule.line_short_name
                    and p.eta_seconds <= rule.threshold_minutes * 60
                ),
                None,
            )
            if match is None:
                continue

            await self._notifier.notify(
                AlertTrigger(
                    rule_id=rule.id,
                    device_id=rule.device_id,
                    line_short_name=rule.line_short_name,
                    stop_id=rule.stop_id,
                    vehicle_id=match.vehicle_id,
                    eta_minutes=max(1, round(match.eta_seconds / 60)),
                    triggered_at=now,
                )
            )
            await self._rules.mark_triggered(rule.id, now)
            fired += 1

        return fired
