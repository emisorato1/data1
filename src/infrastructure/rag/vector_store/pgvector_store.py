"""pgvector storage for document chunk embeddings.

Writes normalized ``halfvec(768)`` embeddings into the existing
``document_chunks`` table and provides:

* Cosine-distance **vector search** via HNSW index (migration 002).
* **BM25 full-text search** via tsvector/GIN index (migration 004).
* **Hybrid search** via the SQL function ``hybrid_search`` that fuses both
  rankings with Reciprocal Rank Fusion (RRF, k=60).

See: rag-indexing/SKILL.md  (PgVectorStore section)
     rag-retrieval/SKILL.md  (Búsqueda Híbrida section)
     database-setup/references/sql-schema.md
     specs/sprint-2/T4-S2-01_hybrid-search.md
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from sqlalchemy import text

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class PgVectorStore:
    """Thin wrapper around pgvector for document-chunk embeddings.

    Parameters
    ----------
    session:
        An active SQLAlchemy ``AsyncSession``.  The caller is responsible for
        committing / rolling back — this class does **not** call ``commit()``.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------

    async def add_chunks(
        self,
        document_id: int,
        chunks: list[tuple[int, str, list[float], str, int | None, dict | None]],
    ) -> list[uuid.UUID]:
        """Insert (or update) chunk embeddings into ``document_chunks``.

        Parameters
        ----------
        document_id:
            FK to ``documents.id``.
        chunks:
            List of tuples ``(chunk_index, content, embedding, area, token_count, metadata)``.
            *embedding* must already be L2-normalized.

        Returns
        -------
        list[uuid.UUID]
            The generated UUIDs for each inserted row.
        """
        chunk_ids: list[uuid.UUID] = []

        for chunk_index, content, embedding, area, token_count, metadata in chunks:
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"

            result = await self._session.execute(
                text("""
                    INSERT INTO document_chunks
                        (document_id, chunk_index, content, embedding, area, token_count, metadata)
                    VALUES
                        (:doc_id, :idx, :content, CAST(:embedding AS halfvec), :area, :tokens, :meta)
                    RETURNING id
                """),
                {
                    "doc_id": document_id,
                    "idx": chunk_index,
                    "content": content,
                    "embedding": embedding_str,
                    "area": area,
                    "tokens": token_count,
                    "meta": json.dumps(metadata or {}),
                },
            )
            chunk_ids.append(result.scalar_one())

        logger.info(
            "chunks_stored document_id=%s count=%d",
            document_id,
            len(chunk_ids),
        )
        return chunk_ids

    # ------------------------------------------------------------------
    # Read path — vector search
    # ------------------------------------------------------------------

    async def similarity_search(
        self,
        query_embedding: list[float],
        *,
        k: int = 30,
        accessible_doc_ids: list[int] | None = None,
        filter_area: str | None = None,
        # Legacy alias kept for backwards compatibility
        limit: int | None = None,
        area: str | None = None,
    ) -> list[dict]:
        """Find the most similar chunks by cosine distance.

        Uses the ``<=>`` operator which leverages the HNSW index on
        ``document_chunks.embedding``.

        Parameters
        ----------
        query_embedding:
            L2-normalized query vector (768-d).
        k:
            Maximum number of results (default 30 for hybrid pool).
        accessible_doc_ids:
            If provided, restricts results to these document IDs (security filter).
        filter_area:
            Optional functional area filter (e.g. ``"riesgos"``).
        limit:
            Deprecated alias for ``k`` — kept for backwards compatibility.
        area:
            Deprecated alias for ``filter_area`` — kept for backwards compatibility.

        Returns
        -------
        list[dict]
            Dicts with keys ``id``, ``document_id``, ``chunk_index``,
            ``content``, ``area``, ``metadata``, ``score``.
        """
        # Backwards compatibility
        effective_limit = limit if limit is not None else k
        effective_area = area if area is not None else filter_area

        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        where_clauses = ["dc.embedding IS NOT NULL", "d.is_active = true"]
        params: dict = {
            "embedding": embedding_str,
            "limit": effective_limit,
        }

        if accessible_doc_ids is not None:
            where_clauses.append("dc.document_id = ANY(:doc_ids)")
            params["doc_ids"] = accessible_doc_ids

        if effective_area:
            where_clauses.append("dc.area = :area")
            params["area"] = effective_area

        where_sql = " AND ".join(where_clauses)

        result = await self._session.execute(
            text(f"""
                SELECT
                    dc.id,
                    dc.document_id,
                    dc.chunk_index,
                    dc.content,
                    dc.area,
                    dc.metadata,
                    d.filename                                          AS document_name,
                    1 - (dc.embedding <=> CAST(:embedding AS halfvec)) AS score
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE {where_sql}
                ORDER BY dc.embedding <=> CAST(:embedding AS halfvec)
                LIMIT :limit
            """),  # noqa: S608
            params,
        )

        rows = result.fetchall()
        return [
            {
                "id": row.id,
                "document_id": row.document_id,
                "chunk_index": row.chunk_index,
                "content": row.content,
                "area": row.area,
                "metadata": row.metadata,
                "document_name": row.document_name,
                "score": float(row.score),
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Read path — BM25 search
    # ------------------------------------------------------------------

    async def bm25_search(
        self,
        query_text: str,
        *,
        k: int = 30,
        accessible_doc_ids: list[int] | None = None,
        filter_area: str | None = None,
    ) -> list[dict]:
        """Full-text BM25 search using PostgreSQL ``tsvector`` / ``tsquery``.

        Requires the ``content_tsv`` column and GIN index created in
        migration ``004_bm25_indexes.py``.

        Parameters
        ----------
        query_text:
            Raw query string (converted to ``tsquery`` internally).
        k:
            Maximum number of results (default 30 for hybrid pool).
        accessible_doc_ids:
            If provided, restricts results to these document IDs (security filter).
        filter_area:
            Optional functional area filter.

        Returns
        -------
        list[dict]
            Dicts with keys ``id``, ``document_id``, ``chunk_index``,
            ``content``, ``area``, ``metadata``, ``score``.
        """
        where_clauses = [
            "d.is_active = true",
            "dc.content_tsv @@ plainto_tsquery('spanish', :query)",
        ]
        params: dict = {"query": query_text, "limit": k}

        if accessible_doc_ids is not None:
            where_clauses.append("dc.document_id = ANY(:doc_ids)")
            params["doc_ids"] = accessible_doc_ids

        if filter_area:
            where_clauses.append("dc.area = :area")
            params["area"] = filter_area

        where_sql = " AND ".join(where_clauses)

        result = await self._session.execute(
            text(f"""
                SELECT
                    dc.id,
                    dc.document_id,
                    dc.chunk_index,
                    dc.content,
                    dc.area,
                    dc.metadata,
                    d.filename                                                        AS document_name,
                    ts_rank_cd(dc.content_tsv, plainto_tsquery('spanish', :query))   AS score
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE {where_sql}
                ORDER BY ts_rank_cd(dc.content_tsv, plainto_tsquery('spanish', :query)) DESC
                LIMIT :limit
            """),  # noqa: S608
            params,
        )

        rows = result.fetchall()
        return [
            {
                "id": row.id,
                "document_id": row.document_id,
                "chunk_index": row.chunk_index,
                "content": row.content,
                "area": row.area,
                "metadata": row.metadata,
                "document_name": row.document_name,
                "score": float(row.score),
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Read path — Hybrid search via SQL function
    # ------------------------------------------------------------------

    async def hybrid_search(
        self,
        query_embedding: list[float],
        query_text: str,
        *,
        match_count: int = 50,
        rrf_k: int = 60,
        accessible_doc_ids: list[int] | None = None,
    ) -> list[dict]:
        """Hybrid search delegating to the PostgreSQL ``hybrid_search`` function.

        The SQL function (migration 004) runs vector search and BM25 in
        parallel CTEs and fuses rankings with Reciprocal Rank Fusion (k=60).

        Parameters
        ----------
        query_embedding:
            L2-normalized query vector (768-d).
        query_text:
            Raw query string for BM25.
        match_count:
            Number of chunks to return after fusion (default 50).
        rrf_k:
            RRF smoothing constant (default 60 — literature standard).
        accessible_doc_ids:
            If provided, restricts search to these document IDs.

        Returns
        -------
        list[dict]
            Dicts with keys ``id``, ``document_id``, ``chunk_index``,
            ``content``, ``area``, ``metadata``, ``document_name``, ``score``.
        """
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        result = await self._session.execute(
            text("""
                SELECT * FROM hybrid_search(
                    CAST(:embedding AS halfvec),
                    :query_text,
                    :match_count,
                    :rrf_k,
                    :doc_ids
                )
            """),
            {
                "embedding": embedding_str,
                "query_text": query_text,
                "match_count": match_count,
                "rrf_k": rrf_k,
                "doc_ids": accessible_doc_ids,
            },
        )

        rows = result.fetchall()
        return [
            {
                "id": row.id,
                "document_id": row.document_id,
                "chunk_index": row.chunk_index,
                "content": row.content,
                "area": row.area,
                "metadata": row.metadata,
                "document_name": row.document_name,
                "score": float(row.rrf_score),
            }
            for row in rows
        ]
