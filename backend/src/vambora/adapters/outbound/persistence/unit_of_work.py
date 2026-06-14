from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool


class Database:
    """Lightweight wrapper around an ``AsyncEngine``.

    Each ``connection()`` opens a transactional scope (``engine.begin``).
    Repositories receive the open connection; we don't expose Sessions because
    the persistence path uses Core-level statements.

    ``pool_pre_ping`` discards connections that died while idle (Supabase's
    pooler and frozen Lambda sandboxes both leave stale sockets behind);
    ``null_pool`` skips pooling entirely, which is what a Lambda wants since a
    pooled connection can't survive between frozen invocations.
    """

    def __init__(
        self, url: str, *, pool_size: int = 5, null_pool: bool = False
    ) -> None:
        kwargs: dict[str, Any] = {"pool_pre_ping": True}
        if null_pool:
            kwargs["poolclass"] = NullPool
        else:
            kwargs["pool_size"] = pool_size
            kwargs["pool_recycle"] = 300
        self._engine: AsyncEngine = create_async_engine(url, **kwargs)

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[AsyncConnection]:
        async with self._engine.begin() as conn:
            yield conn

    async def dispose(self) -> None:
        await self._engine.dispose()
