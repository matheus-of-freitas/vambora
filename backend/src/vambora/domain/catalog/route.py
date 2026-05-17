from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from vambora.domain.shared.errors import InvariantViolation


class RouteType(IntEnum):
    """GTFS route_type values we care about. Includes the extended (700-series)
    ones used by the Rio feed for buses."""

    TRAM = 0  # VLT
    SUBWAY = 1
    RAIL = 2
    BUS = 3
    BUS_EXTENDED = 700


@dataclass(frozen=True, slots=True)
class Route:
    route_id: str
    agency_id: str
    short_name: str
    long_name: str
    route_type: int
    color: str | None
    text_color: str | None

    def __post_init__(self) -> None:
        if not self.route_id:
            raise InvariantViolation("route_id required")
        if not self.agency_id:
            raise InvariantViolation("agency_id required")
        if not self.short_name:
            raise InvariantViolation("route short_name required")
