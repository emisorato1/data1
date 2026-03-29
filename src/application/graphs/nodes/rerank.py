"""Nodo rerank: re-ordena los chunks recuperados usando Gemini."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.config.settings import settings
from src.infrastructure.observability.langfuse_client import observe
from src.infrastructure.rag.retrieval.gemini_reranker import GeminiReranker
from src.infrastructure.rag.retrieval.models import StoredChunk

if TYPE_CHECKING:
    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)

# Instancia global del reranker
_reranker: GeminiReranker | None = None


def _get_reranker() -> GeminiReranker:
    global _reranker
    if _reranker is None:
        _reranker = GeminiReranker()
    return _reranker


@observe(name="rag_rerank")
async def rerank_node(state: RAGState) -> dict:
    """Toma los chunks de 'retrieved_chunks' y los re-ordena con Gemini.

    Retorna 'reranked_chunks'.  El ``top_k`` se lee de ``settings.reranker_top_k``
    (configurable via env ``RERANKER_TOP_K``, spec T3-S4-02).
    """
    query = state.get("query", "")
    retrieved_chunks = state.get("retrieved_chunks", [])

    if not retrieved_chunks:
        logger.info("rerank: sin chunks para rerankear")
        return {"reranked_chunks": []}

    # Convertir dicts a objetos StoredChunk para el reranker
    chunks_to_rerank = [StoredChunk.from_row(c) for c in retrieved_chunks]

    # 2. Reranking con Gemini (top_k configurable via settings — T3-S4-02)
    reranker = _get_reranker()
    reranked_objs = await reranker.rerank(
        query=query,
        chunks=chunks_to_rerank,
        top_k=settings.reranker_top_k,
    )

    # Volver a convertir a dicts para el estado del grafo
    # Usamos el método to_dict manual para ser consistentes
    reranked_chunks = [
        {
            "id": str(c.id),
            "document_id": c.document_id,
            "chunk_index": c.chunk_index,
            "content": c.content,
            "area": c.area,
            "score": c.score,
            "metadata": c.metadata,
            "document_name": c.document_name,
            "page": c.page_number or c.metadata.get("page_number", "N/A"),
        }
        for c in reranked_objs
    ]

    logger.info(
        "rerank: %d chunks rerankeados (top %d seleccionados)",
        len(reranked_chunks),
        settings.reranker_top_k,
    )

    return {"reranked_chunks": reranked_chunks}
