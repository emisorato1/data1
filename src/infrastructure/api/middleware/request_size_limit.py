"""Request body size limit middleware.

Rejects requests whose ``Content-Length`` exceeds a configurable threshold
(default 10 MB) **before** the body is read, returning HTTP 413.

.. warning:: TODO(T2-S3-01): Rewrite as pure ASGI middleware before SSE
   streaming is implemented.  ``BaseHTTPMiddleware`` buffers the entire
   response body, which will break streaming endpoints.

.. warning:: TODO: Only checks the ``Content-Length`` header.  Chunked
   transfer-encoding sends no ``Content-Length``, bypassing this check.
   Address when rewriting as pure ASGI middleware.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# 10 MB expressed in bytes
DEFAULT_MAX_SIZE: int = 10 * 1024 * 1024  # 10_485_760


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Return 413 Payload Too Large when Content-Length exceeds *max_size*."""

    def __init__(self, app, max_size: int = DEFAULT_MAX_SIZE) -> None:
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                length = int(content_length)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "data": None,
                        "error": {
                            "code": "INVALID_CONTENT_LENGTH",
                            "message": "Invalid Content-Length header.",
                        },
                        "meta": {},
                    },
                )

            if length > self.max_size:
                return JSONResponse(
                    status_code=413,
                    content={
                        "data": None,
                        "error": {
                            "code": "PAYLOAD_TOO_LARGE",
                            "message": (f"Request body exceeds the {self.max_size} byte limit."),
                        },
                        "meta": {},
                    },
                )

        return await call_next(request)
