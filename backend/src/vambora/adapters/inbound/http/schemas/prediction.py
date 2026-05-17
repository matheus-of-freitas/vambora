from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from vambora.domain.predictions import ArrivalPrediction


class PredictionDTO(BaseModel):
    line_short_name: str
    vehicle_id: str
    distance_m: float
    speed_kmh: float
    eta_seconds: int
    eta_minutes: int  # ceil-ish whole minutes, for client convenience
    eta_at: datetime
    route_long_name: str | None
    route_color: str | None

    @classmethod
    def from_domain(cls, p: ArrivalPrediction) -> PredictionDTO:
        return cls(
            line_short_name=p.line_short_name,
            vehicle_id=p.vehicle_id,
            distance_m=round(p.distance_m, 1),
            speed_kmh=round(p.speed_kmh, 1),
            eta_seconds=p.eta_seconds,
            eta_minutes=max(1, round(p.eta_seconds / 60)),
            eta_at=p.eta_at,
            route_long_name=p.route_long_name,
            route_color=p.route_color,
        )
