"""Use case: stream RAG response via SSE.

Orchestrates the full chat flow:
1. ``prepare_chat_context`` - validate conversation + persist user message.
   **Must** be called BEFORE creating the ``EventSourceResponse`` so that
   any ``NotFoundError`` is raised in the normal request scope (not inside
   an async generator where ``sse-starlette`` wraps it in an ExceptionGroup).
2. ``stream_rag_events`` - iterate the RAG graph with timeout and yield SSE
   events (``token``, ``done``, ``error``).

Each ``yield`` produces a dict ready for ``sse-starlette``'s
``EventSourceResponse`` (keys: ``event``, ``data``).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

if TYPE_CHECKING:
    from fastapi import BackgroundTasks

from src.application.graphs.nodes.extract_memories import extract_memories
from src.application.graphs.nodes.generate import format_user_memories
from src.application.graphs.nodes.validate_output import validate_output
from src.config.settings import settings
from src.infrastructure.database.models.conversation import Message
from src.infrastructure.llm.client import GeminiClient, GeminiModel
from src.infrastructure.llm.prompts.system_prompt import (
    RAG_FALLBACK_MESSAGE,
    build_rag_prompt,
)
from src.infrastructure.llm.prompts.title_prompt import TITLE_GENERATION_PROMPT
from src.infrastructure.observability.langfuse_client import (
    create_callback_handler,
    flush_langfuse,
    observe,
    propagate_attributes,
)
from src.shared.exceptions import NotFoundError

if TYPE_CHECKING:
    import uuid
    from collections.abc import AsyncIterator

    from langchain_core.runnables import RunnableConfig
    from langgraph.graph.state import CompiledStateGraph
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.application.graphs.state import RAGState
    from src.domain.repositories.conversation_repository import ConversationRepositoryBase

# Maximo de turnos previos a incluir en el prompt (user+assistant = 1 turno).
# Limitar para no exceder la ventana de contexto del LLM.
_MAX_HISTORY_TURNS = 5

logger = logging.getLogger(__name__)


async def _generate_and_save_title(
    conversation_id: uuid.UUID,
    user_id: int,
    message: str,
) -> None:
    """Generate a title using LLM and update the conversation."""
    try:
        from src.application.use_cases.rag.conversations import update_conversation
        from src.infrastructure.database.repositories.conversation_repository import ConversationRepository
        from src.infrastructure.database.session import async_session_maker

        client = GeminiClient(model=GeminiModel.FLASH_LITE, temperature=0.3, max_tokens=10)
        prompt = TITLE_GENERATION_PROMPT.format(message=message)

        try:
            title = await client.generate(prompt)
            title = title.strip().strip('"').strip("'").strip(".")[:50]
        except Exception:
            title = message[:50]

        async with async_session_maker() as session:
            repo = ConversationRepository(session)
            await update_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                title=title,
                db=session,
                repo=repo,
            )
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to generate title for conversation {conversation_id}: {e}")


async def prepare_chat_context(
    *,
    conversation_id: uuid.UUID,
    user_id: int,
    message: str,
    db: AsyncSession,
    repo: ConversationRepositoryBase,
    background_tasks: BackgroundTasks | None = None,
) -> Message:
    """Validate conversation ownership and persist the user message.

    Returns the persisted ``Message`` instance so the caller can reference it.

    Raises
    ------
    NotFoundError
        If the conversation does not exist or does not belong to ``user_id``.
    """
    conversation = await repo.get_by_id(conversation_id, user_id)
    if conversation is None:
        raise NotFoundError(message="Conversation not found.")

    # Check if this is the first user message, generate title if it is
    if not conversation.title and len(conversation.messages) == 0 and background_tasks is not None:
        background_tasks.add_task(_generate_and_save_title, conversation_id, user_id, message)

    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=message,
    )
    db.add(user_msg)
    await db.flush()
    return user_msg


@observe(name="chat_flow")
async def stream_rag_events(
    *,
    conversation_id: uuid.UUID,
    user_id: int,
    message: str,
    db: AsyncSession,
    rag_graph: CompiledStateGraph,
) -> AsyncIterator[dict[str, str]]:
    """Stream RAG response as SSE events with real token-by-token streaming.

    Two-phase approach:
    1. Run the prep graph (classify → guardrail → retrieve → rerank → assemble)
       to get the context synchronously.
    2. Stream the LLM response directly token-by-token, bypassing LangGraph.

    Events emitted
    --------------
    - ``token``: incremental content chunk (``{"content": "..."}``)
    - ``done``:  final event with sources and message id
    - ``error``: error event
    """
    graph_input: dict[str, Any] = {
        "query": message,
        "user_id": user_id,
        "messages": [HumanMessage(content=message)],
        # Reset per-turn fields to prevent checkpoint contamination
        "query_type": "",
        "guardrail_passed": False,
        "needs_clarification": False,
        "retrieval_confidence": "",
        "response": "",
        "context_text": "",
        "sources": [],
        "retrieved_chunks": [],
        "reranked_chunks": [],
        "faithfulness_score": 0.0,
        "pii_detected": [],
    }

    try:
        with propagate_attributes(
            user_id=str(user_id),
            session_id=str(conversation_id),
            tags=["rag"],
        ):
            # CallbackHandler fresh por request — hereda trace context actual
            cb = create_callback_handler()
            graph_config: RunnableConfig = {
                "configurable": {
                    "thread_id": str(conversation_id),
                },
                "callbacks": [cb] if cb else [],
            }

            # ── FASE 1: Preparación (sincrónica) ─────────────────────
            prep_result = await asyncio.wait_for(
                rag_graph.ainvoke(graph_input, config=graph_config),
                timeout=settings.sse_timeout_seconds,
            )

            query_type = prep_result.get("query_type", "consulta")

            # ── Caso: Saludo o Bloqueado (respuesta directa, sin LLM) ─
            if query_type in ("saludo", "blocked", "fuera_dominio"):
                response_text = prep_result.get("response", "")
                if response_text:
                    yield {
                        "event": "token",
                        "data": json.dumps({"content": response_text}),
                    }

                assistant_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response_text,
                )
                db.add(assistant_msg)
                await db.commit()

                yield {
                    "event": "done",
                    "data": json.dumps(
                        {
                            "sources": [],
                            "message_id": str(assistant_msg.id),
                        }
                    ),
                }
                return

            # ── Caso: Contexto del usuario (acuse de recibo sin RAG) ──────
            if query_type == "contexto_usuario":
                acknowledgment = "Entendido, he tomado nota de esa información. ¿En qué puedo ayudarte hoy?"
                yield {
                    "event": "token",
                    "data": json.dumps({"content": acknowledgment}),
                }

                assistant_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=acknowledgment,
                )
                db.add(assistant_msg)
                await db.commit()

                yield {
                    "event": "done",
                    "data": json.dumps(
                        {
                            "sources": [],
                            "message_id": str(assistant_msg.id),
                        }
                    ),
                }

                # Activar extracción de memorias: el par declaración+acuse es
                # lo que permite a extract_memories generar un recuerdo episódico útil.
                context_memory_state: dict[str, Any] = {
                    "user_id": user_id,
                    "messages": [
                        *prep_result.get("messages", []),
                        AIMessage(content=acknowledgment),
                    ],
                }
                asyncio.create_task(  # noqa: RUF006
                    _safe_extract_memories(context_memory_state),
                    name=f"extract_memories_{conversation_id}",
                )
                return

            # ── Caso: Clarificación (ambiguity_detector activó clarificación) ─
            if prep_result.get("needs_clarification", False):
                response_text = prep_result.get("response", "")
                if response_text:
                    yield {
                        "event": "token",
                        "data": json.dumps({"content": response_text}),
                    }

                assistant_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response_text,
                )
                db.add(assistant_msg)
                await db.commit()

                yield {
                    "event": "done",
                    "data": json.dumps(
                        {
                            "sources": [],
                            "message_id": str(assistant_msg.id),
                        }
                    ),
                }
                return

            # ── FASE 2: Streaming LLM directo (token por token) ──────
            context_text = prep_result.get("context_text", "")
            sources = prep_result.get("sources", [])

            if not context_text.strip():
                yield {
                    "event": "token",
                    "data": json.dumps({"content": RAG_FALLBACK_MESSAGE}),
                }
                assistant_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=RAG_FALLBACK_MESSAGE,
                )
                db.add(assistant_msg)
                await db.commit()
                yield {
                    "event": "done",
                    "data": json.dumps(
                        {
                            "sources": [],
                            "message_id": str(assistant_msg.id),
                        }
                    ),
                }
                return

            conversation_history = _format_history(
                prep_result.get("messages", []),
            )
            sources_text = _build_sources_text(sources)
            user_memories_text = format_user_memories(
                prep_result.get("user_memories", []),
            )
            prompt = build_rag_prompt(
                context=context_text,
                sources=sources_text,
                query=message,
                conversation_history=conversation_history,
                user_memories=user_memories_text,
            )

            # Stream directo del LLM
            client = GeminiClient(model=GeminiModel.FLASH)
            accumulated_response = ""

            async for token in client.generate_stream(prompt, config={"callbacks": [cb]} if cb else {}):
                content = token
                if isinstance(content, list):
                    text_parts = []
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                        elif isinstance(part, str):
                            text_parts.append(part)
                    content = "".join(text_parts)

                if content:
                    accumulated_response += str(content)
                    yield {
                        "event": "token",
                        "data": json.dumps({"content": str(content)}),
                    }

            # Asegurar que las trazas se envíen
            flush_langfuse()

            # ── FASE 3: Output Guardrail + Persistencia ──────────────
            is_fallback = RAG_FALLBACK_MESSAGE.lower() in accumulated_response.lower()
            guardrail_ok = True

            if not is_fallback:
                guardrail_ok, validated_response = validate_output(
                    response=accumulated_response,
                    context=context_text,
                )
                if not guardrail_ok:
                    logger.warning(
                        "output_guardrail_blocked conversation_id=%s user_id=%s",
                        conversation_id,
                        user_id,
                    )
                    yield {
                        "event": "guardrail_blocked",
                        "data": json.dumps({"content": validated_response}),
                    }
                    accumulated_response = validated_response
                    sources = []

            final_sources = [] if is_fallback or not guardrail_ok else sources

            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=accumulated_response,
                sources={"items": final_sources} if final_sources else None,
            )
            db.add(assistant_msg)
            await db.commit()

            # ── FASE 4: Extracción de memorias episódicas ────────────
            memory_state: dict[str, Any] = {
                "user_id": user_id,
                "messages": [
                    *prep_result.get("messages", []),
                    AIMessage(content=accumulated_response),
                ],
            }
            _memory_task = asyncio.create_task(  # noqa: RUF006
                _safe_extract_memories(memory_state),
                name=f"extract_memories_{conversation_id}",
            )

            yield {
                "event": "done",
                "data": json.dumps(
                    {
                        "sources": final_sources,
                        "message_id": str(assistant_msg.id),
                    }
                ),
            }

    except TimeoutError:
        logger.error(
            "sse_timeout conversation_id=%s user_id=%s timeout=%ds",
            conversation_id,
            user_id,
            settings.sse_timeout_seconds,
        )
        yield {
            "event": "error",
            "data": json.dumps(
                {
                    "code": "TIMEOUT",
                    "message": f"La generacion excedio el timeout de {settings.sse_timeout_seconds}s.",
                }
            ),
        }

    except Exception:
        logger.exception(
            "sse_generation_failed conversation_id=%s user_id=%s",
            conversation_id,
            user_id,
        )
        yield {
            "event": "error",
            "data": json.dumps(
                {
                    "code": "GENERATION_FAILED",
                    "message": "Error durante la generacion de la respuesta.",
                }
            ),
        }


def _build_sources_text(sources: list[dict]) -> str:
    """Formatea la lista de sources como texto numerado."""
    if not sources:
        return "Sin fuentes disponibles."
    lines = []
    for src in sources:
        idx = src.get("index", "?")
        name = src.get("document_name", "Documento desconocido")
        page = src.get("page", "N/A")
        lines.append(f"{idx}. {name} (p.{page})")
    return "\n".join(lines)


def _format_history(messages: list[BaseMessage]) -> str:
    """Formatea el historial de mensajes previos para inyectar en el prompt.

    Solo incluye los ultimos ``_MAX_HISTORY_TURNS`` turnos (pares user/assistant)
    y excluye el ultimo HumanMessage (que es la query actual).

    Returns
    -------
    str
        Historial formateado o cadena vacia si no hay historial previo.
    """
    if not messages or len(messages) <= 1:
        return ""

    # Excluir el ultimo mensaje (es la query actual del usuario)
    previous = messages[:-1]
    if not previous:
        return ""

    # Tomar los ultimos N turnos (cada turno = 2 mensajes: user + assistant)
    max_messages = _MAX_HISTORY_TURNS * 2
    if len(previous) > max_messages:
        previous = previous[-max_messages:]

    parts: list[str] = []
    for msg in previous:
        if isinstance(msg, HumanMessage):
            parts.append(f"Usuario: {msg.content}")
        elif isinstance(msg, AIMessage):
            parts.append(f"Asistente: {msg.content}")

    return "\n".join(parts) if parts else ""


async def _safe_extract_memories(state: dict[str, Any]) -> None:
    """Wrapper seguro para extracción de memorias — nunca propaga excepciones."""
    from typing import cast

    try:
        await extract_memories(cast("RAGState", state))
    except Exception:
        logger.exception("memory_extraction_failed user_id=%s", state.get("user_id"))
