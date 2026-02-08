from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.db.deps import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict:
    return {"status": "ok"}


@router.get("/db")
async def health_db(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(text("SELECT 1"))
    return {"database": result.scalar_one()}


@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)) -> dict:
    # Si SELECT 1 funciona, DB OK
    await db.execute(text("SELECT 1"))
    return {"status": "ready", "db": "up", "env": settings.ENV}