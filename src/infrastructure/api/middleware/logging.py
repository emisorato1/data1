import time
import uuid
from collections.abc import Callable
from typing import ClassVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging estructurado de requests usando structlog.
    Inyecta request_id y correlaciona con trace_id de Langfuse.
    """

    SKIP_PATHS: ClassVar[set[str]] = {"/health", "/ready", "/metrics", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)  # type: ignore[no-any-return]

        # Generar o obtener request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Bind context inicial
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
        )

        # Guardar en request.state para uso en otros componentes
        request.state.request_id = request_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)

            # Intentar obtener trace_id de Langfuse si existe en este contexto
            try:
                from langfuse.decorators import langfuse_context

                trace_id = langfuse_context.get_current_trace_id()
                if trace_id:
                    structlog.contextvars.bind_contextvars(trace_id=trace_id)
            except Exception:  # noqa: S110
                # No crítico si langfuse no está instalado o falla la obtención del trace_id
                pass

            duration_ms = (time.perf_counter() - start_time) * 1000

            # Obtener user_id de state (seteado por auth dependency)
            user_id = getattr(request.state, "user_id", "anonymous")
            structlog.contextvars.bind_contextvars(user_id=user_id)

            logger.info(
                "http_request",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                user_id=user_id,
            )

            # Agregar headers de respuesta
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            return response  # type: ignore[no-any-return]

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "http_request_error",
                error=str(e),
                duration_ms=round(duration_ms, 2),
                exc_info=True,
            )
            raise
        finally:
            # Limpiar el contexto al finalizar el request
            structlog.contextvars.clear_contextvars()
