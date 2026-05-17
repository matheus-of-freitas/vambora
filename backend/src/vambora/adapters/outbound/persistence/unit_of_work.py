from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine


class Database:
    """Lightweight wrapper around an ``AsyncEngine``.

    Each ``connection()`` opens a transactional scope (``engine.begin``).
    Repositories receive the open connection; we don't expose Sessions because
    the persistence path uses Core-level statements.
    """

    def __init__(self, url: str, *, pool_size: int = 5) -> None:
        self._engine: AsyncEngine = create_async_engine(url, pool_size=pool_size)

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[AsyncConnection]:
        async with self._engine.begin() as conn:
            yield conn

    async def dispose(self) -> None:
        await self._engine.dispose()
