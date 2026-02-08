from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums.conversation_status import ConversationStatus


@dataclass(frozen=True)
class Conversation:
    id: UUID
    tenant_id: UUID
    user_id: UUID
    title: str | None
    status: ConversationStatus
    created_at: datetime