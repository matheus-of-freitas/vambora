from __future__ import annotations

import asyncio
import time

from vambora.application.commands.evaluate_alerts import EvaluateAlerts
from vambora.shared.logger import get_logger

log = get_logger("alerts")


class AlertEvaluator:
    """Periodic server-side rule evaluation, run alongside the SPPO poller."""

    def __init__(self, *, evaluate: EvaluateAlerts, interval_seconds: int) -> None:
        self._evaluate = evaluate
        self._interval = interval_seconds

    async def run_forever(self) -> None:
        log.info("alerts.start", interval=self._interval)
        while True:
            started = time.perf_counter()
            try:
                fired = await self._evaluate()
                if fired:
                    log.info(
                        "alerts.tick",
                        fired=fired,
                        duration_ms=round((time.perf_counter() - started) * 1000, 1),
                    )
            except Exception:
                log.exception("alerts.tick.unhandled")
            await asyncio.sleep(self._interval)
