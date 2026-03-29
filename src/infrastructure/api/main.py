"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from src.api.middleware.audit_middleware import AuditMiddleware
from src.api.routes.admin import router as admin_router
from src.api.routes.feedback import router as feedback_router
from src.application.graphs.rag_graph import build_rag_graph, create_checkpointer
from src.config.settings import settings
from src.infrastructure.api.middleware import (
    LoggingMiddleware,
    RateLimiterMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)
from src.infrastructure.api.v1.auth import router as auth_router
from src.infrastructure.api.v1.chat import router as chat_router
from src.infrastructure.api.v1.documents import router as documents_router
from src.infrastructure.api.v1.health import router as health_router
from src.infrastructure.database.session import async_session_maker, engine
from src.infrastructure.observability.langfuse_client import flush_langfuse, get_langfuse
from src.infrastructure.observability.logging_config import configure_logging
from src.shared.exceptions import AppError

# Configure structured logging
configure_logging()
logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage startup/shutdown resources."""
    # Startup: Initialize Langfuse
    get_langfuse()

    # Startup: verify Postgres
    async with async_session_maker() as session:
        await session.execute(text("SELECT 1"))
    logger.info("postgres_connection_verified")

    # Startup: create Redis pool and verify
    redis = Redis.from_url(settings.redis_url.get_secret_value(), decode_responses=True)
    await redis.ping()
    _app.state.redis = redis
    logger.info("redis_connection_verified")

    # Startup: create checkpointer and compile RAG graph
    async with create_checkpointer(settings.database_url.get_secret_value()) as checkpointer:
        _app.state.checkpointer = checkpointer
        _app.state.rag_graph = build_rag_graph(checkpointer=checkpointer)
        logger.info("rag_graph_compiled")

        yield

    # Shutdown
    flush_langfuse()
    await redis.close()
    await engine.dispose()
    logger.info("connections_closed")


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    error_payload: dict[str, Any] = {"code": code, "message": message}
    if details:
        error_payload["details"] = details
    return JSONResponse(
        status_code=status_code,
        content={"data": None, "error": error_payload, "meta": {}},
    )


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error("app_error_5xx: %s [%s] %s details=%s", exc.code, request.method, request.url.path, exc.details)
    else:
        logger.warning("app_error: %s [%s] %s", exc.code, request.method, request.url.path)
    return _error_response(exc.status_code, exc.code, exc.message, exc.details)


async def _http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code_map: dict[int, str] = {
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    message = str(exc.detail) if exc.detail else "HTTP error"
    return _error_response(exc.status_code, code, message)


async def _validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    field_errors = []
    for err in exc.errors():
        loc = " -> ".join(str(part) for part in err.get("loc", []))
        field_errors.append({"field": loc, "message": err.get("msg", "")})
    return _error_response(
        422,
        "VALIDATION_ERROR",
        "Request validation failed.",
        {"fields": field_errors},
    )


async def _unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    details: dict[str, Any] | None = None
    if settings.debug:
        details = {"type": type(exc).__name__, "message": str(exc)}
    return _error_response(500, "INTERNAL_ERROR", "An unexpected error occurred.", details)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Enterprise AI Platform",
        version=settings.app_version,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
        lifespan=lifespan,
    )

    # ----- Middleware stack -----
    # Starlette processes middleware in reverse registration order (last
    # registered = outermost).  We register from innermost to outermost so
    # the execution order is:
    #   CORS → TrustedHost → RateLimiter → RequestSizeLimit → RequestLogging → SecurityHeaders
    #
    # CORSMiddleware (innermost — runs first on request, last on response)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time"],
    )

    # TrustedHostMiddleware — prevents Host header injection
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_host_list,
    )

    # Rate limiting — Redis sliding window (pure ASGI, SSE-safe)
    application.add_middleware(RateLimiterMiddleware)

    # Request size limit (default 10 MB)
    application.add_middleware(
        RequestSizeLimitMiddleware,
        max_size=settings.max_request_size_bytes,
    )

    # Access logging (method, path, status, duration, user_id)
    application.add_middleware(LoggingMiddleware)

    # Audit logging for sensitive endpoints
    application.add_middleware(AuditMiddleware)

    # Security headers (outermost — guaranteed to run on every response)
    application.add_middleware(SecurityHeadersMiddleware)

    # Exception handlers
    application.add_exception_handler(AppError, _app_error_handler)  # type: ignore[arg-type]
    application.add_exception_handler(StarletteHTTPException, _http_exception_handler)  # type: ignore[arg-type]
    application.add_exception_handler(RequestValidationError, _validation_error_handler)  # type: ignore[arg-type]
    application.add_exception_handler(Exception, _unhandled_exception_handler)

    # Routers
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(chat_router)
    application.include_router(documents_router)
    application.include_router(admin_router, prefix="/api/v1")
    application.include_router(feedback_router, prefix="/api/v1")

    return application


app = create_app()
