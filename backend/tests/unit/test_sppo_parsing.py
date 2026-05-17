from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from vambora.adapters.outbound.providers.sppo_client import parse_payload

pytestmark = pytest.mark.unit


def test_parses_real_sppo_fixture(sppo_fixture_path: Path) -> None:
    payload = json.loads(sppo_fixture_path.read_text())
    positions = parse_payload(payload)

    assert len(positions) == 2

    first = positions[0]
    assert first.vehicle_id == "B11622"
    assert first.line_id == "363"
    # Comma decimal -> float
    assert first.coordinate.latitude == pytest.approx(-22.90842)
    assert first.coordinate.longitude == pytest.approx(-43.23829)
    # ms-epoch string -> aware datetime
    assert first.recorded_at == datetime.fromtimestamp(1778261832, tz=UTC)
    assert first.sent_at == datetime.fromtimestamp(1778261843, tz=UTC)
    assert first.received_at == datetime.fromtimestamp(1778261874, tz=UTC)
    assert first.speed_kmh == 5.0
    assert first.raw == payload[0]


def test_parser_skips_malformed_rows(sppo_fixture_path: Path) -> None:
    good = json.loads(sppo_fixture_path.read_text())
    bad = [{"ordem": "X1"}, {"latitude": "-22,9"}]  # missing required keys
    positions = parse_payload(bad + good)
    assert len(positions) == 2
