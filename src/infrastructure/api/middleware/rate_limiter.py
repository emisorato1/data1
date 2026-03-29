"""Rate limiting middleware with Redis Token Bucket algorithm.

Pure ASGI middleware (no BaseHTTPMiddleware) to avoid buffering responses,
keeping full compatibility with SSE/streaming endpoints.

Algorithm: Token Bucket.
  - See `src.infrastructure.cache.token_bucket.TokenBucket`.

Identification:
  - Users: by authenticated user_id from JWT cookie.
  - Unauthenticated fallback: by client IP.
  - Endpoints: Chat, Upload, and Default.
  - Role: Admin users get higher limits.

Fail-open: if Redis is unreachable, requests are allowed with a warning log.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import structlog
from redis.exceptions import RedisError

from src.config.settings import settings
from src.infrastructure.cache.token_bucket import TokenBucket
from src.infrastructure.security.jwt import decode_access_token

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = structlog.get_logger()

# Paths exempt from rate limiting (health checks, docs).
_EXEMPT_PREFIXES: tuple[str, ...] = ("/health", "/docs", "/redoc", "/openapi.json", "/metrics")


def _build_429_body(retry_after: int) -> bytes:
    """Build a JSON 429 response body following the standard envelope."""
    payload: dict[str, Any] = {
        "success": False,
        "error": {
            "code": "RATE_001",
            "message": "Too many requests. Please try again later.",
            "details": {"retry_after_seconds": retry_after},
        },
    }
    return json.dumps(payload).encode("utf-8")


def _get_client_ip(scope: Scope) -> str:
    """Extract client IP, respecting X-Forwarded-For behind a load balancer."""
    headers: dict[bytes, bytes] = dict(scope.get("headers", []))

    # X-Forwarded-For: client, proxy1, proxy2 -- take the first (leftmost).
    xff = headers.get(b"x-forwarded-for")
    if xff:
        first_ip = xff.decode("latin-1").split(",")[0].strip()
        if first_ip:
            return first_ip

    # Fallback to ASGI client address.
    client = scope.get("client")
    if client:
        return str(client[0])

    return "unknown"


def _get_user_info_from_cookie(scope: Scope) -> tuple[str | None, str | None]:
    """Try to extract user_id and role from the access_token JWT cookie.

    Returns the (user_id, role) strings on success, (None, None) otherwise.
    This is a best-effort extraction for rate-limiting purposes only.
    """
    headers: dict[bytes, bytes] = dict(scope.get("headers", []))
    cookie_header = headers.get(b"cookie")
    if not cookie_header:
        return None, None

    for part in cookie_header.decode("latin-1").split(";"):
        part = part.strip()
        if part.startswith("access_token="):
            token = part[len("access_token=") :]
            try:
                payload = decode_access_token(token)
                return payload.get("sub"), payload.get("role")
            except Exception:
                return None, None

    return None, None


def _get_endpoint_type(scope: Scope) -> str:
    """Identify the endpoint category based on method and path."""
    method = scope.get("method", "")
    path: str = scope.get("path", "")

    # Pattern: POST /api/v1/conversations/{uuid}/messages
    if method == "POST" and "conversations" in path and path.endswith("/messages"):
        return "chat"

    # Pattern: POST /api/v1/documents (or similar upload)
    if method == "POST" and "documents" in path:
        # We classify generic POST to documents as upload
        return "upload"

    return "default"


class RateLimiterMiddleware:
    """Pure ASGI rate-limiting middleware using Redis Token Bucket."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._tb: TokenBucket | None = None

    def _get_token_bucket(self, redis: Redis) -> TokenBucket:
        if self._tb is None or self._tb.redis != redis:
            self._tb = TokenBucket(redis)
        return self._tb

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not settings.rate_limit_enabled:
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")

        # Skip exempt paths.
        if any(path.startswith(prefix) for prefix in _EXEMPT_PREFIXES):
            await self.app(scope, receive, send)
            return

        # Skip non-API paths.
        if not path.startswith("/api/"):
            await self.app(scope, receive, send)
            return

        # Identify user and endpoint
        user_id, role = _get_user_info_from_cookie(scope)
        endpoint_type = _get_endpoint_type(scope)

        if user_id:
            key_prefix = f"rl:tb:user:{user_id}"

            if role == "admin":
                capacity = settings.rate_limit_admin_capacity
                rate = settings.rate_limit_admin_rate
                key = f"{key_prefix}:admin"
            elif endpoint_type == "chat":
                capacity = settings.rate_limit_chat_capacity
                rate = settings.rate_limit_chat_rate
                key = f"{key_prefix}:chat"
            elif endpoint_type == "upload":
                capacity = settings.rate_limit_upload_capacity
                rate = settings.rate_limit_upload_rate
                key = f"{key_prefix}:upload"
            else:
                capacity = settings.rate_limit_default_capacity
                rate = settings.rate_limit_default_rate
                key = f"{key_prefix}:default"
        else:
            # Fallback to IP-based rate limiting (simple capacity based on settings)
            # Reusing the IP window for capacity to map to token bucket
            capacity = settings.rate_limit_ip_max_requests
            rate = float(settings.rate_limit_ip_max_requests) / settings.rate_limit_ip_window_seconds
            key = f"rl:tb:ip:{_get_client_ip(scope)}"

        # Check rate limit via Redis.
        allowed, remaining, reset_in = await self._check_rate_limit(
            scope=scope,
            key=key,
            capacity=capacity,
            rate=rate,
        )

        if not allowed:
            # Log metric
            if user_id:
                logger.warning(
                    "rate_limit_exceeded_user",
                    user_id=user_id,
                    endpoint_type=endpoint_type,
                    role=role,
                    retry_after=reset_in,
                )
            else:
                logger.warning("rate_limit_exceeded_ip", ip=_get_client_ip(scope))

            await self._send_429(send, reset_in, capacity, remaining)
            return

        # Wrap send to inject rate limit headers
        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(
                    [
                        (b"x-ratelimit-limit", str(capacity).encode("ascii")),
                        (b"x-ratelimit-remaining", str(remaining).encode("ascii")),
                        (b"x-ratelimit-reset", str(reset_in).encode("ascii")),
                    ]
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)

    async def _check_rate_limit(
        self,
        *,
        scope: Scope,
        key: str,
        capacity: int,
        rate: float,
    ) -> tuple[bool, int, int]:
        """Check and record request. Returns (allowed, remaining, reset_in)."""
        try:
            redis: Redis = scope["app"].state.redis  # type: ignore[index]
        except (KeyError, AttributeError):
            logger.warning("rate_limit_redis_unavailable", key=key)
            return True, capacity, 0

        try:
            tb = self._get_token_bucket(redis)
            return await tb.consume(key, capacity, rate)
        except RedisError:
            # Fail-open: allow the request if Redis is down.
            logger.warning("rate_limit_redis_error", key=key, exc_info=True)
            return True, capacity, 0

    @staticmethod
    async def _send_429(send: Send, retry_after: int, limit: int, remaining: int) -> None:
        """Send an HTTP 429 response directly via ASGI."""
        body = _build_429_body(retry_after)
        headers: list[tuple[bytes, bytes]] = [
            (b"content-type", b"application/json"),
            (b"retry-after", str(retry_after).encode("ascii")),
            (b"x-ratelimit-limit", str(limit).encode("ascii")),
            (b"x-ratelimit-remaining", str(remaining).encode("ascii")),
            (b"x-ratelimit-reset", str(retry_after).encode("ascii")),
            (b"content-length", str(len(body)).encode("ascii")),
        ]

        start_msg: Message = {
            "type": "http.response.start",
            "status": 429,
            "headers": headers,
        }
        body_msg: Message = {
            "type": "http.response.body",
            "body": body,
        }
        await send(start_msg)
        await send(body_msg)
