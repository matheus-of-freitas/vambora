"""SPPO client + normalization.

Quirks confirmed against the live feed on 2026-05-08:
- Date filter params are `dataInicial` / `dataFinal`, ISO `YYYY-MM-DD HH:MM:SS` (BRT).
- Filter applies to `datahoraenvio`, not `datahora`. Some `datahora` values are stale.
- Lat/lon are strings with comma decimal separator: "-22,89623".
- Timestamps are ms-since-epoch as strings: "1778261843000".
- Content-Type lies (`text/html`); body is JSON.
- Without filters the response is ~90MB and effectively unusable.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import httpx
from pydantic import BaseModel, Field, field_validator

from src.config import settings

# Brazil/Rio is UTC-3 year-round (no DST since 2019). The API expects local time.
BRT = timezone(timedelta(hours=-3), name="America/Sao_Paulo")

# Cap a single fetch's wall time. The full-dump response is huge; with filters
# we expect <1MB but allow headroom.
HTTP_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)


class VehiclePosition(BaseModel):
    vehicle_id: str = Field(alias="ordem")
    line_id: str = Field(alias="linha")
    latitude: float
    longitude: float
    speed_kmh: float = Field(alias="velocidade")
    recorded_at: datetime = Field(alias="datahora")
    sent_at: datetime = Field(alias="datahoraenvio")
    received_at: datetime = Field(alias="datahoraservidor")
    raw: dict[str, Any]

    @field_validator("latitude", "longitude", "speed_kmh", mode="before")
    @classmethod
    def _comma_decimal(cls, v: object) -> object:
        if isinstance(v, str):
            return float(v.replace(",", "."))
        return v

    @field_validator("recorded_at", "sent_at", "received_at", mode="before")
    @classmethod
    def _ms_epoch(cls, v: object) -> object:
        if isinstance(v, str) and v.isdigit():
            return datetime.fromtimestamp(int(v) / 1000, tz=UTC)
        return v


def _format_brt(dt: datetime) -> str:
    return dt.astimezone(BRT).strftime("%Y-%m-%d %H:%M:%S")


def _parse_payload(payload: list[dict[str, Any]]) -> list[VehiclePosition]:
    out: list[VehiclePosition] = []
    for row in payload:
        try:
            out.append(VehiclePosition.model_validate({**row, "raw": row}))
        except (ValueError, KeyError):
            continue  # skip malformed records — the spike's job is to learn, not crash
    return out


async def fetch(client: httpx.AsyncClient, *, since: datetime, until: datetime) -> list[VehiclePosition]:
    params = {
        "dataInicial": _format_brt(since),
        "dataFinal": _format_brt(until),
    }
    response = await client.get(settings.sppo_url, params=params, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    # Server returns text/html but body is JSON. Don't trust the header.
    payload = response.json()
    if not isinstance(payload, list):
        return []
    return _parse_payload(payload)
