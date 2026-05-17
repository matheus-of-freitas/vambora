from __future__ import annotations

import asyncio
import contextlib

import uvicorn

from vambora.adapters.inbound.http.app import create_app
from vambora.adapters.inbound.http.dependencies import build_container
from vambora.adapters.inbound.workers.alert_evaluator import AlertEvaluator
from vambora.adapters.inbound.workers.sppo_poller import SppoPoller
from vambora.shared.config import load_settings
from vambora.shared.logger import configure_logging, get_logger


async def _run() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    log = get_logger("main")

    container = build_container(settings)
    app = create_app(settings, container=container)

    poller = SppoPoller(
        ingest=container.ingest, interval_seconds=settings.sppo_poll_interval_seconds
    )
    evaluator = AlertEvaluator(
        evaluate=container.evaluate_alerts,
        interval_seconds=settings.alert_eval_interval_seconds,
    )

    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=settings.http_host,
            port=settings.http_port,
            log_level=settings.log_level.lower(),
            access_log=False,
        )
    )

    log.info("startup", host=settings.http_host, port=settings.http_port)
    poller_task = asyncio.create_task(poller.run_forever(), name="poller")
    evaluator_task = asyncio.create_task(evaluator.run_forever(), name="alert-evaluator")
    api_task = asyncio.create_task(server.serve(), name="api")
    try:
        done, pending = await asyncio.wait(
            {poller_task, evaluator_task, api_task},
            return_when=asyncio.FIRST_EXCEPTION,
        )
        for task in pending:
            task.cancel()
        for task in done:
            exc = task.exception()
            if exc is not None:
                raise exc
    finally:
        await container.http_client.aclose()
        await container.db.dispose()


def main() -> None:
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(_run())


if __name__ == "__main__":
    main()
