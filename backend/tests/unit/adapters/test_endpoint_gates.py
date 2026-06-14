"""Production gates added for the serverless deployment: trip planning returns
503 when routing is disabled, and /admin/* requires a token off-local.

These ride the real FastAPI app via TestClient but inject a stub container, so
no database or OTP is touched — the gates short-circuit before any port call.
"""

from __future__ import annotations

from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from vambora.adapters.inbound.http.app import create_app
from vambora.adapters.inbound.http.dependencies import Container
from vambora.shared.config import Settings

pytestmark = pytest.mark.unit


class _StubDB:
    async def dispose(self) -> None: ...


class _StubHttp:
    async def aclose(self) -> None: ...


def _client(**settings_kw: Any) -> TestClient:
    settings = Settings.model_construct(cors_allow_origins="", **settings_kw)
    stub = cast(Container, _StubContainer(settings))
    return TestClient(create_app(settings, container=stub))


class _StubContainer:
    """Only the attributes the lifespan teardown and gated endpoints touch."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db = _StubDB()
        self.http_client = _StubHttp()


def test_trip_plan_returns_503_when_routing_disabled() -> None:
    with _client(environment="production", routing_enabled=False) as client:
        resp = client.post(
            "/trips/plan",
            json={
                "origin": {"lat": -22.9, "lon": -43.2},
                "destination": {"lat": -22.8, "lon": -43.1},
            },
        )
    assert resp.status_code == 503


def test_admin_disabled_when_token_unset_off_local() -> None:
    with _client(environment="production", admin_token="") as client:
        assert client.post("/admin/catalog/import").status_code == 503


def test_admin_forbidden_with_wrong_token() -> None:
    with _client(environment="production", admin_token="secret") as client:
        resp = client.post("/admin/catalog/import", headers={"X-Admin-Token": "nope"})
    assert resp.status_code == 403
