from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from vambora.domain.alerts import AlertRule


class CreateAlertRuleRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=128)
    line_short_name: str = Field(min_length=1, max_length=32)
    stop_id: str = Field(min_length=1, max_length=64)
    threshold_minutes: int = Field(ge=1, le=60)


class AlertRuleDTO(BaseModel):
    id: str
    device_id: str
    line_short_name: str
    stop_id: str
    threshold_minutes: int
    created_at: datetime
    last_triggered_at: datetime | None

    @classmethod
    def from_domain(cls, r: AlertRule) -> AlertRuleDTO:
        return cls(
            id=r.id,
            device_id=r.device_id,
            line_short_name=r.line_short_name,
            stop_id=r.stop_id,
            threshold_minutes=r.threshold_minutes,
            created_at=r.created_at,
            last_triggered_at=r.last_triggered_at,
        )
