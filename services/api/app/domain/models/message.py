from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums.message_role import MessageRole


@dataclass(frozen=True)
class Message:
    id: UUID
    tenant_id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    created_at: datetime