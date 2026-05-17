from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vambora.adapters.inbound.http.dependencies import Container, build_container
from vambora.adapters.inbound.http.routers import (
    admin,
    alerts,
    health,
    lines,
    snapshots,
    stops,
    trips,
    vehicles,
)
from vambora.shared.config import Settings


def create_app(settings: Settings, *, container: Container | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        c = container if container is not None else build_container(settings)
        app.state.container = c
        try:
            yield
        finally:
            await c.http_client.aclose()
            await c.db.dispose()

    app = FastAPI(title="Vambora API", version="0.1.0", lifespan=lifespan)
    # Local dev: web runs on a sibling port (3000/3001) — allow any origin.
    # Non-local: explicit allowlist from CORS_ALLOW_ORIGINS (e.g. the
    # Cloudflare Pages *.pages.dev URL) so a deploy works without a domain.
    # See plan.md "Appendix: Deployment (domain-deferred)".
    app.add_middleware(
        CORSMiddleware,
        allow_origins=(
            ["*"] if settings.environment == "local" else settings.cors_origins_list
        ),
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(vehicles.router)
    app.include_router(stops.router)
    app.include_router(lines.router)
    app.include_router(trips.router)
    app.include_router(snapshots.router)
    app.include_router(alerts.router)
    app.include_router(admin.router)
    return app
