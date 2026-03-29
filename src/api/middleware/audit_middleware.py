import asyncio
from collections.abc import Callable

from fastapi import Request, Response
from src.application.services.audit_service import AuditService
from src.domain.entities.audit_log import AuditLogEntry
from src.infrastructure.database.session import async_session_maker
from starlette.middleware.base import BaseHTTPMiddleware

SENSITIVE_ENDPOINTS = [
    ("/api/v1/documents", "POST", "document_upload"),
    ("/api/v1/documents", "DELETE", "document_delete"),
    ("/api/v1/auth/login", "POST", "login"),
    ("/api/v1/auth/logout", "POST", "logout"),
    ("/api/v1/rag/query", "POST", "query"),
    ("/api/v1/admin", "*", "admin_action"),
]


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[type-arg]
        response: Response = await call_next(request)

        # Check if endpoint is sensitive
        action_name = self._get_action_from_request(request)
        if action_name:
            # We want to log the action asynchronously without blocking
            user_id = getattr(request.state, "user_id", None)
            session_id = getattr(request.state, "session_id", None)

            # Simple IP extraction
            client_ip = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

            entry = AuditLogEntry(
                actor_id=user_id,
                session_id=session_id,
                action=action_name,
                resource_type="endpoint",
                resource_id=None,
                details_json={"path": request.url.path, "method": request.method, "status_code": response.status_code},
                ip_address=client_ip,
                user_agent=user_agent,
                status="success" if response.status_code < 400 else "failed",
            )

            # Schedule the task so it runs independently
            asyncio.create_task(self._log_audit(entry))  # noqa: RUF006

        return response

    def _get_action_from_request(self, request: Request) -> str | None:
        path = request.url.path
        method = request.method

        for ep_path, ep_method, action in SENSITIVE_ENDPOINTS:
            if path.startswith(ep_path) and (ep_method == "*" or ep_method == method):
                return action
        return None

    async def _log_audit(self, entry: AuditLogEntry) -> None:
        async with async_session_maker() as session:
            audit_service = AuditService(session)
            try:
                await audit_service.log(entry)
            except Exception as e:
                # Log to standard logger if DB audit fails
                import structlog

                logger = structlog.get_logger(__name__)
                logger.error("audit_log_failed", error=str(e))
