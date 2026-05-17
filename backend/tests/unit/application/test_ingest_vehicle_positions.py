from __future__ import annotations

from datetime import UTC, datetime

import pytest

from vambora.application.commands.ingest_vehicle_positions import IngestVehiclePositions
from vambora.domain.shared.types import Coordinate
from vambora.domain.tracking import VehiclePosition

pytestmark = pytest.mark.unit


class _StubProvider:
    def __init__(self, positions: list[VehiclePosition]) -> None:
        self._positions = positions
        self.last_window: tuple[datetime, datetime] | None = None

    async def fetch(self, *, since: datetime, until: datetime) -> list[VehiclePosition]:
        self.last_window = (since, until)
        return self._positions


class _StubRepo:
    def __init__(self, persisted: int) -> None:
        self._persisted = persisted
        self.received: list[VehiclePosition] = []

    async def upsert_many(self, positions: list[VehiclePosition]) -> int:
        self.received = positions
        return self._persisted

    async def latest_per_vehicle(self, **_: object) -> list[VehiclePosition]:
        raise NotImplementedError

    async def history_for(self, *_: object, **__: object) -> list[VehiclePosition]:
        raise NotImplementedError


def _sample(vehicle_id: str = "B11622") -> VehiclePosition:
    ts = datetime(2026, 5, 9, 14, 30, 0, tzinfo=UTC)
    return VehiclePosition(
        vehicle_id=vehicle_id,
        line_id="363",
        recorded_at=ts,
        sent_at=ts,
        received_at=ts,
        coordinate=Coordinate(latitude=-22.9, longitude=-43.2),
        speed_kmh=20.0,
        raw={},
    )


async def test_ingest_persists_fetched_positions(fake_clock) -> None:  # type: ignore[no-untyped-def]
    provider = _StubProvider([_sample("A1"), _sample("A2")])
    repo = _StubRepo(persisted=2)

    ingest = IngestVehiclePositions(
        provider=provider, repository=repo, clock=fake_clock, window_seconds=45
    )

    result = await ingest()

    assert result.fetched == 2
    assert result.persisted == 2
    assert len(repo.received) == 2
    assert provider.last_window is not None
    since, until = provider.last_window
    assert until == fake_clock.now()
    assert (until - since).total_seconds() == 45


async def test_ingest_handles_empty_provider(fake_clock) -> None:  # type: ignore[no-untyped-def]
    provider = _StubProvider([])
    repo = _StubRepo(persisted=0)

    ingest = IngestVehiclePositions(
        provider=provider, repository=repo, clock=fake_clock, window_seconds=45
    )

    result = await ingest()

    assert result.fetched == 0
    assert result.persisted == 0
