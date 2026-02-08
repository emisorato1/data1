from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MessageCreateRequest(BaseModel):
    session_id: UUID
    user_role: str | None = Field(None, pattern="^(public|private|admin)$", deprecated=True)
    content: str = Field(..., min_length=1, max_length=8000)


class MessageSourceResponse(BaseModel):
    source_name: str
    snippet: Optional[str] = None
    url: Optional[str] = None
    score: Optional[float] = None


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    user_role: str
    direction: str
    content: str
    sources: list[MessageSourceResponse] = []


class MessageRunResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse