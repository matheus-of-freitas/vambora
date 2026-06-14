"""The AWS Lambda inbound adapters: API (Mangum) + scheduled poller.

Both are exercised with stubs so they stay pure unit tests — no DB, no network.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from vambora.adapters.inbound.aws import poller_handler
from vambora.adapters.inbound.aws.api_handler import create_handler
from vambora.adapters.inbound.http.dependencies import Container
from vambora.application.commands.compact_tracking_data import CompactResult
from vambora.application.commands.ingest_vehicle_positions import IngestResult
from vambora.shared.config import Settings

pytestmark = pytest.mark.unit


def _settings(**kw: Any) -> Settings:
    base = {"environment": "local", "routing_enabled": True}
    base.update(kw)
    return Settings.model_construct(**base)


class _FakeResult:
    def scalar_one(self) -> int:
        return 1


class _FakeConn:
    async def execute(self, *args: Any, **kwargs: Any) -> _FakeResult:
        return _FakeResult()


class _FakeDBCtx:
    async def __aenter__(self) -> _FakeConn:
        return _FakeConn()

    async def __aexit__(self, *args: Any) -> bool:
        return False


class _FakeDB:
    def connection(self) -> _FakeDBCtx:
        return _FakeDBCtx()

    async def dispose(self) -> None: ...


class _FakeHttp:
    async def aclose(self) -> None: ...


def _health_container(settings: Settings) -> Container:
    from typing import cast

    return cast(
        Container,
        type("_C", (), {"settings": settings, "db": _FakeDB(), "http_client": _FakeHttp()})(),
    )


def _http_event(path: str) -> dict[str, Any]:
    """A minimal API Gateway v2 (function URL) request payload."""
    return {
        "version": "2.0",
        "rawPath": path,
        "rawQueryString": "",
        "headers": {"host": "example.lambda-url.sa-east-1.on.aws"},
        "requestContext": {
            "http": {"method": "GET", "path": path, "sourceIp": "127.0.0.1"},
        },
        "isBase64Encoded": False,
    }


def test_api_handler_serves_health() -> None:
    settings = _settings()
    handler = create_handler(settings, container=_health_container(settings))
    response = handler(_http_event("/health"), None)
    assert response["statusCode"] == 200
    assert '"ok":true' in response["body"]


class _StubContainer:
    """Stand-in for Container exposing only what run_once touches."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.ingest_calls = 0
        self.evaluate_calls = 0
        self.compact_calls = 0

    async def ingest(self) -> IngestResult:
        self.ingest_calls += 1
        return IngestResult(fetched=3, persisted=2)

    async def evaluate_alerts(self) -> int:
        self.evaluate_calls += 1
        return 1

    async def compact_tracking_data(self) -> CompactResult:
        self.compact_calls += 1
        return CompactResult(rolled_up=4, purged=5, skipped=False)


async def test_poller_run_once_polls_n_times_and_evaluates() -> None:
    container = _StubContainer(_settings(polls_per_invocation=2))
    # minute not divisible by 5 → no compaction this pass.
    await poller_handler.run_once(container, now=datetime(2026, 6, 14, 12, 3, tzinfo=UTC))  # type: ignore[arg-type]
    assert container.ingest_calls == 2
    assert container.evaluate_calls == 1
    assert container.compact_calls == 0


async def test_poller_run_once_compacts_on_fifth_minute() -> None:
    container = _StubContainer(_settings(polls_per_invocation=1))
    await poller_handler.run_once(container, now=datetime(2026, 6, 14, 12, 5, tzinfo=UTC))  # type: ignore[arg-type]
    assert container.ingest_calls == 1
    assert container.compact_calls == 1
