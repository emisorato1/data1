"""OWASP security headers middleware.

Adds hardcoded security headers to every response.  Values follow industry
best-practice and are NOT configurable — there is no valid reason to weaken
them at the application level.

In **development** the CSP is relaxed *only* for documentation routes
(``/docs``, ``/redoc``, ``/openapi.json``) so that Swagger UI can load
external CSS/JS from the jsdelivr CDN and execute the inline bootstrap
script.  All API routes always receive the strict ``default-src 'none'``
policy regardless of environment.

.. warning:: TODO(T2-S3-01): Rewrite as pure ASGI middleware before SSE
   streaming is implemented.  ``BaseHTTPMiddleware`` buffers the entire
   response body, which will break streaming endpoints.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.config.settings import settings

# Paths that serve Swagger / ReDoc HTML pages
_DOCS_PATHS = frozenset({"/docs", "/docs/", "/redoc", "/redoc/", "/openapi.json"})

# Permissive CSP that allows Swagger UI to function (development only)
_DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' https://fastapi.tiangolo.com data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'"
)

# Strict CSP for API endpoints (no resources needed)
_API_CSP = "default-src 'none'; frame-ancestors 'none'"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject OWASP-recommended security headers into all responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enforce HTTPS (1 year + subdomains)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Legacy XSS filter (still useful for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control information sent in Referer header
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict unused browser features
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # CSP: relaxed for docs in development, strict everywhere else
        path = request.url.path.rstrip("/") or "/"
        is_docs_path = f"{path}/" in _DOCS_PATHS or path in _DOCS_PATHS
        if is_docs_path and not settings.is_production:
            response.headers["Content-Security-Policy"] = _DOCS_CSP
        else:
            response.headers["Content-Security-Policy"] = _API_CSP

        # Prevent caching of API responses that may contain sensitive data
        if "/api/" in request.url.path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response
