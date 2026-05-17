"""OpenTripPlanner v2 adapter (GTFS GraphQL API at ``/otp/gtfs/v1``).

OTP returns leg/itinerary times as epoch-millis ``Long``s and leg geometry as a
Google-encoded polyline (precision 5). OTP interprets ``date``/``time`` in the
feed's agency timezone, which for Rio is America/Sao_Paulo (UTC-3, no DST), so
we format ``depart_at`` in BRT before sending it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import httpx
from pydantic import BaseModel, Field

from vambora.domain.routing import Itinerary, Leg, TravelMode
from vambora.domain.shared.types import Coordinate
from vambora.shared.errors import ProviderError
from vambora.shared.logger import get_logger

BRT = timezone(timedelta(hours=-3), name="America/Sao_Paulo")
_HTTP_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)

log = get_logger("otp")

_PLAN_QUERY = """
query Plan($from: InputCoordinates!, $to: InputCoordinates!,
           $date: String!, $time: String!, $num: Int!) {
  plan(
    from: $from
    to: $to
    date: $date
    time: $time
    numItineraries: $num
    transportModes: [{mode: WALK}, {mode: TRANSIT}]
  ) {
    itineraries {
      startTime
      endTime
      walkDistance
      legs {
        mode
        startTime
        endTime
        distance
        from { name lat lon }
        to { name lat lon }
        route { shortName longName }
        trip { tripHeadsign }
        interlineWithPreviousLeg
        legGeometry { points }
      }
    }
    routingErrors { code description }
  }
}
"""


def decode_polyline(encoded: str) -> tuple[Coordinate, ...]:
    """Decode a Google-encoded polyline (precision 5) into coordinates."""
    coords: list[Coordinate] = []
    index = lat = lng = 0
    length = len(encoded)
    while index < length:
        for axis in (0, 1):
            shift = result = 0
            while True:
                byte = ord(encoded[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if byte < 0x20:
                    break
            delta = ~(result >> 1) if result & 1 else (result >> 1)
            if axis == 0:
                lat += delta
            else:
                lng += delta
        coords.append(Coordinate(latitude=lat / 1e5, longitude=lng / 1e5))
    return tuple(coords)


def _ms_to_dt(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=UTC)


class _Place(BaseModel):
    name: str | None = None
    lat: float
    lon: float


class _Route(BaseModel):
    short_name: str | None = Field(default=None, alias="shortName")
    long_name: str | None = Field(default=None, alias="longName")


class _Trip(BaseModel):
    headsign: str | None = Field(default=None, alias="tripHeadsign")


class _Geometry(BaseModel):
    points: str | None = None


class _Leg(BaseModel):
    mode: str
    start_time: int = Field(alias="startTime")
    end_time: int = Field(alias="endTime")
    distance: float
    frm: _Place = Field(alias="from")
    to: _Place
    route: _Route | None = None
    trip: _Trip | None = None
    interline: bool = Field(default=False, alias="interlineWithPreviousLeg")
    leg_geometry: _Geometry | None = Field(default=None, alias="legGeometry")

    def to_domain(self) -> Leg:
        points = self.leg_geometry.points if self.leg_geometry else None
        return Leg(
            mode=TravelMode.parse(self.mode),
            start_time=_ms_to_dt(self.start_time),
            end_time=_ms_to_dt(self.end_time),
            distance_m=self.distance,
            from_name=self.frm.name or "",
            from_coordinate=Coordinate(latitude=self.frm.lat, longitude=self.frm.lon),
            to_name=self.to.name or "",
            to_coordinate=Coordinate(latitude=self.to.lat, longitude=self.to.lon),
            geometry=decode_polyline(points) if points else (),
            route_short_name=self.route.short_name if self.route else None,
            route_long_name=self.route.long_name if self.route else None,
            headsign=self.trip.headsign if self.trip else None,
            interline=self.interline,
        )


class _Itinerary(BaseModel):
    start_time: int = Field(alias="startTime")
    end_time: int = Field(alias="endTime")
    walk_distance: float = Field(default=0.0, alias="walkDistance")
    legs: list[_Leg] = Field(default_factory=list)

    def to_domain(self) -> Itinerary:
        return Itinerary(
            start_time=_ms_to_dt(self.start_time),
            end_time=_ms_to_dt(self.end_time),
            walk_distance_m=self.walk_distance,
            legs=tuple(leg.to_domain() for leg in self.legs),
        )


class _RoutingError(BaseModel):
    code: str | None = None
    description: str | None = None


class _Plan(BaseModel):
    itineraries: list[_Itinerary] = Field(default_factory=list)
    routing_errors: list[_RoutingError] = Field(default_factory=list, alias="routingErrors")


class OtpClient:
    def __init__(self, *, base_url: str, http_client: httpx.AsyncClient) -> None:
        self._url = base_url.rstrip("/") + "/otp/gtfs/v1"
        self._http = http_client

    async def plan_trip(
        self,
        *,
        origin: Coordinate,
        destination: Coordinate,
        depart_at: datetime,
        max_itineraries: int = 3,
    ) -> list[Itinerary]:
        local = depart_at.astimezone(BRT)
        variables = {
            "from": {"lat": origin.latitude, "lon": origin.longitude},
            "to": {"lat": destination.latitude, "lon": destination.longitude},
            "date": local.strftime("%Y-%m-%d"),
            "time": local.strftime("%H:%M:%S"),
            "num": max_itineraries,
        }
        try:
            response = await self._http.post(
                self._url,
                json={"query": _PLAN_QUERY, "variables": variables},
                timeout=_HTTP_TIMEOUT,
            )
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"otp plan failed: {exc}") from exc
        except ValueError as exc:
            raise ProviderError("otp response was not valid JSON") from exc

        if not isinstance(body, dict):
            raise ProviderError("otp response was not a JSON object")
        if body.get("errors"):
            raise ProviderError(f"otp graphql errors: {body['errors']}")
        raw_plan = (body.get("data") or {}).get("plan")
        if not raw_plan:
            return []
        plan = _Plan.model_validate(raw_plan)
        if plan.routing_errors and not plan.itineraries:
            log.info(
                "otp.no_route",
                routing_errors=[e.model_dump() for e in plan.routing_errors],
            )
            return []
        return [it.to_domain() for it in plan.itineraries]
