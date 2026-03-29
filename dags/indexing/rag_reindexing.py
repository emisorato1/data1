"""DAG de re-indexacion batch para el sistema RAG.

Re-procesa documentos existentes para actualizar embeddings o chunks
cuando se cambia la estrategia de chunking o el modelo de embeddings.

Soporta dos modos:
  - **incremental** (default): re-indexa solo documentos con status='stale'
  - **full**: re-indexa todos los documentos con status='indexed'

Schedule configurable via Airflow Variable `reindex_schedule` (default: @weekly).
Batch size configurable via Airflow Variable `reindex_batch_size` (default: 10).

Puede dispararse manualmente con:
  {"conf": {"mode": "full"}}  # o "incremental" (default)

Referencia: spec T3-S7-02 (DAG re-indexacion batch cron semanal/diario)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

from airflow.sdk import DAG, task

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default args
# ---------------------------------------------------------------------------
DEFAULT_ARGS = {
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=15),
}

# ---------------------------------------------------------------------------
# Schedule: read from Airflow Variable at parse time, fallback to @weekly
# ---------------------------------------------------------------------------
_DEFAULT_SCHEDULE = "@weekly"
_DEFAULT_BATCH_SIZE = 10


def _get_schedule() -> str:
    """Read reindex schedule from Airflow Variable (parse-time safe)."""
    try:
        from airflow.models import Variable

        return str(Variable.get("reindex_schedule", default_var=_DEFAULT_SCHEDULE))
    except Exception:
        return _DEFAULT_SCHEDULE


def _get_batch_size() -> int:
    """Read batch size from Airflow Variable."""
    try:
        from airflow.models import Variable

        return int(Variable.get("reindex_batch_size", default_var=str(_DEFAULT_BATCH_SIZE)))
    except Exception:
        return _DEFAULT_BATCH_SIZE


# ---------------------------------------------------------------------------
# Helpers: sync DB access via psycopg
# ---------------------------------------------------------------------------
def _get_db_url() -> str:
    """Get the DATABASE_URL from environment, suitable for sync psycopg."""
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return url


def _get_sync_connection():
    """Create a sync psycopg connection from DATABASE_URL."""
    import psycopg

    url = _get_db_url()
    if "+psycopg" in url:
        url = url.replace("+psycopg", "")
    elif "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    return psycopg.connect(url)


def _get_current_chunk_version(conn, document_id: int) -> int:
    """Get the current max version of chunks for a document."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(MAX(version), 0) FROM document_chunks WHERE document_id = %s",
            (document_id,),
        )
        row = cur.fetchone()
        return row[0] if row else 0


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="rag_reindexing_batch",
    description="Re-indexa documentos batch: select -> reindex -> update_status -> cleanup",
    start_date=datetime(2025, 1, 1),
    schedule=_get_schedule(),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["indexing", "rag", "reindexing", "batch"],
    params={
        "mode": "incremental",
    },
) as dag:

    @task()
    def select_documents(**context) -> list[dict]:
        """Select documents to re-index based on mode.

        - incremental (default): documents with status='stale'
        - full: all documents with status='indexed'

        Returns list of {document_id, file_path, current_version} dicts.
        """
        conf = context["dag_run"].conf or {}
        mode = conf.get("mode", "incremental")

        if mode not in ("incremental", "full"):
            raise ValueError(f"Invalid mode '{mode}'. Must be 'incremental' or 'full'.")

        batch_size = _get_batch_size()

        status_filter = "indexed" if mode == "full" else "stale"

        logger.info(
            "select_documents mode=%s status_filter=%s batch_size=%d",
            mode,
            status_filter,
            batch_size,
        )

        documents = []
        with _get_sync_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                    SELECT id, file_path
                    FROM documents
                    WHERE status = %s AND is_active = true
                    ORDER BY updated_at ASC
                    LIMIT %s
                    """,
                (status_filter, batch_size),
            )
            rows = cur.fetchall()

            for row in rows:
                doc_id, file_path = row[0], row[1]
                current_version = _get_current_chunk_version(conn, doc_id)
                documents.append(
                    {
                        "document_id": doc_id,
                        "file_path": file_path,
                        "current_version": current_version,
                        "new_version": current_version + 1,
                    }
                )

        logger.info("select_documents found=%d documents", len(documents))

        if not documents:
            logger.info("No documents to re-index. Skipping.")

        return documents

    @task()
    def batch_reindex(documents: list[dict]) -> list[dict]:
        """Re-index selected documents using the existing indexing pipeline.

        For each document:
        1. Load and chunk the document
        2. Generate new embeddings
        3. Store chunks with incremented version number

        Processes sequentially within this task. Parallelism is achieved
        by running multiple task instances via Airflow's task mapping.
        """
        if not documents:
            logger.info("No documents to re-index.")
            return []

        results = []

        for doc_info in documents:
            document_id = doc_info["document_id"]
            file_path_str = doc_info["file_path"]
            new_version = doc_info["new_version"]

            logger.info(
                "reindex_start document_id=%s version=%d",
                document_id,
                new_version,
            )

            try:
                from pathlib import Path

                # Use the same components as rag_indexing DAG
                from src.infrastructure.rag.chunking.adaptive_chunker import AdaptiveChunker
                from src.infrastructure.rag.embeddings.gemini_embeddings import GeminiEmbeddingService
                from src.infrastructure.rag.loaders.factory import LoaderFactory

                file_path = Path(file_path_str)

                # 1. Load and chunk
                loader_factory = LoaderFactory()
                loaded_doc = loader_factory.load(file_path)
                chunker = AdaptiveChunker()
                chunks = chunker.chunk(loaded_doc)

                logger.info(
                    "reindex_chunked document_id=%s chunks=%d",
                    document_id,
                    len(chunks),
                )

                # 2. Generate embeddings
                embedding_service = GeminiEmbeddingService()
                texts = [c.text for c in chunks]
                embeddings = asyncio.run(embedding_service.embed_documents(texts))

                # 3. Store with new version
                with _get_sync_connection() as conn:
                    with conn.cursor() as cur:
                        chunk_ids = []
                        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
                            area = chunk.metadata.get("area", "general") if chunk.metadata else "general"
                            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
                            metadata = chunk.metadata or {}

                            cur.execute(
                                """
                                INSERT INTO document_chunks
                                    (document_id, chunk_index, content, embedding,
                                     area, token_count, metadata, version)
                                VALUES
                                    (%s, %s, %s, CAST(%s AS halfvec), %s, %s, %s, %s)
                                RETURNING id
                                """,
                                (
                                    document_id,
                                    idx,
                                    chunk.text,
                                    embedding_str,
                                    area,
                                    chunk.token_count,
                                    json.dumps(metadata),
                                    new_version,
                                ),
                            )
                            row = cur.fetchone()
                            chunk_ids.append(str(row[0]))

                    conn.commit()

                results.append(
                    {
                        "document_id": document_id,
                        "new_version": new_version,
                        "chunk_count": len(chunk_ids),
                        "status": "success",
                    }
                )

                logger.info(
                    "reindex_done document_id=%s version=%d chunks=%d",
                    document_id,
                    new_version,
                    len(chunk_ids),
                )

            except Exception as exc:
                logger.error(
                    "reindex_failed document_id=%s error=%s",
                    document_id,
                    str(exc),
                    exc_info=True,
                )
                results.append(
                    {
                        "document_id": document_id,
                        "new_version": new_version,
                        "chunk_count": 0,
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        return results

    @task()
    def update_status(reindex_results: list[dict]) -> list[dict]:
        """Update document status after re-indexing.

        - Success: set status back to 'indexed'
        - Failed: set status to 'failed'
        """
        if not reindex_results:
            logger.info("No results to update.")
            return []

        with _get_sync_connection() as conn:
            with conn.cursor() as cur:
                for result in reindex_results:
                    document_id = result["document_id"]
                    new_status = "indexed" if result["status"] == "success" else "failed"

                    cur.execute(
                        "UPDATE documents SET status = %s, updated_at = now() WHERE id = %s",
                        (new_status, document_id),
                    )

                    logger.info(
                        "status_updated document_id=%s status=%s",
                        document_id,
                        new_status,
                    )

            conn.commit()

        return reindex_results

    @task()
    def cleanup_old_chunks(reindex_results: list[dict]) -> dict:
        """Delete old chunk versions after successful re-indexing.

        Only removes chunks from documents that were successfully re-indexed.
        Keeps only the latest version (new_version) for each document.
        """
        if not reindex_results:
            logger.info("No results to cleanup.")
            return {"cleaned": 0, "errors": 0}

        successful = [r for r in reindex_results if r["status"] == "success"]
        cleaned_total = 0
        error_count = 0

        with _get_sync_connection() as conn:
            with conn.cursor() as cur:
                for result in successful:
                    document_id = result["document_id"]
                    new_version = result["new_version"]

                    try:
                        cur.execute(
                            """
                            DELETE FROM document_chunks
                            WHERE document_id = %s AND version < %s
                            """,
                            (document_id, new_version),
                        )
                        deleted = cur.rowcount
                        cleaned_total += deleted

                        logger.info(
                            "cleanup_done document_id=%s old_chunks_deleted=%d kept_version=%d",
                            document_id,
                            deleted,
                            new_version,
                        )

                    except Exception as exc:
                        error_count += 1
                        logger.error(
                            "cleanup_failed document_id=%s error=%s",
                            document_id,
                            str(exc),
                            exc_info=True,
                        )

            conn.commit()

        summary = {
            "cleaned": cleaned_total,
            "errors": error_count,
            "documents_processed": len(successful),
        }
        logger.info("cleanup_complete summary=%s", summary)
        return summary

    # Task dependencies: select -> reindex -> update_status -> cleanup
    selected = select_documents()
    reindexed = batch_reindex(selected)
    updated = update_status(reindexed)
    cleanup_old_chunks(updated)
