from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    """Dominio: Representacion de un log de auditoria."""

    id: UUID | None = None
    actor_id: int | None = None
    session_id: str | None = None
    action: str
    resource_type: str | None = None
    resource_id: int | None = None
    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    details_json: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    status: str = "success"
    error_message: str | None = None
    hash_chain: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
