from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from vambora.adapters.inbound.http.dependencies import Container, container
from vambora.adapters.inbound.http.schemas.vehicle import VehiclePositionDTO

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehiclePositionDTO])
async def list_live(
    line_id: str | None = Query(default=None),
    fresh_seconds: int = Query(default=120, ge=10, le=3600),
    limit: int = Query(default=2000, ge=1, le=10000),
    c: Container = Depends(container),
) -> list[VehiclePositionDTO]:
    positions = await c.get_live_vehicles(line_id=line_id, fresh_seconds=fresh_seconds, limit=limit)
    return [VehiclePositionDTO.from_domain(p) for p in positions]


@router.get("/{vehicle_id}", response_model=list[VehiclePositionDTO])
async def vehicle_history(
    vehicle_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    c: Container = Depends(container),
) -> list[VehiclePositionDTO]:
    positions = await c.get_vehicle_history(vehicle_id, limit=limit)
    if not positions:
        raise HTTPException(status_code=404, detail="vehicle not found")
    return [VehiclePositionDTO.from_domain(p) for p in positions]
