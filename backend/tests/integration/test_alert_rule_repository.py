"""Integration coverage for the alert-rules repository (plan.md decision #4).

The SQL + the `uuid` validation/`CAST(:id AS uuid)` paths were only exercised
via fakes in unit tests. This pins them against a real DB: round-trip,
device scoping + ordering, the cooldown timestamp, delete semantics, and that
a malformed rule id degrades gracefully (no 500) rather than throwing.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from vambora.adapters.outbound.persistence.repositories.alert_rules import (
    PostgresAlertRuleRepository,
)

pytestmark = pytest.mark.integration


async def test_add_round_trips_with_uuid_and_created_at(db) -> None:  # type: ignore[no-untyped-def]
    repo = PostgresAlertRuleRepository(db)
    rule = await repo.add(
        device_id="dev-A",
        line_short_name="639",
        stop_id="S1",
        threshold_minutes=5,
    )
    assert rule.id  # a real uuid string
    assert "-" in rule.id
    assert rule.device_id == "dev-A"
    assert rule.line_short_name == "639"
    assert rule.stop_id == "S1"
    assert rule.threshold_minutes == 5
    assert rule.created_at.tzinfo is not None
    assert rule.last_triggered_at is None


async def test_list_for_device_scopes_and_all_rules(db) -> None:  # type: ignore[no-untyped-def]
    repo = PostgresAlertRuleRepository(db)
    await repo.add(device_id="A", line_short_name="639", stop_id="S1", threshold_minutes=5)
    await repo.add(device_id="A", line_short_name="100", stop_id="S2", threshold_minutes=10)
    await repo.add(device_id="B", line_short_name="485", stop_id="S3", threshold_minutes=3)

    a_rules = await repo.list_for_device("A")
    assert {r.line_short_name for r in a_rules} == {"639", "100"}
    assert all(r.device_id == "A" for r in a_rules)
    # Ordered newest-first.
    assert a_rules[0].created_at >= a_rules[-1].created_at

    b_rules = await repo.list_for_device("B")
    assert [r.line_short_name for r in b_rules] == ["485"]
    assert len(await repo.all_rules()) == 3


async def test_mark_triggered_sets_last_triggered_at(db) -> None:  # type: ignore[no-untyped-def]
    repo = PostgresAlertRuleRepository(db)
    rule = await repo.add(
        device_id="A", line_short_name="639", stop_id="S1", threshold_minutes=5
    )
    when = datetime(2026, 5, 17, 12, 0, tzinfo=UTC)
    await repo.mark_triggered(rule.id, when)

    refreshed = (await repo.list_for_device("A"))[0]
    assert refreshed.last_triggered_at is not None
    assert refreshed.last_triggered_at == when


async def test_delete_returns_true_then_false(db) -> None:  # type: ignore[no-untyped-def]
    repo = PostgresAlertRuleRepository(db)
    rule = await repo.add(
        device_id="A", line_short_name="639", stop_id="S1", threshold_minutes=5
    )
    assert await repo.delete(rule.id) is True
    assert await repo.delete(rule.id) is False  # already gone
    assert await repo.list_for_device("A") == []


async def test_malformed_uuid_degrades_gracefully(db) -> None:  # type: ignore[no-untyped-def]
    repo = PostgresAlertRuleRepository(db)
    # No exception (would surface as a 500): invalid uuid → False / no-op.
    assert await repo.delete("not-a-uuid") is False
    await repo.mark_triggered("also-not-a-uuid", datetime.now(UTC))  # no raise
