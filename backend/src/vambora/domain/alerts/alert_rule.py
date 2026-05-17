"""Device-scoped geofence alert (plan.md decision #4: push critical from MVP).

A rule says "notify device D when a bus on line L is at most T minutes from
stop S". "Minutes away" reuses the naive ETA (decision #7 / predictions
context). ``last_triggered_at`` powers a per-rule cooldown so a bus dwelling
within the threshold doesn't re-fire every evaluation cycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from vambora.domain.shared.errors import InvariantViolation


@dataclass(frozen=True, slots=True)
class AlertRule:
    id: str
    device_id: str
    line_short_name: str
    stop_id: str
    threshold_minutes: int
    created_at: datetime
    last_triggered_at: datetime | None

    def __post_init__(self) -> None:
        if not self.device_id:
            raise InvariantViolation("device_id required")
        if not self.line_short_name:
            raise InvariantViolation("line_short_name required")
        if not self.stop_id:
            raise InvariantViolation("stop_id required")
        if not 1 <= self.threshold_minutes <= 60:
            raise InvariantViolation("threshold_minutes must be in 1..60")


@dataclass(frozen=True, slots=True)
class AlertTrigger:
    """Transient: a rule matched a live vehicle this cycle. Handed to the
    ``Notifier`` (logging stub now; FCM is the deferred swap)."""

    rule_id: str
    device_id: str
    line_short_name: str
    stop_id: str
    vehicle_id: str
    eta_minutes: int
    triggered_at: datetime
