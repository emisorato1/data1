"""Indexing service — orchestrates the full document indexing pipeline.

Pipeline stages: validate -> load -> chunk -> embed -> store.

This service operates within an existing SQLAlchemy session but does NOT
call ``session.commit()`` — the caller (e.g. Airflow DAG) is responsible
for committing or rolling back the transaction.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from sqlalchemy import text

if TYPE_CHECKING:
    import uuid
    from collections.abc import Callable
    from pathlib import Path

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.domain.repositories.document_repository import DocumentRepositoryBase
    from src.infrastructure.rag.chunking.adaptive_chunker import AdaptiveChunker
    from src.infrastructure.rag.embeddings.gemini_embeddings import GeminiEmbeddingService
    from src.infrastructure.rag.loaders.factory import LoaderFactory
    from src.infrastructure.rag.vector_store.pgvector_store import PgVectorStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IndexingResult:
    """Result of a document indexing operation."""

    document_id: int
    chunks_created: int
    tokens_total: int
    areas_distribution: dict[str, int]
    duration_seconds: float
    success: bool
    error: str | None = None


class IndexingService:
    """Orchestrates the full document indexing pipeline.

    Pipeline: validate -> load -> chunk -> embed -> store.

    Parameters
    ----------
    session:
        Active SQLAlchemy AsyncSession (caller manages commit/rollback).
    loader_factory:
        Selects the right loader (PDF/DOCX) by MIME type.
    chunker:
        Adaptive chunker that splits documents into chunks.
    embedding_service:
        Gemini embedding service for generating vectors.
    vector_store:
        PgVectorStore for persisting chunks with embeddings.
    document_repository:
        Repository for document CRUD operations.
    """

    def __init__(
        self,
        *,
        session: AsyncSession,
        loader_factory: LoaderFactory,
        chunker: AdaptiveChunker,
        embedding_service: GeminiEmbeddingService,
        vector_store: PgVectorStore,
        document_repository: DocumentRepositoryBase,
    ) -> None:
        self._session = session
        self._loader_factory = loader_factory
        self._chunker = chunker
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._document_repository = document_repository

    async def index_document(
        self,
        file_path: Path,
        document_id: int,
        *,
        pipeline_run_id: uuid.UUID | None = None,
        on_progress: Callable[[str, float], None] | None = None,
    ) -> IndexingResult:
        """Run the full indexing pipeline for a single document.

        Parameters
        ----------
        file_path:
            Path to the file on disk.
        document_id:
            ID of the document in the ``documents`` table.
        pipeline_run_id:
            Optional UUID of an existing ``pipeline_runs`` row to update.
            If provided, the row is transitioned from ``pending`` ->
            ``running`` -> ``completed``/``failed``.
        on_progress:
            Optional callback ``(stage_name, percentage)`` for tracking
            progress through the pipeline stages.

        Returns
        -------
        IndexingResult
            Summary of the indexing operation.
        """
        start_time = time.monotonic()

        # Mark pipeline run as running
        if pipeline_run_id is not None:
            await self._update_pipeline_run(
                pipeline_run_id,
                status="running",
                set_started=True,
            )

        try:
            result = await self._execute_pipeline(
                file_path=file_path,
                document_id=document_id,
                start_time=start_time,
                on_progress=on_progress,
            )

            # Mark pipeline run as completed
            if pipeline_run_id is not None:
                await self._update_pipeline_run(
                    pipeline_run_id,
                    status="completed",
                    set_finished=True,
                )

            return result

        except Exception as exc:
            duration = time.monotonic() - start_time
            error_msg = str(exc)

            logger.error(
                "indexing_failed document_id=%s error=%s duration=%.2f",
                document_id,
                error_msg,
                duration,
                exc_info=True,
            )

            # Mark pipeline run as failed
            if pipeline_run_id is not None:
                await self._update_pipeline_run(
                    pipeline_run_id,
                    status="failed",
                    set_finished=True,
                    error_message=error_msg,
                )

            return IndexingResult(
                document_id=document_id,
                chunks_created=0,
                tokens_total=0,
                areas_distribution={},
                duration_seconds=duration,
                success=False,
                error=error_msg,
            )

    # ------------------------------------------------------------------
    # Private: pipeline execution
    # ------------------------------------------------------------------

    async def _execute_pipeline(
        self,
        *,
        file_path: Path,
        document_id: int,
        start_time: float,
        on_progress: Callable[[str, float], None] | None,
    ) -> IndexingResult:
        """Execute all pipeline stages sequentially."""

        # 1. Check duplicates by file hash
        self._notify(on_progress, "checking_duplicates", 0.05)

        file_hash = self._compute_file_hash(file_path)
        existing = await self._document_repository.find_by_hash(file_hash)
        if existing is not None and existing.id != document_id:
            logger.warning(
                "duplicate_document existing_id=%s new_id=%s file_hash=%s",
                existing.id,
                document_id,
                file_hash,
            )

        # 2. Load document
        self._notify(on_progress, "loading", 0.10)

        loaded_doc = self._loader_factory.load(file_path)

        logger.info(
            "document_loaded document_id=%s filename=%s pages=%d",
            document_id,
            file_path.name,
            loaded_doc.pages,
        )

        # 3. Chunk document
        self._notify(on_progress, "chunking", 0.20)

        chunks = self._chunker.chunk(loaded_doc)

        logger.info(
            "document_chunked document_id=%s chunks=%d tokens=%d",
            document_id,
            len(chunks),
            sum(c.token_count for c in chunks),
        )

        # 4. Generate embeddings
        self._notify(on_progress, "embedding", 0.40)

        texts = [c.text for c in chunks]

        def _embedding_progress(batch_num: int, total_batches: int, total_embedded: int) -> None:
            if on_progress is not None:
                pct = 0.40 + (0.40 * batch_num / max(total_batches, 1))
                on_progress("embedding", pct)

        embeddings = await self._embedding_service.embed_documents(
            texts,
            on_progress=_embedding_progress,
        )

        # 5. Store chunks in pgvector
        self._notify(on_progress, "storing", 0.85)

        chunk_tuples = self._build_chunk_tuples(chunks, embeddings)
        chunk_ids = await self._vector_store.add_chunks(
            document_id=document_id,
            chunks=chunk_tuples,
        )

        # 6. Update document metadata
        self._notify(on_progress, "finalizing", 0.95)

        areas_dist = self._compute_areas_distribution(chunks)

        await self._document_repository.update_after_indexing(
            document_id,
            file_hash=file_hash,
            chunk_count=len(chunks),
            areas=areas_dist,
        )

        self._notify(on_progress, "completed", 1.0)

        duration = time.monotonic() - start_time

        logger.info(
            "indexing_completed document_id=%s chunks=%d duration=%.2f",
            document_id,
            len(chunk_ids),
            duration,
        )

        return IndexingResult(
            document_id=document_id,
            chunks_created=len(chunk_ids),
            tokens_total=sum(c.token_count for c in chunks),
            areas_distribution=areas_dist,
            duration_seconds=duration,
            success=True,
        )

    # ------------------------------------------------------------------
    # Private: helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_file_hash(file_path: Path) -> str:
        """Compute SHA-256 hash of the file for duplicate detection."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(8192), b""):
                sha256.update(block)
        return sha256.hexdigest()

    @staticmethod
    def _build_chunk_tuples(
        chunks: list[Any],
        embeddings: list[list[float]],
    ) -> list[tuple[int, str, list[float], str, int | None, dict | None]]:
        """Transform Chunk objects + embeddings into the tuple format
        expected by ``PgVectorStore.add_chunks``.

        Format: ``(chunk_index, content, embedding, area, token_count, metadata)``
        """
        result: list[tuple[int, str, list[float], str, int | None, dict | None]] = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
            area = chunk.metadata.get("area", "general") if chunk.metadata else "general"
            result.append(
                (
                    idx,
                    chunk.text,
                    embedding,
                    area,
                    chunk.token_count,
                    chunk.metadata,
                )
            )
        return result

    @staticmethod
    def _compute_areas_distribution(chunks: list[Any]) -> dict[str, int]:
        """Count chunks per functional area."""
        dist: dict[str, int] = {}
        for chunk in chunks:
            area = chunk.metadata.get("area", "general") if chunk.metadata else "general"
            dist[area] = dist.get(area, 0) + 1
        return dist

    @staticmethod
    def _notify(
        on_progress: Callable[[str, float], None] | None,
        stage: str,
        percentage: float,
    ) -> None:
        """Fire the progress callback if provided."""
        if on_progress is not None:
            on_progress(stage, percentage)

    async def _update_pipeline_run(
        self,
        run_id: uuid.UUID,
        *,
        status: str,
        set_started: bool = False,
        set_finished: bool = False,
        error_message: str | None = None,
    ) -> None:
        """Update a ``pipeline_runs`` row via raw SQL.

        Uses the database ``now()`` function for timestamps, avoiding
        Python-side timezone gymnastics and keeping the application layer
        free of ORM model imports.
        """
        clauses = ["status = :status"]
        params: dict[str, Any] = {"run_id": run_id, "status": status}

        if set_started:
            clauses.append("started_at = now()")
        if set_finished:
            clauses.append("finished_at = now()")
        if error_message is not None:
            clauses.append("error_message = :error_message")
            params["error_message"] = error_message

        sql = f"UPDATE pipeline_runs SET {', '.join(clauses)} WHERE id = :run_id"  # noqa: S608
        await self._session.execute(text(sql), params)

        logger.info(
            "pipeline_run_updated run_id=%s status=%s",
            run_id,
            status,
        )
