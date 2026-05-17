from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from vambora.adapters.inbound.http.dependencies import Container, container
from vambora.adapters.inbound.http.schemas.catalog import RouteDTO
from vambora.adapters.inbound.http.schemas.vehicle import (
    HourlyLineStatDTO,
    VehiclePositionDTO,
)

router = APIRouter(prefix="/lines", tags=["lines"])


class LineRealtimeDTO(BaseModel):
    routes: list[RouteDTO]
    vehicles: list[VehiclePositionDTO]


@router.get("", response_model=list[RouteDTO])
async def list_lines(
    agency_id: str | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=5000),
    c: Container = Depends(container),
) -> list[RouteDTO]:
    routes = await c.list_routes(agency_id=agency_id, limit=limit)
    return [RouteDTO.from_domain(r) for r in routes]


@router.get("/{short_name}/realtime", response_model=LineRealtimeDTO)
async def line_realtime(
    short_name: str,
    fresh_seconds: int = Query(default=180, ge=10, le=3600),
    c: Container = Depends(container),
) -> LineRealtimeDTO:
    result = await c.get_line_realtime(short_name, fresh_seconds=fresh_seconds)
    if not result.routes:
        raise HTTPException(status_code=404, detail="line not found in catalog")
    return LineRealtimeDTO(
        routes=[RouteDTO.from_domain(r) for r in result.routes],
        vehicles=[VehiclePositionDTO.from_domain(v) for v in result.vehicles],
    )


@router.get("/{short_name}/shape")
async def line_shape(
    short_name: str,
    c: Container = Depends(container),
) -> dict[str, object]:
    """GeoJSON FeatureCollection with one LineString per distinct shape on the line."""
    shapes = await c.get_line_shape(short_name)
    if not shapes:
        raise HTTPException(status_code=404, detail="no shapes for this line")
    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[p.longitude, p.latitude] for p in pts],
            },
            "properties": {},
        }
        for pts in shapes
    ]
    return {"type": "FeatureCollection", "features": features}


@router.get("/{short_name}/stats", response_model=list[HourlyLineStatDTO])
async def line_stats(
    short_name: str,
    hours: int = Query(default=24, ge=1, le=336),
    c: Container = Depends(container),
) -> list[HourlyLineStatDTO]:
    """Hourly activity buckets for a line from the continuous aggregate."""
    stats = await c.get_line_stats(short_name, hours=hours)
    return [HourlyLineStatDTO.from_domain(s) for s in stats]
