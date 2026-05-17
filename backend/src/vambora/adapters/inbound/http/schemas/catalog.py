from __future__ import annotations

from pydantic import BaseModel

from vambora.domain.catalog import Route, ScheduledArrival, Stop


class StopDTO(BaseModel):
    stop_id: str
    code: str | None
    name: str
    latitude: float
    longitude: float
    parent_station: str | None
    wheelchair_boarding: int | None

    @classmethod
    def from_domain(cls, s: Stop) -> StopDTO:
        return cls(
            stop_id=s.stop_id,
            code=s.code,
            name=s.name,
            latitude=s.coordinate.latitude,
            longitude=s.coordinate.longitude,
            parent_station=s.parent_station,
            wheelchair_boarding=s.wheelchair_boarding,
        )


class RouteDTO(BaseModel):
    route_id: str
    agency_id: str
    short_name: str
    long_name: str
    route_type: int
    color: str | None
    text_color: str | None

    @classmethod
    def from_domain(cls, r: Route) -> RouteDTO:
        return cls(
            route_id=r.route_id,
            agency_id=r.agency_id,
            short_name=r.short_name,
            long_name=r.long_name,
            route_type=r.route_type,
            color=r.color,
            text_color=r.text_color,
        )


class ImportResultDTO(BaseModel):
    feed_version: str
    agencies: int
    routes: int
    stops: int


class ArrivalDTO(BaseModel):
    arrival_seconds: int
    arrival_time: str  # HH:MM rendering for client convenience
    trip_id: str
    headsign: str | None
    route_id: str
    route_short_name: str
    route_long_name: str
    route_color: str | None

    @classmethod
    def from_domain(cls, a: ScheduledArrival) -> ArrivalDTO:
        # arrival_seconds may exceed 86400 for past-midnight schedule entries.
        total = a.arrival_seconds
        h, rem = divmod(total, 3600)
        m, _ = divmod(rem, 60)
        return cls(
            arrival_seconds=a.arrival_seconds,
            arrival_time=f"{h:02d}:{m:02d}",
            trip_id=a.trip_id,
            headsign=a.headsign,
            route_id=a.route_id,
            route_short_name=a.route_short_name,
            route_long_name=a.route_long_name,
            route_color=a.route_color,
        )
