"""Dev/MVP notifier: structured log line instead of a real push.

The FCM adapter (credential-gated — Firebase, see ``credentials.md``) is the
deferred swap behind the ``Notifier`` port. Until it lands, a triggered alert
is observable in the logs, which is enough to verify rule evaluation
end-to-end against the live feed.
"""

from __future__ import annotations

from vambora.domain.alerts import AlertTrigger
from vambora.shared.logger import get_logger

log = get_logger("alerts")


class LoggingNotifier:
    async def notify(self, trigger: AlertTrigger) -> None:
        log.info(
            "alert.triggered",
            rule_id=trigger.rule_id,
            device_id=trigger.device_id,
            line=trigger.line_short_name,
            stop_id=trigger.stop_id,
            vehicle_id=trigger.vehicle_id,
            eta_minutes=trigger.eta_minutes,
            triggered_at=trigger.triggered_at.isoformat(),
        )
