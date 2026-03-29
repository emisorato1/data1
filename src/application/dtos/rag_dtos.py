"""DTOs for conversation endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# ── Request DTOs ──────────────────────────────────────────────


class CreateConversationRequest(BaseModel):
    """Body for POST /api/v1/conversations."""

    title: str | None = Field(
        None,
        max_length=255,
        description="Titulo opcional. Si se omite queda NULL hasta que el usuario lo asigne.",
    )


class RenameConversationRequest(BaseModel):
    """Body for PATCH /api/v1/conversations/{id}."""

    title: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="Nuevo titulo de la conversacion.",
    )
    is_pinned: bool | None = Field(None, description="Indica si el chat esta fijado.")
    is_favorite: bool | None = Field(None, description="Indica si el chat es favorito.")


class SendMessageRequest(BaseModel):
    """Body for POST /api/v1/conversations/{id}/messages."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Pregunta del usuario para el sistema RAG.",
    )


# ── Response DTOs ─────────────────────────────────────────────


class ConversationSummary(BaseModel):
    """Item in the paginated conversation list."""

    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    is_pinned: bool = False
    is_favorite: bool = False

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Single message inside a conversation detail."""

    id: UUID
    role: str
    content: str
    sources: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    """Full conversation with messages (GET /conversations/{id})."""

    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    is_pinned: bool = False
    is_favorite: bool = False
    messages: list[MessageResponse]

    model_config = {"from_attributes": True}
