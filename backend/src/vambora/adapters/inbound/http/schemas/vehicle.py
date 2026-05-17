from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from vambora.domain.tracking import HourlyLineStat, VehiclePosition


class VehiclePositionDTO(BaseModel):
    vehicle_id: str
    line_id: str
    recorded_at: datetime
    sent_at: datetime
    received_at: datetime
    latitude: float
    longitude: float
    speed_kmh: float

    @classmethod
    def from_domain(cls, p: VehiclePosition) -> VehiclePositionDTO:
        return cls(
            vehicle_id=p.vehicle_id,
            line_id=p.line_id,
            recorded_at=p.recorded_at,
            sent_at=p.sent_at,
            received_at=p.received_at,
            latitude=p.coordinate.latitude,
            longitude=p.coordinate.longitude,
            speed_kmh=p.speed_kmh,
        )


class HourlyLineStatDTO(BaseModel):
    bucket: datetime
    position_count: int
    vehicle_count: int
    avg_speed_kmh: float
    max_speed_kmh: float

    @classmethod
    def from_domain(cls, s: HourlyLineStat) -> HourlyLineStatDTO:
        return cls(
            bucket=s.bucket,
            position_count=s.position_count,
            vehicle_count=s.vehicle_count,
            avg_speed_kmh=round(s.avg_speed_kmh, 2),
            max_speed_kmh=round(s.max_speed_kmh, 2),
        )
