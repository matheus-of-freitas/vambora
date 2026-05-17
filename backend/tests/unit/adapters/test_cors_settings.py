from __future__ import annotations

import pytest
from starlette.middleware.cors import CORSMiddleware

from vambora.adapters.inbound.http.app import create_app
from vambora.shared.config import Settings

pytestmark = pytest.mark.unit


def _settings(*, environment: str, cors: str) -> Settings:
    return Settings.model_construct(environment=environment, cors_allow_origins=cors)


def test_cors_origins_list_parses_trims_and_drops_empties() -> None:
    s = _settings(
        environment="production",
        cors=" https://a.pages.dev , ,https://b.example , ",
    )
    assert s.cors_origins_list == ["https://a.pages.dev", "https://b.example"]


def _cors_allow_origins(settings: Settings) -> list[str]:
    app = create_app(settings)
    for mw in app.user_middleware:
        if mw.cls is CORSMiddleware:
            return list(mw.kwargs["allow_origins"])
    raise AssertionError("CORSMiddleware not installed")


def test_local_allows_any_origin() -> None:
    assert _cors_allow_origins(_settings(environment="local", cors="")) == ["*"]


def test_non_local_uses_explicit_allowlist() -> None:
    settings = _settings(
        environment="production",
        cors="https://vambora-web.pages.dev",
    )
    assert _cors_allow_origins(settings) == ["https://vambora-web.pages.dev"]


def test_non_local_without_origins_is_empty_not_wildcard() -> None:
    # The pre-fix bug was a hard-coded [] here; now it's an *explicit*
    # (still-empty) allowlist driven by config, not a wildcard leak.
    assert _cors_allow_origins(_settings(environment="production", cors="")) == []
