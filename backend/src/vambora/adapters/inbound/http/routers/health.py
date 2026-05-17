from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text

from vambora.adapters.inbound.http.dependencies import Container, container

router = APIRouter()


@router.get("/health")
async def health(c: Container = Depends(container)) -> dict[str, bool]:
    async with c.db.connection() as conn:
        result = await conn.execute(text("SELECT 1"))
        ok = result.scalar_one() == 1
    return {"ok": ok}
