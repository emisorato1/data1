"""Búsqueda híbrida Vector + BM25 + RRF (Reciprocal Rank Fusion).

Implementa el motor de búsqueda principal del sistema RAG bancario.
Combina similaridad vectorial (cosine/halfvec) con búsqueda textual
(PostgreSQL tsvector) y fusiona rankings con RRF (k=60).

Pipeline:
    query → Gemini embedding (RETRIEVAL_QUERY)
         → Vector search (30 chunks, cosine)   ┐
         → BM25 search  (30 chunks, tsvector)  ┘ → RRF fusion → top-N chunks

Ver:
    - spec T4-S2-01
    - ADR-007: Búsqueda Híbrida Vector + BM25 + RRF
    - rag-retrieval/SKILL.md sección "Búsqueda Híbrida con RRF"
    - rag-retrieval/references/pgvector-store.md

Out of scope (spec T4-S2-01):
    - Reranking Vertex AI (T4-S2-02)
    - Cache semántico Redis (post-MVP)
    - Filtros por área funcional desde Security Mirror (post-MVP)
    - Query expansion / rewriting (post-MVP)
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.infrastructure.rag.retrieval.models import (
    RetrievalMetrics,
    StoredChunk,
)

if TYPE_CHECKING:
    from src.infrastructure.rag.embeddings.gemini_embeddings import (
        GeminiEmbeddingService,
    )
    from src.infrastructure.rag.vector_store.pgvector_store import PgVectorStore

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchConfig:
    """Parámetros configurables de la búsqueda híbrida.

    Los valores por defecto se leen de ``Settings`` (spec T3-S4-02) para
    permitir la configuración via variables de entorno.  Si se instancia
    sin argumentos, usa los defaults centralizados de ``settings.py``.

    Attributes
    ----------
    vector_k:
        Número de chunks a recuperar en la búsqueda vectorial.
        Pool amplio para maximizar recall antes de la fusión RRF.
    bm25_k:
        Número de chunks a recuperar en la búsqueda BM25.
    rrf_k:
        Parámetro de suavizado RRF (k=60 es el estándar de la literatura).
        Evita que posiciones muy altas dominen el score.
        Score RRF = Σ 1/(k + rank).
    top_k:
        Número de chunks únicos a retornar tras la fusión RRF.
    use_sql_function:
        Si ``True`` (default), delega a la función SQL ``hybrid_search``
        que ejecuta ambas búsquedas en un solo round-trip.
        Si ``False``, ejecuta búsquedas separadas y aplica RRF en Python
        (útil para testing o entornos sin la función SQL instalada).
    """

    vector_k: int = 30
    bm25_k: int = 30
    rrf_k: int = 60
    top_k: int = 20
    use_sql_function: bool = True

    @classmethod
    def from_settings(cls) -> HybridSearchConfig:
        """Crea la config leyendo los defaults de ``settings.py`` (T3-S4-02)."""
        from src.config.settings import settings

        return cls(
            rrf_k=settings.retrieval_rrf_k,
            top_k=settings.retrieval_top_k,
        )


class HybridSearchService:
    """Servicio de búsqueda híbrida para el pipeline RAG.

    Combina búsqueda vectorial (cosine similarity sobre halfvec) con
    búsqueda BM25 (PostgreSQL tsvector) y fusiona los rankings con
    Reciprocal Rank Fusion.

    Parameters
    ----------
    embedding_service:
        Instancia de ``GeminiEmbeddingService`` para obtener el embedding
        de la query con ``task_type=RETRIEVAL_QUERY``.
    vector_store:
        Instancia de ``PgVectorStore`` con acceso a la sesión de BD.
    config:
        Configuración opcional.  Si se omite usa ``HybridSearchConfig()``
        con valores por defecto.

    Example
    -------
    >>> svc = HybridSearchService(embedding_service, vector_store)
    >>> chunks, metrics = await svc.search(
    ...     query="Comunicación A 7632",
    ...     accessible_doc_ids=[1, 2, 3],
    ... )
    """

    def __init__(
        self,
        embedding_service: GeminiEmbeddingService,
        vector_store: PgVectorStore,
        config: HybridSearchConfig | None = None,
    ) -> None:
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._config = config or HybridSearchConfig()

    async def search(
        self,
        query: str,
        *,
        accessible_doc_ids: list[int] | None = None,
        top_k: int | None = None,
        rrf_k: int | None = None,
        vector_weight: float = 1.0,
        bm25_weight: float = 1.0,
    ) -> tuple[list[StoredChunk], RetrievalMetrics]:
        """Ejecuta la búsqueda híbrida y retorna los chunks más relevantes.

        Invariante de seguridad: si ``accessible_doc_ids`` es una lista
        vacía, retorna ``[]`` sin ejecutar ninguna consulta a la BD.

        Parameters
        ----------
        query:
            Texto de la pregunta del usuario.
        accessible_doc_ids:
            IDs de documentos a los que el usuario tiene acceso.
            ``None`` = sin filtro (solo en tests/desarrollo).
            ``[]`` = sin acceso a ningún documento → retorna vacío.
        top_k:
            Sobreescribe ``config.top_k`` para esta búsqueda.
        rrf_k:
            Sobreescribe ``config.rrf_k`` para esta búsqueda.
        vector_weight:
            Peso para scores del ranking vectorial en RRF (default 1.0).
        bm25_weight:
            Peso para scores del ranking BM25 en RRF (default 1.0).

        Returns
        -------
        tuple[list[StoredChunk], RetrievalMetrics]
            Chunks ordenados por score RRF descendente y métricas de latencia.
        """
        # Invariante: lista vacía → sin acceso → retornar vacío
        if accessible_doc_ids is not None and len(accessible_doc_ids) == 0:
            logger.warning("hybrid_search_empty_doc_ids query=%r", query)
            return [], RetrievalMetrics()

        effective_top_k = top_k if top_k is not None else self._config.top_k
        effective_rrf_k = rrf_k if rrf_k is not None else self._config.rrf_k

        metrics = RetrievalMetrics()
        t_total_start = time.monotonic()

        # 1. Embedding de la query (RETRIEVAL_QUERY)
        t0 = time.monotonic()
        query_embedding = await self._embedding_service.embed_query(query)
        metrics.embedding_ms = (time.monotonic() - t0) * 1000

        if self._config.use_sql_function:
            chunks, search_ms = await self._search_via_sql(
                query_embedding=query_embedding,
                query_text=query,
                match_count=effective_top_k,
                rrf_k=effective_rrf_k,
                accessible_doc_ids=accessible_doc_ids,
            )
            metrics.vector_search_ms = search_ms  # latencia total SQL

        else:
            chunks, v_ms, b_ms, rrf_ms = await self._search_via_python_rrf(
                query_embedding=query_embedding,
                query_text=query,
                accessible_doc_ids=accessible_doc_ids,
                top_k=effective_top_k,
                rrf_k=effective_rrf_k,
                vector_weight=vector_weight,
                bm25_weight=bm25_weight,
            )
            metrics.vector_search_ms = v_ms
            metrics.bm25_search_ms = b_ms
            metrics.rrf_fusion_ms = rrf_ms

        metrics.total_ms = (time.monotonic() - t_total_start) * 1000

        logger.info(
            "hybrid_search_done query=%r chunks=%d total_ms=%.1f",
            query,
            len(chunks),
            metrics.total_ms,
        )
        return chunks, metrics

    # ------------------------------------------------------------------
    # Estrategia A: función SQL hybrid_search (single round-trip)
    # ------------------------------------------------------------------

    async def _search_via_sql(
        self,
        query_embedding: list[float],
        query_text: str,
        match_count: int,
        rrf_k: int,
        accessible_doc_ids: list[int] | None,
    ) -> tuple[list[StoredChunk], float]:
        """Delega a la función SQL ``hybrid_search`` (migration 004)."""
        t0 = time.monotonic()
        rows = await self._vector_store.hybrid_search(
            query_embedding=query_embedding,
            query_text=query_text,
            match_count=match_count,
            rrf_k=rrf_k,
            accessible_doc_ids=accessible_doc_ids,
        )
        elapsed_ms = (time.monotonic() - t0) * 1000
        chunks = [StoredChunk.from_row(r) for r in rows]
        return chunks, elapsed_ms

    # ------------------------------------------------------------------
    # Estrategia B: búsquedas separadas + RRF en Python
    # ------------------------------------------------------------------

    async def _search_via_python_rrf(
        self,
        query_embedding: list[float],
        query_text: str,
        accessible_doc_ids: list[int] | None,
        top_k: int,
        rrf_k: int,
        vector_weight: float,
        bm25_weight: float,
    ) -> tuple[list[StoredChunk], float, float, float]:
        """Ejecuta vector + BM25 en paralelo y aplica RRF en Python."""
        # Lanzar ambas búsquedas en paralelo
        t_vec = time.monotonic()

        vector_rows, bm25_rows = await asyncio.gather(
            self._vector_store.similarity_search(
                query_embedding,
                k=self._config.vector_k,
                accessible_doc_ids=accessible_doc_ids,
            ),
            self._vector_store.bm25_search(
                query_text,
                k=self._config.bm25_k,
                accessible_doc_ids=accessible_doc_ids,
            ),
        )

        # Estimamos latencias por separado (gather las solapa)
        parallel_ms = (time.monotonic() - t_vec) * 1000
        vector_ms = parallel_ms
        bm25_ms = parallel_ms

        vector_chunks = [StoredChunk.from_row(r) for r in vector_rows]
        bm25_chunks = [StoredChunk.from_row(r) for r in bm25_rows]

        # RRF fusion
        t0 = time.monotonic()
        fused = self._reciprocal_rank_fusion(
            vector_results=vector_chunks,
            bm25_results=bm25_chunks,
            k=rrf_k,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight,
        )
        rrf_ms = (time.monotonic() - t0) * 1000

        return fused[:top_k], vector_ms, bm25_ms, rrf_ms

    # ------------------------------------------------------------------
    # RRF core
    # ------------------------------------------------------------------

    @staticmethod
    def _reciprocal_rank_fusion(
        vector_results: list[StoredChunk],
        bm25_results: list[StoredChunk],
        k: int = 60,
        vector_weight: float = 1.0,
        bm25_weight: float = 1.0,
    ) -> list[StoredChunk]:
        """Fusiona dos rankings con Reciprocal Rank Fusion.

        RRF score = Σ weight_i / (k + rank_i)

        Un documento que aparece en posición 1 en vector y posición 5 en BM25:
            score = 1/(60+1) + 1/(60+5) = 0.0164 + 0.0154 = 0.0318

        Parameters
        ----------
        vector_results:
            Chunks ordenados por similaridad cosine (mayor primero).
        bm25_results:
            Chunks ordenados por ts_rank_cd (mayor primero).
        k:
            Parámetro de suavizado (default 60).
        vector_weight:
            Factor multiplicador para el ranking vectorial.
        bm25_weight:
            Factor multiplicador para el ranking BM25.

        Returns
        -------
        list[StoredChunk]
            Lista ordenada por score RRF descendente.
            El campo ``score`` de cada chunk contiene el score RRF final.
        """
        scores: dict[str, float] = {}
        chunks_map: dict[str, StoredChunk] = {}

        for rank, chunk in enumerate(vector_results, start=1):
            cid = str(chunk.id)
            scores[cid] = scores.get(cid, 0.0) + vector_weight / (k + rank)
            chunks_map[cid] = chunk

        for rank, chunk in enumerate(bm25_results, start=1):
            cid = str(chunk.id)
            scores[cid] = scores.get(cid, 0.0) + bm25_weight / (k + rank)
            # Preferir el chunk de vector si ya estaba (tiene embedding)
            if cid not in chunks_map:
                chunks_map[cid] = chunk

        # Asignar scores RRF y ordenar
        sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
        result: list[StoredChunk] = []
        for cid in sorted_ids:
            c = chunks_map[cid]
            c.score = scores[cid]
            result.append(c)

        return result
