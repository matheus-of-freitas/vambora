from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from vambora.adapters.inbound.http.dependencies import Container, container
from vambora.adapters.inbound.http.schemas.catalog import ArrivalDTO, StopDTO
from vambora.adapters.inbound.http.schemas.prediction import PredictionDTO

router = APIRouter(prefix="/stops", tags=["stops"])


@router.get("/nearby", response_model=list[StopDTO])
async def stops_nearby(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_m: int = Query(default=500, ge=10, le=10_000),
    limit: int = Query(default=200, ge=1, le=1000),
    c: Container = Depends(container),
) -> list[StopDTO]:
    stops = await c.find_nearby_stops(latitude=lat, longitude=lon, radius_m=radius_m, limit=limit)
    return [StopDTO.from_domain(s) for s in stops]


@router.get("/{stop_id}", response_model=StopDTO)
async def stop_by_id(
    stop_id: str,
    c: Container = Depends(container),
) -> StopDTO:
    stop = await c.get_stop(stop_id)
    if stop is None:
        raise HTTPException(status_code=404, detail="stop not found")
    return StopDTO.from_domain(stop)


@router.get("/{stop_id}/arrivals", response_model=list[ArrivalDTO])
async def stop_arrivals(
    stop_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    c: Container = Depends(container),
) -> list[ArrivalDTO]:
    arrivals = await c.get_stop_arrivals(stop_id, limit=limit)
    return [ArrivalDTO.from_domain(a) for a in arrivals]


@router.get("/{stop_id}/predictions", response_model=list[PredictionDTO])
async def stop_predictions(
    stop_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    c: Container = Depends(container),
) -> list[PredictionDTO]:
    """Naive real-time ETAs from live vehicles (plan.md decision #7).

    Empty when no live vehicle is currently approaching on a known shape —
    the client falls back to scheduled ``/arrivals``.
    """
    predictions = await c.get_stop_predictions(stop_id, limit=limit)
    return [PredictionDTO.from_domain(p) for p in predictions]
