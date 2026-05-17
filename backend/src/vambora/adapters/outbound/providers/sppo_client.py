"""SPPO (RJ-SMTR) live-feed adapter.

See ``plan.md`` "Appendix: SPPO API Quirks" for the full quirk list. Highlights:
- Date-range filter is mandatory; the unfiltered response is ~90 MB.
- Format must be ISO ``YYYY-MM-DD HH:MM:SS`` in BRT (UTC-3, no DST).
- Filter operates on ``datahoraenvio`` (server arrival).
- Lat/lon are comma-decimal strings; timestamps are ms-epoch strings.
- Content-Type is ``text/html`` despite the body being JSON.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import httpx
from pydantic import BaseModel, Field, field_validator

from vambora.domain.shared.types import Coordinate
from vambora.domain.tracking import VehiclePosition
from vambora.shared.errors import ProviderError
from vambora.shared.logger import get_logger

BRT = timezone(timedelta(hours=-3), name="America/Sao_Paulo")
_HTTP_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)

log = get_logger("sppo")


class _RawPosition(BaseModel):
    vehicle_id: str = Field(alias="ordem")
    line_id: str = Field(alias="linha")
    latitude: float
    longitude: float
    speed_kmh: float = Field(alias="velocidade")
    recorded_at: datetime = Field(alias="datahora")
    sent_at: datetime = Field(alias="datahoraenvio")
    received_at: datetime = Field(alias="datahoraservidor")

    @field_validator("latitude", "longitude", "speed_kmh", mode="before")
    @classmethod
    def _comma_decimal(cls, v: object) -> object:
        if isinstance(v, str):
            return float(v.replace(",", "."))
        return v

    @field_validator("recorded_at", "sent_at", "received_at", mode="before")
    @classmethod
    def _ms_epoch(cls, v: object) -> object:
        if isinstance(v, str) and v.lstrip("-").isdigit():
            return datetime.fromtimestamp(int(v) / 1000, tz=UTC)
        return v


def parse_payload(payload: list[dict[str, Any]]) -> list[VehiclePosition]:
    """Convert raw SPPO records to domain ``VehiclePosition``s, skipping malformed rows."""
    out: list[VehiclePosition] = []
    skipped = 0
    for row in payload:
        try:
            r = _RawPosition.model_validate(row)
            out.append(
                VehiclePosition(
                    vehicle_id=r.vehicle_id,
                    line_id=r.line_id,
                    recorded_at=r.recorded_at,
                    sent_at=r.sent_at,
                    received_at=r.received_at,
                    coordinate=Coordinate(latitude=r.latitude, longitude=r.longitude),
                    speed_kmh=r.speed_kmh,
                    raw=row,
                )
            )
        except (ValueError, KeyError):
            skipped += 1
    if skipped:
        log.warning("sppo.parse.skipped", count=skipped)
    return out


def _format_brt(dt: datetime) -> str:
    return dt.astimezone(BRT).strftime("%Y-%m-%d %H:%M:%S")


class SppoClient:
    def __init__(self, *, base_url: str, http_client: httpx.AsyncClient) -> None:
        self._url = base_url
        self._http = http_client

    async def fetch(self, *, since: datetime, until: datetime) -> list[VehiclePosition]:
        params = {"dataInicial": _format_brt(since), "dataFinal": _format_brt(until)}
        try:
            response = await self._http.get(self._url, params=params, timeout=_HTTP_TIMEOUT)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"sppo fetch failed: {exc}") from exc
        # Server lies about content-type. Don't trust it.
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderError("sppo response was not valid JSON") from exc
        if not isinstance(payload, list):
            return []
        return parse_payload(payload)
