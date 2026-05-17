from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text

from vambora.adapters.outbound.persistence.unit_of_work import Database
from vambora.domain.alerts import AlertRule


def _valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


class PostgresAlertRuleRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def add(
        self,
        *,
        device_id: str,
        line_short_name: str,
        stop_id: str,
        threshold_minutes: int,
    ) -> AlertRule:
        sql = text(
            """
            INSERT INTO alert_rules
                (device_id, line_short_name, stop_id, threshold_minutes)
            VALUES
                (:device_id, :line_short_name, :stop_id, :threshold_minutes)
            RETURNING id, created_at
            """
        )
        async with self._db.connection() as conn:
            row = (
                await conn.execute(
                    sql,
                    {
                        "device_id": device_id,
                        "line_short_name": line_short_name,
                        "stop_id": stop_id,
                        "threshold_minutes": threshold_minutes,
                    },
                )
            ).one()
        return AlertRule(
            id=str(row._mapping["id"]),
            device_id=device_id,
            line_short_name=line_short_name,
            stop_id=stop_id,
            threshold_minutes=threshold_minutes,
            created_at=_aware(row._mapping["created_at"]),
            last_triggered_at=None,
        )

    async def delete(self, rule_id: str) -> bool:
        if not _valid_uuid(rule_id):
            return False
        sql = text("DELETE FROM alert_rules WHERE id = CAST(:id AS uuid) RETURNING 1")
        async with self._db.connection() as conn:
            result = await conn.execute(sql, {"id": rule_id})
            return result.first() is not None

    async def list_for_device(self, device_id: str) -> list[AlertRule]:
        sql = text(
            """
            SELECT id, device_id, line_short_name, stop_id, threshold_minutes,
                   created_at, last_triggered_at
            FROM alert_rules
            WHERE device_id = :device_id
            ORDER BY created_at DESC
            """
        )
        async with self._db.connection() as conn:
            result = await conn.execute(sql, {"device_id": device_id})
            return [_to_rule(dict(r._mapping)) for r in result]

    async def all_rules(self) -> list[AlertRule]:
        sql = text(
            """
            SELECT id, device_id, line_short_name, stop_id, threshold_minutes,
                   created_at, last_triggered_at
            FROM alert_rules
            """
        )
        async with self._db.connection() as conn:
            result = await conn.execute(sql)
            return [_to_rule(dict(r._mapping)) for r in result]

    async def mark_triggered(self, rule_id: str, at: datetime) -> None:
        if not _valid_uuid(rule_id):
            return
        sql = text(
            "UPDATE alert_rules SET last_triggered_at = :at "
            "WHERE id = CAST(:id AS uuid)"
        )
        async with self._db.connection() as conn:
            await conn.execute(sql, {"id": rule_id, "at": at})


def _to_rule(row: Mapping[str, Any]) -> AlertRule:
    last = row["last_triggered_at"]
    return AlertRule(
        id=str(row["id"]),
        device_id=row["device_id"],
        line_short_name=row["line_short_name"],
        stop_id=row["stop_id"],
        threshold_minutes=int(row["threshold_minutes"]),
        created_at=_aware(row["created_at"]),
        last_triggered_at=_aware(last) if last is not None else None,
    )


def _aware(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    raise TypeError(f"expected datetime, got {type(value).__name__}")
