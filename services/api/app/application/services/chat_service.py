from __future__ import annotations

from uuid import UUID, uuid4
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.http.rag_client import RagClient
from app.infrastructure.db.orm.message import MessageORM
from app.infrastructure.db.orm.message_source import MessageSourceORM
from app.core.config import settings

# Import del cliente global de Langfuse
from app.infrastructure.observability.langfuse_client import get_langfuse_client

# UUID por defecto para usuarios anónimos
ANONYMOUS_USER_ID = UUID("00000000-0000-0000-0000-000000000000")
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


class ChatService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.rag = RagClient()

    def _extract_text_and_sources(self, rag_result: dict) -> tuple[str, list]:
        """
        Intentá extraer el texto del assistant y las sources tolerando distintos formatos.
        Normaliza las sources al formato esperado por el frontend.
        """
        if not rag_result:
            return "", []

        # Formato A: { values: { response: "...", sources: [...] } }
        values = rag_result.get("values")
        if isinstance(values, dict):
            text = (
                values.get("response")
                or values.get("message")
                or values.get("answer")
                or values.get("output")
                or ""
            )
            sources = values.get("sources") or []
            return text, self._normalize_sources(sources)

        # Formato B: { response: "...", sources: [...] } o { message: "...", sources: [...] }
        text = (
            rag_result.get("response")
            or rag_result.get("message")
            or rag_result.get("answer")
            or rag_result.get("output")
            or ""
        )
        sources = rag_result.get("sources") or []
        return text, self._normalize_sources(sources)
    
    def _normalize_sources(self, sources: list) -> list:
        """
        Normaliza las sources al formato esperado por el frontend.
        Deduplica por nombre de documento, manteniendo el de mayor score.
        
        El RAG envía: title, relevance_score, snippet, document_id, chunk_id
        El frontend espera: source_name (o name), score, snippet
        """
        if not sources:
            return []
        
        # Diccionario para deduplicar por nombre de documento
        seen_docs: dict[str, dict] = {}
        
        for s in sources:
            if isinstance(s, dict):
                source_name = s.get("title") or s.get("source_name") or s.get("name") or "Documento"
                score = s.get("relevance_score") or s.get("score") or 0
                
                # Si ya vimos este documento, mantener el de mayor score
                if source_name in seen_docs:
                    existing_score = seen_docs[source_name].get("score") or 0
                    if score > existing_score:
                        seen_docs[source_name] = {
                            "source_name": source_name,
                            "name": source_name,
                            "score": score,
                            "snippet": s.get("snippet") or s.get("content", "")[:200],
                            "document_id": s.get("document_id"),
                            "chunk_id": s.get("chunk_id"),
                        }
                else:
                    seen_docs[source_name] = {
                        "source_name": source_name,
                        "name": source_name,
                        "score": score,
                        "snippet": s.get("snippet") or s.get("content", "")[:200],
                        "document_id": s.get("document_id"),
                        "chunk_id": s.get("chunk_id"),
                    }
            else:
                source_name = str(s)
                if source_name not in seen_docs:
                    seen_docs[source_name] = {
                        "source_name": source_name,
                        "name": source_name,
                    }
        
        # Retornar ordenado por score descendente
        return sorted(seen_docs.values(), key=lambda x: x.get("score") or 0, reverse=True)

    async def execute(
        self,
        *,
        session_id: UUID,
        user_role: str,
        message: str,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
    ) -> dict:
        # Crear trace en Langfuse si está habilitado
        langfuse = get_langfuse_client()
        trace = None
        
        if langfuse and settings.LANGFUSE_ENABLED:
            try:
                trace = langfuse.trace(
                    name="chat_execute",
                    user_id=str(session_id),
                    session_id=str(session_id),
                    metadata={"user_role": user_role},
                    tags=["chat", user_role],
                    input={"message": message},
                )
            except Exception:
                pass

        # 1) guardar mensaje user
        user_msg = MessageORM(
            session_id=session_id,
            user_role=user_role,
            direction="user",
            content=message,
            meta={},
        )
        self.db.add(user_msg)
        await self.db.flush()

        # Resolver IDs para memoria (usar defaults si no hay usuario autenticado)
        effective_user_id = user_id or ANONYMOUS_USER_ID
        effective_tenant_id = tenant_id or DEFAULT_TENANT_ID
        
        # 2) llamar RAG (pero que no reviente todo si falla)
        try:
            rag_result = await self.rag.run_and_join(
                message=message,
                session_id=str(session_id),  # thread_id para short-term memory
                user_id=effective_user_id,   # user_id para long-term memory
                tenant_id=effective_tenant_id,
                user_role=user_role,
            )

            assistant_text, sources = self._extract_text_and_sources(rag_result or {})

            # Fallback si el RAG "respondió" pero no trajo texto
            if not assistant_text.strip():
                assistant_text = (
                    "No encontré una respuesta utilizable en el resultado del RAG. "
                    "Revisá el formato de salida del grafo (qué campo trae el texto final)."
                )

        except Exception as e:
            assistant_text = "Hubo un error procesando tu consulta. Intentá de nuevo en unos segundos."
            sources = []
            rag_result = {"error": str(e)}

        # 3) guardar mensaje assistant (aunque RAG falle)
        assistant_msg = MessageORM(
            session_id=session_id,
            user_role=user_role,
            direction="assistant",
            content=assistant_text,
            meta={"rag": rag_result} if rag_result else {},
        )
        self.db.add(assistant_msg)
        await self.db.flush()

        # 4) guardar sources (si vienen)
        for s in sources:
            if isinstance(s, dict):
                # Convertir score a float si existe
                score_value = s.get("score")
                if score_value is not None:
                    try:
                        score_value = float(score_value)
                    except (ValueError, TypeError):
                        score_value = None
                
                self.db.add(
                    MessageSourceORM(
                        message_id=assistant_msg.id,
                        source_name=s.get("source_name") or s.get("name") or "unknown",
                        snippet=s.get("snippet"),
                        url=s.get("url"),
                        score=score_value,
                    )
                )
            else:
                self.db.add(
                    MessageSourceORM(
                        message_id=assistant_msg.id,
                        source_name=str(s),
                    )
                )

        await self.db.commit()

        result = {
            "session_id": str(session_id),
            "message": assistant_text,
            "sources": sources,
            "rag": {
                "thread_id": (rag_result or {}).get("thread_id"),
                "run_id": (rag_result or {}).get("run_id"),
                "error": (rag_result or {}).get("error"),
            },
        }
        
        if trace:
            try:
                # Actualizar el trace con la respuesta
                trace.update(output=result)
                trace.end()  # Finalizar observation manualmente (v3)
                
                # Flush inmediato
                if langfuse:
                    langfuse.flush()
            except Exception:
                pass
        
        return result

    async def list_messages(self, session_id: UUID):
        stmt = (
            select(MessageORM)
            .where(MessageORM.session_id == session_id)
            .order_by(MessageORM.created_at.asc())
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def execute_stream(
        self,
        *,
        session_id: UUID,
        user_role: str,
        message: str,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Ejecuta el chat en modo streaming.
        Yields chunks de respuesta (tokens) y al final guarda el mensaje completo en BD.
        
        Args:
            session_id: ID de la sesión/thread (short-term memory)
            user_role: Rol del usuario para permisos
            message: Mensaje del usuario
            user_id: ID del usuario autenticado (long-term memory)
            tenant_id: ID del tenant del usuario
        """
        # 1) Guardar mensaje user
        user_msg = MessageORM(
            session_id=session_id,
            user_role=user_role,
            direction="user",
            content=message,
            meta={},
        )
        self.db.add(user_msg)
        await self.db.flush()
        
        # Resolver IDs para memoria (usar defaults si no hay usuario autenticado)
        effective_user_id = user_id or ANONYMOUS_USER_ID
        effective_tenant_id = tenant_id or DEFAULT_TENANT_ID
        
        full_response = ""
        sources = []
        
        try:
            # 2) Streaming desde RAG con soporte de memoria
            async for event in self.rag.stream(
                message=message, 
                session_id=str(session_id),  # thread_id para short-term memory
                user_id=effective_user_id,   # user_id para long-term memory
                tenant_id=effective_tenant_id,
                user_role=user_role,
            ):
                # RagClient yields {"event": "events", "data": {SSE JSON payload}}
                # El evento REAL de LangGraph está en data["event"]
                data = event.get("data", {})
                kind = data.get("event", "")  # El tipo de evento real está DENTRO de data
                
                # Filtrar solo eventos de generación de chat model de los agentes (NO del orchestrator)
                if kind == "on_chat_model_stream":
                    metadata = data.get("metadata", {})
                    langgraph_node = metadata.get("langgraph_node", "")
                    
                    # Solo capturar chunks de los agentes que generan respuestas
                    if langgraph_node in ("public_agent", "private_agent"):
                        chunk_data = data.get("data", {})
                        chunk_content = chunk_data.get("chunk", {}).get("content", "")
                        if chunk_content:
                            full_response += chunk_content
                            # Yield para el frontend
                            yield {"content": chunk_content, "done": False}
                
                # Detectar el evento final del grafo raíz (SOLO name="rag_generation")
                if kind == "on_chain_end":
                    event_name = data.get("name", "")
                    
                    # SOLO procesar el evento del nodo raíz final
                    is_root = (event_name == "rag_generation")
                    
                    if is_root:
                        # Intentar sacar sources y texto del output final
                        inner_data = data.get("data", {})
                        output = inner_data.get("output", {})
                        
                        if output:
                            extracted_text, extracted_sources = self._extract_text_and_sources(output)
                            if extracted_sources:
                                sources = extracted_sources
                            
                            # Fallback: Si no se stremeó nada (full_response vacío), usar el texto final
                            if not full_response and extracted_text:
                                full_response = extracted_text
                                yield {"content": full_response, "done": False}

        except Exception as e:
            yield {"content": f"\n[Error: {str(e)}]", "done": True}
            full_response += f"\n[Error: {str(e)}]"
        
        # 3) Guardar mensaje assistant
        assistant_msg = MessageORM(
            session_id=session_id,
            user_role=user_role,
            direction="assistant",
            content=full_response,
            meta={},
        )
        self.db.add(assistant_msg)
        await self.db.flush()
        
        # 4) Guardar sources
        for s in sources:
            if isinstance(s, dict):
                # Convertir score a float si existe
                score_value = s.get("score")
                if score_value is not None:
                    try:
                        score_value = float(score_value)
                    except (ValueError, TypeError):
                        score_value = None
                
                self.db.add(
                    MessageSourceORM(
                        message_id=assistant_msg.id,
                        source_name=s.get("source_name") or s.get("name") or "unknown",
                        snippet=s.get("snippet"),
                        url=s.get("url"),
                        score=score_value,
                    )
                )
            else:
                self.db.add(
                    MessageSourceORM(
                        message_id=assistant_msg.id,
                        source_name=str(s),
                    )
                )

        await self.db.commit()
        
        # Yield final con sources
        yield {"content": "", "done": True, "sources": sources}


def _pick_text_and_sources(self, joined: dict) -> tuple[str, list]:
    if not isinstance(joined, dict):
        return "", []

    # 1) valores típicos
    values = joined.get("values")
    if isinstance(values, dict):
        # texto candidato en orden
        text = (
            values.get("response")
            or values.get("answer")
            or values.get("final")
            or values.get("output")
            or values.get("generation")
            or values.get("content")
            or ""
        )

        # a veces sources vienen colgados de values
        sources = values.get("sources") or []

        # 1.b) si el grafo devuelve algo tipo values.rag
        rag_block = values.get("rag")
        if (not text) and isinstance(rag_block, dict):
            text = (
                rag_block.get("response")
                or rag_block.get("answer")
                or rag_block.get("final")
                or rag_block.get("output")
                or ""
            )
            if not sources:
                sources = rag_block.get("sources") or []

        return text, sources

    # 2) otros formatos: output directo
    output = joined.get("output")
    if isinstance(output, dict):
        text = (
            output.get("response")
            or output.get("answer")
            or output.get("final")
            or output.get("content")
            or ""
        )
        sources = output.get("sources") or []
        return text, sources

    # 3) fallback top-level
    text = (
        joined.get("response")
        or joined.get("answer")
        or joined.get("final")
        or joined.get("content")
        or ""
    )
    sources = joined.get("sources") or []
    return text, sources
