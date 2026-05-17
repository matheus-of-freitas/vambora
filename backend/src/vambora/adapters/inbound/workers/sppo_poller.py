from __future__ import annotations

import asyncio
import time

from vambora.application.commands.ingest_vehicle_positions import IngestVehiclePositions
from vambora.shared.errors import ProviderError
from vambora.shared.logger import get_logger

log = get_logger("poller")


class SppoPoller:
    def __init__(self, *, ingest: IngestVehiclePositions, interval_seconds: int) -> None:
        self._ingest = ingest
        self._interval = interval_seconds

    async def run_forever(self) -> None:
        log.info("poller.start", interval=self._interval)
        while True:
            started = time.perf_counter()
            try:
                result = await self._ingest()
                log.info(
                    "tick.ok",
                    fetched=result.fetched,
                    persisted=result.persisted,
                    duration_ms=round((time.perf_counter() - started) * 1000, 1),
                )
            except ProviderError as exc:
                log.warning("tick.provider_error", error=str(exc))
            except Exception:
                log.exception("tick.unhandled")
            await asyncio.sleep(self._interval)
