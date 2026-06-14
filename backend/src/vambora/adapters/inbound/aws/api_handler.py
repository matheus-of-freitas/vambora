"""Lambda handler for the FastAPI app behind a function URL.

A function URL delivers API Gateway v2 (HTTP API) payloads, which Mangum
translates to/from ASGI. ``lifespan="auto"`` lets the app's existing lifespan
build the container on cold start and dispose it when the sandbox shuts down.
"""

from __future__ import annotations

from typing import Any

from mangum import Mangum
from mangum.types import LambdaContext

from vambora.adapters.inbound.http.app import create_app
from vambora.adapters.inbound.http.dependencies import Container
from vambora.shared.config import Settings, load_settings
from vambora.shared.logger import configure_logging


def create_handler(settings: Settings, *, container: Container | None = None) -> Mangum:
    configure_logging(settings.log_level)
    app = create_app(settings, container=container)
    return Mangum(app, lifespan="auto")


# Built lazily on the first invocation (cold start) and reused while warm.
# Lazy so importing this module doesn't require the full runtime env — keeps it
# importable in tests and anywhere settings aren't configured.
_handler: Mangum | None = None


def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    global _handler
    if _handler is None:
        _handler = create_handler(load_settings())
    return _handler(event, context)
