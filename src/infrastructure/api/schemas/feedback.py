"""Esquemas de validación Pydantic para feedback de respuestas RAG."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    """Payload para enviar feedback."""

    message_id: UUID = Field(..., description="ID del mensaje del asistente.")
    rating: Literal["positive", "negative"] = Field(..., description="Calificación (positive o negative).")
    comment: str | None = Field(default=None, description="Comentario opcional, util para rating negativo.")

    model_config = ConfigDict(from_attributes=True)


class FeedbackResponse(BaseModel):
    """Respuesta al enviar feedback."""

    id: UUID
    message_id: UUID
    rating: Literal["positive", "negative"]
    comment: str | None

    model_config = ConfigDict(from_attributes=True)
