"""Naive real-time ETAs at a stop (plan.md decision #7).

Unlike scheduled arrivals this needs no ``GTFS_DATE_OVERRIDE``: it reads the
*live* SPPO feed, so it works against real wall-clock time. An empty result
just means no live vehicle is currently approaching the stop on a known shape.
"""

from __future__ import annotations

from vambora.domain.predictions import ArrivalPrediction
from vambora.ports.outbound.prediction_repository import PredictionRepository
from vambora.shared.config import Settings


class GetStopPredictions:
    def __init__(self, *, repository: PredictionRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def __call__(self, stop_id: str, *, limit: int = 10) -> list[ArrivalPrediction]:
        return await self._repository.predict_stop_arrivals(
            stop_id=stop_id,
            fresh_seconds=self._settings.eta_fresh_seconds,
            fallback_kmh=self._settings.eta_fallback_kmh,
            max_horizon_seconds=self._settings.eta_max_horizon_seconds,
            max_snap_m=self._settings.eta_max_snap_m,
            limit=limit,
        )
