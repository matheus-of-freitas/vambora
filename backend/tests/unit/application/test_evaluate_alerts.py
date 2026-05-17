from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from vambora.application.commands.evaluate_alerts import EvaluateAlerts
from vambora.domain.alerts import AlertRule, AlertTrigger
from vambora.domain.predictions import ArrivalPrediction
from vambora.shared.config import Settings

pytestmark = pytest.mark.unit

_NOW = datetime(2026, 5, 16, 12, 0, tzinfo=UTC)


def _settings() -> Settings:
    # Bypass env/validation; set only what EvaluateAlerts reads.
    return Settings.model_construct(
        eta_fresh_seconds=180,
        eta_fallback_kmh=15.0,
        eta_max_horizon_seconds=3600,
        eta_max_snap_m=150.0,
        alert_cooldown_seconds=600,
    )


def _rule(*, line: str = "639", threshold: int = 10, last: datetime | None = None) -> AlertRule:
    return AlertRule(
        id="r1",
        device_id="d1",
        line_short_name=line,
        stop_id="S1",
        threshold_minutes=threshold,
        created_at=_NOW - timedelta(days=1),
        last_triggered_at=last,
    )


def _pred(line: str, eta_seconds: int) -> ArrivalPrediction:
    return ArrivalPrediction(
        line_short_name=line,
        vehicle_id="B1",
        distance_m=500.0,
        speed_kmh=20.0,
        eta_seconds=eta_seconds,
        eta_at=_NOW,
        route_long_name=None,
        route_color=None,
    )


class _FakeRules:
    def __init__(self, rules: list[AlertRule]) -> None:
        self._rules = rules
        self.triggered: list[tuple[str, datetime]] = []

    async def all_rules(self) -> list[AlertRule]:
        return self._rules

    async def mark_triggered(self, rule_id: str, at: datetime) -> None:
        self.triggered.append((rule_id, at))


class _FakePredictions:
    def __init__(self, preds: list[ArrivalPrediction]) -> None:
        self._preds = preds

    async def predict_stop_arrivals(self, **_: object) -> list[ArrivalPrediction]:
        return self._preds


class _FakeNotifier:
    def __init__(self) -> None:
        self.sent: list[AlertTrigger] = []

    async def notify(self, trigger: AlertTrigger) -> None:
        self.sent.append(trigger)


class _FixedClock:
    def now(self) -> datetime:
        return _NOW


def _make(rules: _FakeRules, preds: _FakePredictions, notifier: _FakeNotifier) -> EvaluateAlerts:
    return EvaluateAlerts(
        rules=rules,  # type: ignore[arg-type]
        predictions=preds,  # type: ignore[arg-type]
        notifier=notifier,  # type: ignore[arg-type]
        clock=_FixedClock(),
        settings=_settings(),
    )


async def test_fires_when_line_within_threshold() -> None:
    rules = _FakeRules([_rule(threshold=10)])
    notifier = _FakeNotifier()
    cmd = _make(rules, _FakePredictions([_pred("639", 7 * 60)]), notifier)

    assert await cmd() == 1
    assert len(notifier.sent) == 1
    assert notifier.sent[0].vehicle_id == "B1"
    assert notifier.sent[0].eta_minutes == 7
    assert rules.triggered == [("r1", _NOW)]


async def test_skips_when_in_cooldown() -> None:
    rules = _FakeRules([_rule(last=_NOW - timedelta(seconds=120))])  # < 600 cooldown
    notifier = _FakeNotifier()
    cmd = _make(rules, _FakePredictions([_pred("639", 60)]), notifier)

    assert await cmd() == 0
    assert notifier.sent == []


async def test_fires_again_after_cooldown_elapsed() -> None:
    rules = _FakeRules([_rule(last=_NOW - timedelta(seconds=900))])  # > 600
    notifier = _FakeNotifier()
    cmd = _make(rules, _FakePredictions([_pred("639", 60)]), notifier)

    assert await cmd() == 1
    assert len(notifier.sent) == 1


async def test_no_fire_when_eta_beyond_threshold_or_other_line() -> None:
    rules = _FakeRules([_rule(line="639", threshold=5)])
    notifier = _FakeNotifier()
    # 639 is 20 min away (> 5), and the 8-min bus is a different line.
    cmd = _make(
        rules,
        _FakePredictions([_pred("639", 20 * 60), _pred("100", 8 * 60)]),
        notifier,
    )

    assert await cmd() == 0
    assert notifier.sent == []
