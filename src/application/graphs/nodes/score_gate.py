"""Nodo score_gate: evalua calidad de chunks post-reranking.

Determina si los documentos recuperados son suficientemente relevantes
para generar una respuesta, usando los scores de reranking como indicador.

Ubicacion en el grafo: rerank -> score_gate -> [routing condicional]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.config.settings import settings
from src.infrastructure.observability.langfuse_client import observe

if TYPE_CHECKING:
    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)


@observe(name="rag_score_gate")
def score_gate_node(state: RAGState) -> dict:
    """Evalua la calidad de los chunks rerankeados y clasifica la confianza.

    Resultado ``retrieval_confidence``:
    - ``"suficiente"``: max score >= reranking_threshold → continuar a generate.
    - ``"insuficiente"``: max score < similarity_threshold → fallback.
    - ``"ambiguo"``: score entre ambos umbrales → escalar a topic_classifier.

    Caso especial: si no hay chunks, clasifica como ``"sin_contexto"``
    (tratado como insuficiente por el routing).
    """
    reranked_chunks: list[dict] = state.get("reranked_chunks", [])

    if not reranked_chunks:
        logger.info("score_gate: no chunks retrieved — sin_contexto")
        return {"retrieval_confidence": "insuficiente"}

    max_score = max(chunk.get("score", 0.0) for chunk in reranked_chunks)

    high_threshold = settings.reranking_threshold
    low_threshold = settings.similarity_threshold

    if max_score >= high_threshold:
        confidence = "suficiente"
    elif max_score < low_threshold:
        confidence = "insuficiente"
    else:
        confidence = "ambiguo"

    logger.info(
        "score_gate: confidence=%s max_score=%.3f thresholds=[%.2f, %.2f] n_chunks=%d",
        confidence,
        max_score,
        low_threshold,
        high_threshold,
        len(reranked_chunks),
    )
    return {"retrieval_confidence": confidence}
