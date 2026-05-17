from __future__ import annotations

from datetime import datetime
from typing import Protocol

from vambora.domain.tracking import VehiclePosition


class VehicleTrackingProvider(Protocol):
    """Upstream feed of real-time vehicle positions (e.g. SPPO)."""

    async def fetch(self, *, since: datetime, until: datetime) -> list[VehiclePosition]:
        """Return positions whose server-arrival time is within the window."""
        ...
