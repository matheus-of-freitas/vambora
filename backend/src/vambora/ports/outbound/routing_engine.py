from __future__ import annotations

from datetime import datetime
from typing import Protocol

from vambora.domain.routing import Itinerary
from vambora.domain.shared.types import Coordinate


class RoutingEngine(Protocol):
    """Multi-modal trip planner. Implemented by the OTP adapter.

    ``depart_at`` is an aware datetime; the engine interprets it in the
    feed's local timezone (America/Sao_Paulo).
    """

    async def plan_trip(
        self,
        *,
        origin: Coordinate,
        destination: Coordinate,
        depart_at: datetime,
        max_itineraries: int = 3,
    ) -> list[Itinerary]: ...
