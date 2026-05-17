from __future__ import annotations

import asyncio
import logging
import sys

import structlog
import uvicorn

from src import db, poller
from src.api import app
from src.config import settings


def _configure_logging() -> None:
    logging.basicConfig(level=settings.log_level, stream=sys.stdout, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping()[settings.log_level.upper()]
        ),
    )


async def _run() -> None:
    _configure_logging()
    config = uvicorn.Config(
        app,
        host=settings.http_host,
        port=settings.http_port,
        log_level=settings.log_level.lower(),
        access_log=False,
    )
    server = uvicorn.Server(config)
    poller_task = asyncio.create_task(poller.run_forever(), name="poller")
    api_task = asyncio.create_task(server.serve(), name="api")
    try:
        done, pending = await asyncio.wait(
            {poller_task, api_task}, return_when=asyncio.FIRST_EXCEPTION
        )
        for task in pending:
            task.cancel()
        for task in done:
            exc = task.exception()
            if exc is not None:
                raise exc
    finally:
        await db.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass
