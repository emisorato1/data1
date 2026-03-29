"""Application exception hierarchy.

Flat two-level hierarchy: AppError -> specific errors.
All handlers convert these to the standard {"data", "error", "meta"} envelope.
"""

from typing import Any


class AppError(Exception):
    """Base application error with structured error response support."""

    def __init__(
        self,
        *,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        message: str = "An unexpected error occurred.",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class NotFoundError(AppError):
    """Resource not found (404)."""

    def __init__(
        self,
        message: str = "Resource not found.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code="NOT_FOUND", status_code=404, message=message, details=details)


class AuthenticationError(AppError):
    """Authentication failed (401)."""

    def __init__(
        self,
        message: str = "Authentication failed.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code="AUTH_FAILED", status_code=401, message=message, details=details)


class AuthorizationError(AppError):
    """Insufficient permissions (403)."""

    def __init__(
        self,
        message: str = "Insufficient permissions.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code="FORBIDDEN", status_code=403, message=message, details=details)


class ValidationError(AppError):
    """Domain validation error (422)."""

    def __init__(
        self,
        message: str = "Validation failed.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code="VALIDATION_ERROR", status_code=422, message=message, details=details)


class RateLimitError(AppError):
    """Rate limit exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code="RATE_LIMIT_EXCEEDED", status_code=429, message=message, details=details)


class ExternalServiceError(AppError):
    """External service failure (502)."""

    def __init__(
        self,
        message: str = "External service error.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code="EXTERNAL_SERVICE_ERROR", status_code=502, message=message, details=details)


class PipelineError(AppError):
    """Pipeline processing error (500)."""

    def __init__(
        self,
        message: str = "Pipeline processing error.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code="PIPELINE_ERROR", status_code=500, message=message, details=details)
