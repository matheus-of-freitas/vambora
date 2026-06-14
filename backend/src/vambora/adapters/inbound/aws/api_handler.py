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


# Built once per cold start, reused across warm invocations.
_handler = create_handler(load_settings())


def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    return _handler(event, context)
