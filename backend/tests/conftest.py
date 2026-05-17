from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sppo_fixture_path() -> Path:
    return FIXTURES / "sppo_sample.json"


@pytest.fixture
def fake_clock() -> Iterator[FakeClock]:
    return FakeClock()


class FakeClock:
    """Test double for the ``Clock`` port."""

    def __init__(self) -> None:
        from datetime import UTC, datetime

        self._now = datetime(2026, 5, 9, 14, 30, 0, tzinfo=UTC)

    def now(self):  # type: ignore[no-untyped-def]
        return self._now

    def advance(self, seconds: int) -> None:
        from datetime import timedelta

        self._now += timedelta(seconds=seconds)
