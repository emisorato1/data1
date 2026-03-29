"""Node to extract episodic memories post-generation."""

from typing import Any

from src.application.graphs.state import RAGState
from src.application.services.memory_service import MemoryService
from src.infrastructure.database.session import async_session_maker
from src.infrastructure.rag.embeddings.gemini_embeddings import GeminiEmbeddingService


async def extract_memories(state: RAGState) -> dict[str, Any]:
    """Extrae recuerdos episódicos de la conversación actual."""
    user_id = state.get("user_id")
    messages = state.get("messages", [])

    # Solo procesamos si hay un user_id y suficientes mensajes en el intercambio
    if not user_id or len(messages) < 2:
        return {}

    # Extraemos el historial de conversación en el formato esperado
    conversation_history = [{"role": msg.type, "content": msg.content} for msg in messages]

    # Instanciar el servicio de base de datos
    async with async_session_maker() as session:
        embedding_service = GeminiEmbeddingService()
        memory_service = MemoryService(session=session, embedding_service=embedding_service)

        await memory_service.extract_and_store_memories(user_id=user_id, conversation_history=conversation_history)
        await session.commit()

    return {}
