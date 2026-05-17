import pytest

from vambora.adapters.outbound.providers.gtfs_loader import _hms_to_seconds

pytestmark = pytest.mark.unit


def test_hms_zero() -> None:
    assert _hms_to_seconds("00:00:00") == 0


def test_hms_basic() -> None:
    assert _hms_to_seconds("12:34:56") == 12 * 3600 + 34 * 60 + 56


def test_hms_past_midnight() -> None:
    """GTFS allows arrival_time > 24:00:00 for service that crosses midnight."""
    assert _hms_to_seconds("25:30:00") == 25 * 3600 + 30 * 60
