from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from vambora.adapters.inbound.http.dependencies import Container, container
from vambora.adapters.inbound.http.schemas.routing import ItineraryDTO, PlanTripRequest
from vambora.domain.shared.types import Coordinate

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("/plan", response_model=list[ItineraryDTO])
async def plan_trip(
    body: PlanTripRequest,
    c: Container = Depends(container),
) -> list[ItineraryDTO]:
    # Trip planning needs OpenTripPlanner, which isn't part of the serverless
    # deployment. Return a clear 503 rather than failing against an
    # unreachable OTP. See plan.md decision #15.
    if not c.settings.routing_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="trip planning is temporarily unavailable",
        )
    itineraries = await c.plan_trip(
        origin=Coordinate(latitude=body.origin.lat, longitude=body.origin.lon),
        destination=Coordinate(latitude=body.destination.lat, longitude=body.destination.lon),
        depart_at=body.depart_at,
        max_itineraries=body.max_itineraries,
    )
    tight = c.settings.routing_tight_transfer_seconds
    return [ItineraryDTO.from_domain(it, tight_below_seconds=tight) for it in itineraries]
