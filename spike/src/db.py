from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from src.config import settings

_engine: AsyncEngine = create_async_engine(settings.database_url, pool_size=5, max_overflow=5)


def engine() -> AsyncEngine:
    return _engine


@asynccontextmanager
async def connection() -> AsyncIterator[AsyncConnection]:
    async with _engine.begin() as conn:
        yield conn


async def dispose() -> None:
    await _engine.dispose()
