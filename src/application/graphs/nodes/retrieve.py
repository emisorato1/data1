"""Nodo retrieve: búsqueda híbrida de chunks relevantes en la base de datos."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import text

from src.application.services.memory_retrieval_service import MemoryRetrievalService
from src.config.settings import settings
from src.infrastructure.database.session import async_session_maker
from src.infrastructure.observability.langfuse_client import observe
from src.infrastructure.rag.embeddings.gemini_embeddings import GeminiEmbeddingService
from src.infrastructure.rag.vector_store.pgvector_store import PgVectorStore
from src.infrastructure.security.permission_cache import PermissionCache
from src.infrastructure.security.permission_resolver import PermissionResolver

try:
    from langfuse.decorators import langfuse_context  # type: ignore
except ImportError:
    langfuse_context = None  # type: ignore

if TYPE_CHECKING:
    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)

# Cache de instancia para evitar reconectar en cada nodo
# En un sistema real usaríamos inyección de dependencias
_embedding_service: GeminiEmbeddingService | None = None
_permission_cache: PermissionCache | None = None


def _get_embedding_service() -> GeminiEmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = GeminiEmbeddingService()
    return _embedding_service


def _get_permission_cache() -> PermissionCache:
    global _permission_cache
    if _permission_cache is None:
        _permission_cache = PermissionCache()
    return _permission_cache


def _build_enriched_query(query: str, messages: list) -> str:
    """Enriquece la query con contexto del turno anterior para mejorar el retrieval.

    Solo actúa cuando la query es corta (≤ 5 tokens) y hay historial previo.
    Extrae el contenido del HumanMessage anterior (no el actual) como contexto.
    No modifica ``state["query"]`` — solo se usa para embedding y búsqueda híbrida.
    """
    token_count = len(query.strip().split())
    if token_count > 5 or not messages:
        return query

    from langchain_core.messages import AIMessage, HumanMessage

    # Buscar el HumanMessage anterior al actual (el actual es el último mensaje)
    # messages[-1] es el HumanMessage actual; buscamos el último previo
    prev_human: str | None = None
    for msg in reversed(messages[:-1]):
        content = str(msg.content) if not isinstance(msg.content, str) else msg.content
        if isinstance(msg, HumanMessage) and content.strip() != query.strip():
            prev_human = content[:80]  # primeros 80 chars para no saturar
            break

    if not prev_human:
        # Fallback: usar el último AIMessage como contexto
        for msg in reversed(messages[:-1]):
            if isinstance(msg, AIMessage):
                prev_human = str(msg.content)[:60] if not isinstance(msg.content, str) else msg.content[:60]
                break

    if not prev_human:
        return query

    return f"{query} (contexto: {prev_human})"


@observe(name="retrieve")
async def retrieve_node(state: RAGState) -> dict:
    """Ejecuta búsqueda híbrida (Vector + BM25) sobre los documentos.

    1. Resuelve los documentos accesibles para el usuario (Late binding).
    2. Configura ef_search de HNSW para la sesión (spec T3-S4-02).
    3. Genera embedding de la consulta.
    4. Ejecuta búsqueda híbrida en Postgres con filtro de permisos.
    5. Busca memorias episódicas relevantes (T4-S5-02).
    """
    query = state.get("query", "")
    user_id = state.get("user_id")
    messages: list = state.get("messages", [])

    if not user_id:
        logger.warning("No user_id found in state. Skipping retrieval.")
        return {"retrieved_chunks": [], "context_text": "No tengo documentos disponibles para tu consulta"}

    # 1. Generar Embedding (con query enriquecida si hay historial y la query es corta)
    retrieval_query = _build_enriched_query(query, messages)
    if retrieval_query != query:
        logger.debug("retrieve: query enriched for retrieval (original=%r)", query)

    embedding_service = _get_embedding_service()
    query_vector = await embedding_service.embed_query(retrieval_query)

    # 2. Búsqueda Híbrida con ef_search tuneable (T3-S4-02), Filtro de Permisos y Memoria (T4-S5-02)
    async with async_session_maker() as session:
        # Resolver permisos usando CTE para grupos
        permission_cache = _get_permission_cache()
        resolver = PermissionResolver(session, permission_cache)
        accessible_doc_ids = await resolver.get_accessible_document_ids(user_id, use_cte=True)

        if not accessible_doc_ids:
            logger.info("Usuario %s no tiene acceso a ningún documento. Cortocircuitando búsqueda.", user_id)
            if langfuse_context is not None:
                langfuse_context.update_current_observation(metadata={"accessible_doc_ids": []})
            return {
                "query_embedding": query_vector,
                "retrieved_chunks": [],
                "context_text": "No tengo documentos disponibles para tu consulta",
            }

        if langfuse_context is not None:
            langfuse_context.update_current_observation(metadata={"accessible_doc_ids": list(accessible_doc_ids)})

        # Configurar ef_search para esta sesión (SET LOCAL no afecta otras)
        # SET no acepta bind params ($1) en PostgreSQL, se interpola como literal.
        # Es seguro: retrieval_ef_search es un int validado por Pydantic.
        await session.execute(text(f"SET LOCAL hnsw.ef_search = {settings.retrieval_ef_search}"))

        vector_store = PgVectorStore(session)

        # Recuperamos un pool amplio para luego rerankear
        hybrid_results = await vector_store.hybrid_search(
            query_embedding=query_vector,
            query_text=retrieval_query,
            match_count=settings.retrieval_top_k,
            rrf_k=settings.retrieval_rrf_k,
            accessible_doc_ids=list(accessible_doc_ids),
        )

        # Buscar memorias relevantes
        memories = []
        if user_id:
            memory_service = MemoryRetrievalService(session)
            memories = await memory_service.search_memories(
                user_id=user_id,
                query_embedding=query_vector,
            )

    logger.info("retrieve: %d chunks encontrados para la query '%s'", len(hybrid_results), query)

    return {
        "query_embedding": query_vector,
        "retrieved_chunks": hybrid_results,
        "user_memories": memories,
    }
