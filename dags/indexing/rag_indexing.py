"""DAG de indexacion de documentos para el sistema RAG.

Orquesta el pipeline completo de indexacion: validacion de archivo,
carga y chunking, generacion de embeddings, almacenamiento en pgvector
y actualizacion de estado.

Cada task usa los componentes de la libreria (LoaderFactory, AdaptiveChunker,
GeminiEmbeddingService, PgVectorStore) directamente — no duplica logica.
La orquestacion usa sync psycopg para DB (compatible con Airflow 3 / SA 1.4)
y asyncio.run() para el servicio de embeddings (Gemini SDK es async-native).

Triggerable manualmente desde la UI de Airflow o via REST API con:
  {"conf": {"document_id": 123, "file_path": "/path/to/file.pdf"}}

Soporta URIs de GCS (gs://bucket/path) — descarga el archivo al worker
automaticamente usando la SA de Workload Identity.

Si solo se provee document_id (sin file_path), busca file_path en la tabla
documents de la BD.

Referencia: spec T3-S2-03 (Airflow DAG de indexacion)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from airflow.sdk import DAG, task

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default args: retry 2 times with exponential backoff per task
# ---------------------------------------------------------------------------
DEFAULT_ARGS = {
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=10),
}


# ---------------------------------------------------------------------------
# Helpers: sync DB access via psycopg (no SQLAlchemy async needed)
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
    # Strip the SQLAlchemy prefix to get a plain libpq conninfo
    # e.g. postgresql+psycopg://user:pass@host:5432/db -> postgresql://user:pass@host:5432/db
    if "+psycopg" in url:
        url = url.replace("+psycopg", "")
    elif "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    return psycopg.connect(url)


def _create_pipeline_run(document_id: int, dag_run_id: str) -> str:
    """Create a pipeline_runs row in 'pending' status. Returns the run UUID."""
    run_id = str(uuid.uuid4())
    with _get_sync_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pipeline_runs (id, document_id, dag_run_id, status)
                VALUES (%s, %s, %s, 'pending')
                """,
                (run_id, document_id, dag_run_id),
            )
        conn.commit()
    logger.info("pipeline_run_created run_id=%s document_id=%s", run_id, document_id)
    return run_id


def _update_pipeline_run(
    run_id: str,
    status: str,
    *,
    set_started: bool = False,
    set_finished: bool = False,
    error_message: str | None = None,
) -> None:
    """Update a pipeline_runs row via sync psycopg."""
    clauses = ["status = %s"]
    params: list = [status]

    if set_started:
        clauses.append("started_at = now()")
    if set_finished:
        clauses.append("finished_at = now()")
    if error_message is not None:
        clauses.append("error_message = %s")
        params.append(error_message)

    params.append(run_id)
    sql = f"UPDATE pipeline_runs SET {', '.join(clauses)} WHERE id = %s"  # noqa: S608

    with _get_sync_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    logger.info("pipeline_run_updated run_id=%s status=%s", run_id, status)


# ---------------------------------------------------------------------------
# GCS helpers
# ---------------------------------------------------------------------------
def _download_from_gcs(gcs_uri: str, dest_dir: str | None = None) -> Path:
    """Download a file from GCS to a local temp directory.

    Args:
        gcs_uri: URI like gs://bucket/path/to/file.pdf
        dest_dir: Optional directory for download. If None, uses a tempdir.

    Returns:
        Path to the downloaded local file.
    """
    from google.cloud import storage

    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"Not a GCS URI: {gcs_uri}")

    # Parse gs://bucket/path/to/file.pdf
    without_scheme = gcs_uri[5:]
    bucket_name, _, blob_path = without_scheme.partition("/")
    if not blob_path:
        raise ValueError(f"No object path in GCS URI: {gcs_uri}")

    filename = blob_path.rsplit("/", 1)[-1]
    if dest_dir is None:
        dest_dir = tempfile.mkdtemp(prefix="airflow_gcs_")
    local_path = Path(dest_dir) / filename

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.download_to_filename(str(local_path))

    logger.info(
        "gcs_download_complete uri=%s local=%s size=%d",
        gcs_uri,
        local_path,
        local_path.stat().st_size,
    )
    return local_path


