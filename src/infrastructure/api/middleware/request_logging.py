"""Request logging middleware — structured access log.

Emits one log line per HTTP request via the ``rag_system.access`` stdlib
logger so that the output is available to any standard handler (file,
stdout, external collector).

Headers injected into every response:
  - ``X-Request-ID``:  Correlation identifier (echoed from the incoming
    header or generated as a UUID-4).
  - ``X-Response-Time``: Wall-clock duration formatted as ``<float>ms``.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from collections.abc import Callable

    from starlette.requests import Request
    from starlette.responses import Response

access_logger = logging.getLogger("rag_system.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Lightweight access-log middleware using stdlib logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        user_id = getattr(request.state, "user_id", "anonymous")

        access_logger.info(
            "http_request method=%s path=%s status=%s duration_ms=%.2f user_id=%s request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            user_id,
            request_id,
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response  # type: ignore[no-any-return]
