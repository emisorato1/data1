"""Endpoint para recibir feedback de las respuestas del asistente."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.api.dependencies import get_current_user, get_db
from src.infrastructure.api.schemas.feedback import FeedbackCreate, FeedbackResponse
from src.infrastructure.database.models.conversation import Message
from src.infrastructure.database.models.feedback import Feedback
from src.infrastructure.database.models.user import User
from src.infrastructure.observability.langfuse_client import get_langfuse

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    payload: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    """Envía feedback (thumbs up/down) para una respuesta específica del asistente."""

    # 1. Validar que el mensaje exista y sea del asistente
    query = select(Message).where(Message.id == payload.message_id, Message.role == "assistant")
    result = await session.execute(query)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado o no es una respuesta del asistente")

    # Validar que el mensaje pertenezca a una conversación del usuario actual
    await session.refresh(message, ["conversation"])
    if message.conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para dar feedback a este mensaje")

    # 2. Validar que no haya feedback previo (toggle no acumulativo)
    existing_query = select(Feedback).where(Feedback.message_id == payload.message_id)
    existing_result = await session.execute(existing_query)
    existing_feedback = existing_result.scalar_one_or_none()

    if existing_feedback:
        # Se podría actualizar en lugar de rechazar si es un toggle,
        # pero la spec dice "Un solo feedback por respuesta (toggle, no acumulativo)".
        # Vamos a actualizarlo si ya existe para permitir el toggle.
        existing_feedback.rating = payload.rating
        existing_feedback.comment = payload.comment
        feedback_obj = existing_feedback
    else:
        # Crear nuevo
        feedback_obj = Feedback(
            message_id=payload.message_id,
            rating=payload.rating,
            comment=payload.comment,
        )
        session.add(feedback_obj)

    await session.commit()
    await session.refresh(feedback_obj)

    # 3. Enviar score a Langfuse
    langfuse = get_langfuse()
    if langfuse:
        score_value = 1.0 if payload.rating == "positive" else 0.0

        # El trace_id en Langfuse usualmente es el message_id o conversation_id.
        # El spec dice: "Feedback enviado a Langfuse como score del trace correspondiente"
        # Asumimos que el trace_id es el id del mensaje o que se puede atar al trace.
        langfuse.score(  # type: ignore
            trace_id=str(message.conversation_id),
            observation_id=str(message.id),  # Assuming generation/span ID is message.id
            name="user_feedback",
            value=score_value,
            comment=payload.comment,
        )

    return FeedbackResponse.model_validate(feedback_obj)