def _lookup_file_path(document_id: int) -> str:
    """Look up the file_path for a document_id from the documents table."""
    with _get_sync_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT file_path FROM documents WHERE id = %s",
            (document_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Document id={document_id} not found in database")
        return row[0]


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="rag_indexing",
    description="Indexa un documento en el sistema RAG: validate -> chunk -> embed -> store",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["indexing", "rag", "core"],
    params={
        "document_id": None,
        "file_path": None,
    },
) as dag:

    @task()
    def validate_file(**context) -> dict:
        """Validate the input file exists, is accessible, and has an allowed type.

        Uses LoaderFactory's FileValidator under the hood (magic bytes detection).
        Creates a pipeline_runs record to track this execution.

        Supports GCS URIs (gs://bucket/path) — downloads to worker temp dir.
        If only document_id is provided, looks up file_path from the DB.
        """
        conf = context["dag_run"].conf or {}
        document_id = conf.get("document_id")
        file_path_str = conf.get("file_path")

        # If no file_path, look it up from the documents table
        if not file_path_str and document_id:
            file_path_str = _lookup_file_path(int(document_id))
            logger.info(
                "file_path_from_db document_id=%s file_path=%s",
                document_id,
                file_path_str,
            )

        if not document_id or not file_path_str:
            raise ValueError(
                "DAG requires 'document_id' (and optionally 'file_path') in conf. "
                f"Received: document_id={document_id}, file_path={file_path_str}"
            )

        document_id = int(document_id)
        original_path = file_path_str

        # If GCS URI, download to local temp
        if file_path_str.startswith("gs://"):
            local_path = _download_from_gcs(file_path_str)
            file_path = local_path
        else:
            file_path = Path(file_path_str)

        logger.info("validate_file_start document_id=%s file_path=%s", document_id, file_path)

        # Create pipeline run record
        dag_run_id = context["dag_run"].run_id
        pipeline_run_id = _create_pipeline_run(document_id, dag_run_id)
        _update_pipeline_run(pipeline_run_id, "running", set_started=True)

        # Validate using the library's FileValidator (same as LoaderFactory uses)
        from src.infrastructure.rag.loaders.validator import FileValidator

        validator = FileValidator()
        try:
            mime_type = validator.validate(file_path)
        except Exception as exc:
            _update_pipeline_run(
                pipeline_run_id,
                "failed",
                set_finished=True,
                error_message=f"File validation failed: {exc}",
            )
            raise

        # Compute file hash for duplicate detection (same algo as IndexingService)
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(8192), b""):
                sha256.update(block)
        file_hash = sha256.hexdigest()

        logger.info(
            "validate_file_done document_id=%s mime=%s hash=%s",
            document_id,
            mime_type,
            file_hash[:16],
        )

        return {
            "document_id": document_id,
            "file_path": str(file_path),  # local path (after GCS download if applicable)
            "original_path": original_path,  # original GCS URI or local path
            "mime_type": mime_type,
            "file_hash": file_hash,
            "pipeline_run_id": pipeline_run_id,
        }

    @task()
    def load_and_chunk(validation_result: dict) -> dict:
        """Load the document and split into chunks.

        Uses LoaderFactory (selects PDF/DOCX loader by MIME type) and
        AdaptiveChunker (~1000 tokens, 15% overlap, tables preserved).
        """
        document_id = validation_result["document_id"]
        file_path = Path(validation_result["file_path"])
        pipeline_run_id = validation_result["pipeline_run_id"]

        logger.info("load_and_chunk_start document_id=%s", document_id)

        try:
            from src.infrastructure.rag.chunking.adaptive_chunker import AdaptiveChunker
            from src.infrastructure.rag.loaders.factory import LoaderFactory

            loader_factory = LoaderFactory()
            loaded_doc = loader_factory.load(file_path)

            logger.info(
                "document_loaded document_id=%s pages=%d",
                document_id,
                loaded_doc.pages,
            )

            chunker = AdaptiveChunker()
            chunks = chunker.chunk(loaded_doc)

            logger.info(
                "document_chunked document_id=%s chunks=%d tokens=%d",
                document_id,
                len(chunks),
                sum(c.token_count for c in chunks),
            )

            # Serialize chunks for XCom (Airflow inter-task communication)
            serialized_chunks = [
                {
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                    "token_count": chunk.token_count,
                }
                for chunk in chunks
            ]

            return {
                **validation_result,
                "chunks": serialized_chunks,
                "chunk_count": len(chunks),
                "total_tokens": sum(c.token_count for c in chunks),
                "pages": loaded_doc.pages,
            }

        except Exception as exc:
            _update_pipeline_run(
                pipeline_run_id,
                "failed",
                set_finished=True,
                error_message=f"Load/chunk failed: {exc}",
            )
            raise

    @task()
    def generate_embeddings(chunk_result: dict) -> dict:
        """Generate Gemini embeddings for all chunks.

        Uses GeminiEmbeddingService (768-d, L2-normalized, batched in groups of 100).
        Runs the async embedding service via asyncio.run().
        """
        document_id = chunk_result["document_id"]
        pipeline_run_id = chunk_result["pipeline_run_id"]
        chunks = chunk_result["chunks"]

        logger.info(
            "generate_embeddings_start document_id=%s chunk_count=%d",
            document_id,
            len(chunks),
        )

        try:
            from src.infrastructure.rag.embeddings.gemini_embeddings import GeminiEmbeddingService

            embedding_service = GeminiEmbeddingService()
            texts = [c["text"] for c in chunks]

            # Bridge async -> sync: Gemini SDK is async-native
            embeddings = asyncio.run(embedding_service.embed_documents(texts))

            logger.info(
                "embeddings_generated document_id=%s count=%d dims=%d",
                document_id,
                len(embeddings),
                len(embeddings[0]) if embeddings else 0,
            )

            # Don't put full embeddings in XCom — they're too large.
            # Instead, serialize to a temp file or pass as compressed JSON.
            # For now, we pass them directly since Airflow 3 uses DB-backed XCom
            # and typical document sizes (< 500 chunks * 768 floats) fit.
            return {
                "document_id": chunk_result["document_id"],
                "file_path": chunk_result["file_path"],
                "file_hash": chunk_result["file_hash"],
                "pipeline_run_id": pipeline_run_id,
                "chunks": chunks,
                "embeddings": embeddings,
                "chunk_count": chunk_result["chunk_count"],
                "total_tokens": chunk_result["total_tokens"],
            }

        except Exception as exc:
            _update_pipeline_run(
                pipeline_run_id,
                "failed",
                set_finished=True,
                error_message=f"Embedding generation failed: {exc}",
            )
            raise

    @task()
    def store_in_pgvector(embedding_result: dict) -> dict:
        """Store chunks with embeddings in pgvector.

        Uses sync psycopg to INSERT into document_chunks table with halfvec(768).
        Mirrors the logic of PgVectorStore.add_chunks() but using sync DB access.
        """
        document_id = embedding_result["document_id"]
        pipeline_run_id = embedding_result["pipeline_run_id"]
        chunks = embedding_result["chunks"]
        embeddings = embedding_result["embeddings"]
        file_hash = embedding_result["file_hash"]

        logger.info(
            "store_in_pgvector_start document_id=%s chunks=%d",
            document_id,
            len(chunks),
        )

        try:
            chunk_ids = []
            areas_distribution: dict[str, int] = {}

            with _get_sync_connection() as conn:
                with conn.cursor() as cur:
                    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
                        area = chunk.get("metadata", {}).get("area", "general") if chunk.get("metadata") else "general"
                        token_count = chunk.get("token_count")
                        metadata = chunk.get("metadata", {})
                        embedding_str = "[" + ",".join(map(str, embedding)) + "]"

                        cur.execute(
                            """
                            INSERT INTO document_chunks
                                (document_id, chunk_index, content, embedding, area, token_count, metadata)
                            VALUES
                                (%s, %s, %s, CAST(%s AS halfvec), %s, %s, %s)
                            RETURNING id
                            """,
                            (
                                document_id,
                                idx,
                                chunk["text"],
                                embedding_str,
                                area,
                                token_count,
                                json.dumps(metadata),
                            ),
                        )
                        row = cur.fetchone()
                        chunk_ids.append(str(row[0]))

                        # Track areas distribution
                        areas_distribution[area] = areas_distribution.get(area, 0) + 1

                    # Update document metadata (file_hash + indexing results)
                    # First get current metadata
                    cur.execute(
                        "SELECT metadata FROM documents WHERE id = %s",
                        (document_id,),
                    )
                    row = cur.fetchone()
                    current_meta = row[0] if row and row[0] else {}
                    if isinstance(current_meta, str):
                        current_meta = json.loads(current_meta)

                    current_meta["indexing"] = {
                        "chunk_count": len(chunks),
                        "areas": areas_distribution,
                    }

                    cur.execute(
                        "UPDATE documents SET file_hash = %s, metadata = %s WHERE id = %s",
                        (file_hash, json.dumps(current_meta), document_id),
                    )

                conn.commit()

            logger.info(
                "store_in_pgvector_done document_id=%s chunks_stored=%d",
                document_id,
                len(chunk_ids),
            )

            return {
                "document_id": document_id,
                "pipeline_run_id": pipeline_run_id,
                "chunk_count": len(chunk_ids),
                "total_tokens": embedding_result["total_tokens"],
                "areas_distribution": areas_distribution,
            }

        except Exception as exc:
            _update_pipeline_run(
                pipeline_run_id,
                "failed",
                set_finished=True,
                error_message=f"Storage failed: {exc}",
            )
            raise

    @task()
    def update_status(store_result: dict) -> dict:
        """Mark the pipeline run as completed and emit final summary.

        Updates the pipeline_runs row to 'completed' with finished_at timestamp.
        """
        document_id = store_result["document_id"]
        pipeline_run_id = store_result["pipeline_run_id"]
        chunk_count = store_result["chunk_count"]
        total_tokens = store_result["total_tokens"]
        areas = store_result["areas_distribution"]

        logger.info(
            "update_status_start document_id=%s pipeline_run_id=%s",
            document_id,
            pipeline_run_id,
        )

        _update_pipeline_run(pipeline_run_id, "completed", set_finished=True)

        summary = {
            "document_id": document_id,
            "pipeline_run_id": pipeline_run_id,
            "status": "completed",
            "chunk_count": chunk_count,
            "total_tokens": total_tokens,
            "areas_distribution": areas,
        }

        logger.info("indexing_completed document_id=%s summary=%s", document_id, summary)
        print(f"Indexing completed for document {document_id}: {chunk_count} chunks, {total_tokens} tokens")

        return summary

    # Task dependencies: validate -> chunk -> embed -> store -> update
    validated = validate_file()
    chunked = load_and_chunk(validated)
    embedded = generate_embeddings(chunked)
    stored = store_in_pgvector(embedded)
    update_status(stored)
