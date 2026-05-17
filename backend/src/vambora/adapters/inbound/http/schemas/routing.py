from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from vambora.domain.routing import Connection, Itinerary, Leg


class CoordinateDTO(BaseModel):
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)


class PlanTripRequest(BaseModel):
    origin: CoordinateDTO
    destination: CoordinateDTO
    depart_at: datetime | None = None
    max_itineraries: int = Field(default=3, ge=1, le=6)


class LegDTO(BaseModel):
    mode: str
    start_time: datetime
    end_time: datetime
    duration_s: int
    distance_m: float
    from_name: str
    from_lat: float
    from_lon: float
    to_name: str
    to_lat: float
    to_lon: float
    route_short_name: str | None
    route_long_name: str | None
    headsign: str | None
    interline: bool
    geometry: list[list[float]]

    @classmethod
    def from_domain(cls, leg: Leg) -> LegDTO:
        return cls(
            mode=leg.mode.value,
            start_time=leg.start_time,
            end_time=leg.end_time,
            duration_s=leg.duration_s,
            distance_m=leg.distance_m,
            from_name=leg.from_name,
            from_lat=leg.from_coordinate.latitude,
            from_lon=leg.from_coordinate.longitude,
            to_name=leg.to_name,
            to_lat=leg.to_coordinate.latitude,
            to_lon=leg.to_coordinate.longitude,
            route_short_name=leg.route_short_name,
            route_long_name=leg.route_long_name,
            headsign=leg.headsign,
            interline=leg.interline,
            geometry=[[c.longitude, c.latitude] for c in leg.geometry],
        )


class ConnectionDTO(BaseModel):
    from_route: str | None
    to_route: str | None
    wait_seconds: int
    wait_minutes: int
    kind: str  # INTERLINE | TIGHT | OK

    @classmethod
    def from_domain(cls, c: Connection) -> ConnectionDTO:
        return cls(
            from_route=c.from_route,
            to_route=c.to_route,
            wait_seconds=c.wait_seconds,
            wait_minutes=c.wait_minutes,
            kind=c.kind.value,
        )


class ItineraryDTO(BaseModel):
    start_time: datetime
    end_time: datetime
    duration_s: int
    walk_distance_m: float
    transfers: int
    legs: list[LegDTO]
    connections: list[ConnectionDTO]

    @classmethod
    def from_domain(cls, it: Itinerary, *, tight_below_seconds: int) -> ItineraryDTO:
        return cls(
            start_time=it.start_time,
            end_time=it.end_time,
            duration_s=it.duration_s,
            walk_distance_m=it.walk_distance_m,
            transfers=it.transfers,
            legs=[LegDTO.from_domain(leg) for leg in it.legs],
            connections=[
                ConnectionDTO.from_domain(c)
                for c in it.connections(tight_below_seconds=tight_below_seconds)
            ],
        )
