from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from itertools import pairwise

from vambora.domain.shared.types import Coordinate


class TravelMode(StrEnum):
    """The subset of OTP modes Rio's network actually produces, plus a
    catch-all so an unexpected upstream mode never breaks a plan."""

    WALK = "WALK"
    BUS = "BUS"
    RAIL = "RAIL"
    SUBWAY = "SUBWAY"
    TRAM = "TRAM"
    FERRY = "FERRY"
    TRANSIT = "TRANSIT"

    @classmethod
    def parse(cls, raw: str) -> TravelMode:
        try:
            return cls(raw.upper())
        except ValueError:
            return cls.TRANSIT


@dataclass(frozen=True, slots=True)
class Leg:
    """One continuous segment of a trip in a single mode."""

    mode: TravelMode
    start_time: datetime
    end_time: datetime
    distance_m: float
    from_name: str
    from_coordinate: Coordinate
    to_name: str
    to_coordinate: Coordinate
    geometry: tuple[Coordinate, ...]
    route_short_name: str | None = None
    route_long_name: str | None = None
    headsign: str | None = None
    # OTP: this transit leg continues on the SAME physical vehicle as the
    # previous transit leg (through-routed) — i.e. not a real transfer.
    interline: bool = False

    @property
    def duration_s(self) -> int:
        return int((self.end_time - self.start_time).total_seconds())

    @property
    def is_transit(self) -> bool:
        return self.mode is not TravelMode.WALK


class ConnectionKind(StrEnum):
    # Same vehicle through-routed — the rider never gets off. No transfer risk.
    INTERLINE = "INTERLINE"
    # A real transfer with little slack — risky if the first bus runs late.
    TIGHT = "TIGHT"
    # A real transfer with comfortable slack.
    OK = "OK"


@dataclass(frozen=True, slots=True)
class Connection:
    """The handover between two consecutive transit legs.

    Rio's open GTFS has no ``transfers.txt``, so OTP can't model timed or
    guaranteed transfers. ``wait_seconds`` is the honest signal we *can*
    derive: the gap between arriving on the first vehicle and the second
    vehicle's departure (it absorbs any walking + waiting in between).
    """

    from_route: str | None
    to_route: str | None
    wait_seconds: int
    kind: ConnectionKind

    @property
    def wait_minutes(self) -> int:
        return max(0, round(self.wait_seconds / 60))


@dataclass(frozen=True, slots=True)
class Itinerary:
    """A complete origin→destination journey: a sequence of legs."""

    start_time: datetime
    end_time: datetime
    walk_distance_m: float
    legs: tuple[Leg, ...]

    @property
    def duration_s(self) -> int:
        return int((self.end_time - self.start_time).total_seconds())

    @property
    def _transit_legs(self) -> list[Leg]:
        return [leg for leg in self.legs if leg.is_transit]

    @property
    def transfers(self) -> int:
        """Real transfers only — interlined (same-vehicle) handovers don't
        count, matching OTP's own ``numberOfTransfers``."""
        return sum(1 for leg in self._transit_legs[1:] if not leg.interline)

    def connections(self, *, tight_below_seconds: int) -> tuple[Connection, ...]:
        """One ``Connection`` per consecutive transit-leg pair, classified by
        slack. Interlined pairs are reported as ``INTERLINE`` (no transfer)."""
        transit = self._transit_legs
        out: list[Connection] = []
        for prev, nxt in pairwise(transit):
            wait = int((nxt.start_time - prev.end_time).total_seconds())
            if nxt.interline:
                kind = ConnectionKind.INTERLINE
            elif wait < tight_below_seconds:
                kind = ConnectionKind.TIGHT
            else:
                kind = ConnectionKind.OK
            out.append(
                Connection(
                    from_route=prev.route_short_name,
                    to_route=nxt.route_short_name,
                    wait_seconds=max(0, wait),
                    kind=kind,
                )
            )
        return tuple(out)
