"""Read-model for a naive, real-time arrival estimate at a stop.

This is the MVP "naive ETA" (plan.md decision #7): linear extrapolation from
a vehicle's latest *live* GPS fix along the route geometry to the stop.
Liveness is gated on ``received_at`` (decision #25), enforced in the query.

It is deliberately crude: distance-along-route ÷ a speed (the vehicle's own
reported speed, floored by a fallback so a stopped bus still yields a finite
ETA). No trip pairing, no dwell modelling, no traffic — Phase 2 replaces this
with an ML model.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ArrivalPrediction:
    line_short_name: str
    vehicle_id: str
    distance_m: float
    speed_kmh: float  # the speed actually used (vehicle's, floored by fallback)
    eta_seconds: int
    eta_at: datetime  # aware UTC; now + eta_seconds
    route_long_name: str | None
    route_color: str | None
