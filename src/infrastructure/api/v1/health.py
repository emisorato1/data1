"""Health check endpoints for liveness and readiness probes."""

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.infrastructure.api.dependencies import get_db, get_redis

router = APIRouter(tags=["health"])


def _envelope(data: Any, status_code: int = 200) -> JSONResponse:
    """Wrap response in standard {data, error, meta} envelope."""
    return JSONResponse(
        status_code=status_code,
        content={"data": data, "error": None, "meta": {}},
    )


@router.get("/health")
async def liveness() -> JSONResponse:
    """Liveness probe — always returns ok if the process is running."""
    return _envelope({"status": "ok", "version": settings.app_version})


@router.get("/health/ready")
async def readiness(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),  # type: ignore[type-arg]
) -> JSONResponse:
    """Readiness probe — verifies Postgres and Redis connectivity."""
    checks: dict[str, str] = {}
    status_code = 200

    # Postgres
    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        checks["postgres"] = "unavailable"
        status_code = 503

    # Redis
    try:
        pong: bool = await redis.ping()  # type: ignore[misc]
        checks["redis"] = "ok" if pong else "unavailable"
    except Exception:
        checks["redis"] = "unavailable"
        status_code = 503

    status = "ready" if status_code == 200 else "degraded"
    return _envelope({"status": status, "checks": checks}, status_code=status_code)
