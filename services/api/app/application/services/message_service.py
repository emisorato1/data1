from __future__ import annotations

from uuid import UUID

from app.infrastructure.db.repositories.message_repo import MessageRepository
from app.infrastructure.http.rag_client import RagClient
from app.infrastructure.db.orm.message import MessageORM
from app.infrastructure.observability.langfuse_client import get_langfuse_client
from app.core.config import settings


class MessageService:
    def __init__(self, msg_repo: MessageRepository, rag: RagClient):
        self.msg_repo = msg_repo
        self.rag = rag

    async def send_and_receive(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        tenant_id: UUID,
        user_role: str,
        content: str,
    ) -> tuple[MessageORM, MessageORM]:
        """Envía un mensaje al RAG y guarda tanto el mensaje del usuario como la respuesta."""
        
        # Crear trace en Langfuse si está habilitado
        langfuse = get_langfuse_client()
        trace = None
        
        if langfuse and settings.LANGFUSE_ENABLED:
            try:
                # Langfuse v3 usa start_observation() en lugar de trace()
                trace = langfuse.start_observation(
                    name="message_send_and_receive",
                    input={"content": content, "user_role": user_role, "session_id": str(session_id)},
                )
            except Exception:
                pass
        
        # 1. Guardar mensaje del usuario
        user_msg = await self.msg_repo.create_user_message(
            session_id=session_id,
            user_role=user_role,
            content=content,
        )

        # 2. Llamar al servicio RAG
        rag_response = await self.rag.run(
            message=content,
            session_id=str(session_id),
            user_id=user_id,
            tenant_id=tenant_id,
            user_role=user_role,
        )

        # 3. Extraer respuesta y sources del RAG
        # LangGraph devuelve el estado en formato: {"values": {"response": "...", ...}}
        # También puede venir directamente como {"response": "..."}
        values = rag_response.get("values", rag_response)
        if not isinstance(values, dict):
            values = {}
        
        response_text = (
            values.get("response") 
            or values.get("answer") 
            or values.get("output")
            or rag_response.get("response")
            or "No se pudo obtener respuesta del agente."
        )
        sources = values.get("sources", rag_response.get("sources", []))

        # Formatear sources para el repositorio
        formatted_sources = []
        for s in sources:
            formatted_sources.append({
                "source_name": s.get("title", "Sin título"),
                "snippet": s.get("snippet", ""),
                "url": None,
                "score": s.get("relevance_score"),
            })

        # 4. Guardar respuesta del asistente
        assistant_msg = await self.msg_repo.create_assistant_message(
            session_id=session_id,
            user_role=user_role,
            content=response_text,
            sources=formatted_sources,
            meta={"rag_response": rag_response},
        )

        # Finalizar observation con el output y flush
        if trace and langfuse:
            try:
                trace.update(output={
                    "response": response_text,
                    "sources_count": len(formatted_sources),
                })
                trace.end()  # Requerido en Langfuse v3 para observations manuales
                langfuse.flush()
            except Exception:
                pass

        return user_msg, assistant_msg
