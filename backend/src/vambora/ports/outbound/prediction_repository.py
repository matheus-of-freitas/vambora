from __future__ import annotations

from typing import Protocol

from vambora.domain.predictions import ArrivalPrediction


class PredictionRepository(Protocol):
    """Read port for naive real-time ETAs.

    Spans the catalog (route geometry, stop position) and tracking
    (live vehicle positions) tables — a single read against the shared DB.
    """

    async def predict_stop_arrivals(
        self,
        *,
        stop_id: str,
        fresh_seconds: int,
        fallback_kmh: float,
        max_horizon_seconds: int,
        max_snap_m: float,
        limit: int,
    ) -> list[ArrivalPrediction]:
        """Per live vehicle approaching ``stop_id``, the naive ETA.

        ``fresh_seconds`` gates vehicle liveness on ``received_at``.
        ``fallback_kmh`` floors the speed so a stopped bus still yields a
        finite ETA. ``max_snap_m`` is the max distance a vehicle may sit from
        a route shape to be considered "on" it. Vehicles already past the
        stop, or whose ETA exceeds ``max_horizon_seconds``, are excluded.
        Ordered by ETA ascending.
        """
        ...
