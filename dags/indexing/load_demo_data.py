"""DAG de carga masiva de documentos para el sistema RAG.

Escanea un bucket de GCS configurable (default: macro-ai-dev-backend-samples)
o una carpeta local (modo desarrollo) y ejecuta el pipeline de indexacion para
cada documento PDF/DOCX encontrado. Reutiliza los mismos componentes de
infraestructura que el DAG rag_indexing (LoaderFactory, AdaptiveChunker,
GeminiEmbeddingService).

Mapea carpetas del bucket a areas funcionales del banco:
  RRHH/ -> rrhh
  002 _ Cuentas/ -> operaciones
  004 _ Prestamos/ -> operaciones
  005 _ Tarjeta de debito/ -> operaciones
  007 _ Canales automaticos y claves/ -> tecnologia
  008 _ Cobros y pagos/ -> operaciones
  010 _ Paquetes/ -> operaciones
  011 _ Tarjeta de credito/ -> operaciones
  CAT/ -> operaciones

Omite la carpeta muestras-banco/ (es duplicado de las carpetas raiz).

Triggerable manualmente desde la UI de Airflow o via REST API con:
  {"conf": {"gcs_bucket": "macro-ai-dev-backend-samples", "skip_existing": true}}
  {"conf": {"folder_path": "data/demo/", "skip_existing": true}}  (modo local)

Parametros:
  - gcs_bucket: nombre del bucket GCS (sin gs://) (default: macro-ai-dev-backend-samples)
  - folder_path: ruta relativa a /opt/airflow para modo local (default: null = usa GCS)
  - skip_existing: si es true, omite documentos ya indexados por file_hash (default: true)

Referencia: spec T3-S4-01 (Carga masiva dataset demo via Airflow)
            spec T3-S7-03 (Modo carpeta local para load_demo_data DAG)
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import logging
import os
import tempfile
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from airflow.sdk import DAG, task

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supported file extensions (aligned with LoaderFactory)
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

# ---------------------------------------------------------------------------
# Folder-to-area mapping for the bank's document structure
# ---------------------------------------------------------------------------
FOLDER_AREA_MAPPING = {
    "RRHH": "rrhh",
    "002 _ Cuentas": "operaciones",
    "004 _ Prestamos": "operaciones",
    "005 _ Tarjeta de débito": "operaciones",
    "005 _ Tarjeta de debito": "operaciones",  # ASCII fallback
    "007 _ Canales automaticos y claves": "tecnologia",
    "007 _ Canales automáticos y claves": "tecnologia",  # accent variant
    "008 _ Cobros y pagos": "operaciones",
    "010 _ Paquetes": "operaciones",
    "011 _ Tarjeta de crédito": "operaciones",
    "011 _ Tarjeta de credito": "operaciones",  # ASCII fallback
    "CAT": "operaciones",
}

# Prefixes to skip entirely
SKIP_PREFIXES = {"muestras-banco/", "muestras-banco\\"}

# ---------------------------------------------------------------------------
# Filename-to-area mapping for flat local directories (tests/data/demo)
# Keys are filename prefixes; values are area_funcional enum values.
# ---------------------------------------------------------------------------
FILENAME_AREA_MAPPING: dict[str, str] = {
    "RRHH": "rrhh",
    "PAQ": "operaciones",
    "PP": "operaciones",
    "CS": "operaciones",
    "005 _ Tarjeta": "operaciones",
}

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
# Helpers: sync DB access via psycopg (same pattern as rag_indexing DAG)
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


def _compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    return sha256.hexdigest()


def _check_hash_exists(file_hash: str) -> bool:
    """Check if a document with this hash already exists in the DB."""
    with _get_sync_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM documents WHERE file_hash = %s AND is_active = true",
            (file_hash,),
        )
        row = cur.fetchone()
        return row[0] > 0 if row else False


def _determine_area(blob_name: str) -> str:
    """Determine the area_funcional based on the GCS blob path (folder name).

    Examines the first path component (top-level folder) and maps it to
    the area_funcional enum using FOLDER_AREA_MAPPING.
    """
    # blob_name examples:
    #   "RRHH/001 RRHH - Administracion.pdf"
    #   "002 _ Cuentas/subcarpeta/archivo.pdf"
    #   "CAT/Canales/doc.docx"
    parts = blob_name.split("/")
    if len(parts) < 2:
        return "general"

    top_folder = parts[0]

    # Direct match
    if top_folder in FOLDER_AREA_MAPPING:
        return FOLDER_AREA_MAPPING[top_folder]

    # Fuzzy match: try stripping accents or matching prefix
    for folder_key, area in FOLDER_AREA_MAPPING.items():
        if top_folder.startswith(folder_key) or folder_key.startswith(top_folder):
            return area

    logger.warning("unmapped_folder folder=%s blob=%s defaulting=general", top_folder, blob_name)
    return "general"


def _determine_area_from_filename(filename: str) -> str:
    """Determine area from filename for flat (non-folder) local directories.

    Used when documents are in a flat directory without GCS folder structure.
    Matches filename prefixes against FILENAME_AREA_MAPPING.
    """
    for prefix, area in FILENAME_AREA_MAPPING.items():
        if filename.startswith(prefix):
            return area
    logger.warning("unmapped_filename filename=%s defaulting=general", filename)
    return "general"


def _register_or_update_document_local(
    filename: str,
    container_path: str,
    file_size: int,
    file_hash: str,
    area: str,
) -> int:
    """Register or update a local document in the documents table.

    If a record with the same file_path already exists (e.g. from seed_data),
    updates its file_hash and returns the existing ID (preserving ACLs).
    Otherwise creates a new record.
    Returns document_id.
    """
    file_ext = Path(filename).suffix.lstrip(".")

    with _get_sync_connection() as conn:
        with conn.cursor() as cur:
            # Check if record exists by file_path (seeded records have file_path set)
            cur.execute(
                "SELECT id FROM documents WHERE file_path = %s AND is_active = true LIMIT 1",
                (container_path,),
            )
            row = cur.fetchone()

            if row:
                doc_id = row[0]
                cur.execute(
                    "UPDATE documents SET file_hash = %s, file_size = %s WHERE id = %s",
                    (file_hash, file_size, doc_id),
                )
                logger.info("document_updated id=%s filename=%s", doc_id, filename)
            else:
                doc_id = abs(hash(f"{filename}_{file_hash[:16]}_{uuid.uuid4().hex[:8]}")) % (2**31)
                cur.execute(
                    """
                    INSERT INTO documents
                        (id, filename, file_path, file_type, file_size, file_hash, area, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    RETURNING id
                    """,
                    (
                        doc_id,
                        filename,
                        container_path,
                        file_ext,
                        file_size,
                        file_hash,
                        area,
                        json.dumps({"source": "local_batch_load", "local_path": container_path}),
                    ),
                )
                result = cur.fetchone()
                doc_id = result[0] if result else doc_id
                logger.info("document_registered id=%s filename=%s area=%s", doc_id, filename, area)
        conn.commit()
    return doc_id


def _register_document(
    filename: str,
    gcs_uri: str,
    file_size: int,
    file_hash: str,
    area: str,
) -> int:
    """Register a new document in the documents table. Returns document_id."""
    doc_id = abs(hash(f"{filename}_{file_hash[:16]}_{uuid.uuid4().hex[:8]}")) % (2**31)
    file_ext = Path(filename).suffix.lstrip(".")

    with _get_sync_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (id, filename, file_path, file_type, file_size, file_hash, area, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                RETURNING id
                """,
                (
                    doc_id,
                    filename,
                    gcs_uri,  # Store the GCS URI as file_path
                    file_ext,
                    file_size,
                    file_hash,
                    area,
                    json.dumps({"source": "gcs_batch_load", "gcs_uri": gcs_uri}),
                ),
            )
            result = cur.fetchone()
            if result is None:
                # Collision on id, generate a new one
                doc_id = abs(hash(f"{uuid.uuid4().hex}")) % (2**31)
                cur.execute(
                    """
                    INSERT INTO documents (id, filename, file_path, file_type, file_size, file_hash, area, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        doc_id,
                        filename,
                        gcs_uri,
                        file_ext,
                        file_size,
                        file_hash,
                        area,
                        json.dumps({"source": "gcs_batch_load", "gcs_uri": gcs_uri}),
                    ),
                )
                result = cur.fetchone()
                doc_id = result[0]
            else:
                doc_id = result[0]
        conn.commit()

    logger.info("document_registered id=%s filename=%s area=%s", doc_id, filename, area)
    return doc_id


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
    return run_id


def _update_pipeline_run(
    run_id: str,
    status: str,
    *,
    set_started: bool = False,
    set_finished: bool = False,
    error_message: str | None = None,
) -> None:
    """Update a pipeline_runs row."""
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


def _download_from_gcs(gcs_uri: str, dest_dir: str) -> Path:
    """Download a file from GCS to a local directory.

    Args:
        gcs_uri: URI like gs://bucket/path/to/file.pdf
        dest_dir: Local directory for download.

    Returns:
        Path to the downloaded local file.
    """
    from google.cloud import storage

    without_scheme = gcs_uri[5:]
    bucket_name, _, blob_path = without_scheme.partition("/")
    filename = blob_path.rsplit("/", 1)[-1]
    local_path = Path(dest_dir) / filename

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.download_to_filename(str(local_path))

    return local_path


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="load_demo_data",
    description="Carga masiva: indexa documentos PDF/DOCX desde un bucket GCS",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["indexing", "rag", "demo", "batch"],
    params={
        "gcs_bucket": "macro-ai-dev-backend-samples",
        "folder_path": None,  # if set, uses local filesystem mode instead of GCS
        "skip_existing": True,
    },
) as dag:

    @task()
    def discover_documents(**context) -> dict:
        """List all PDF/DOCX files from a local folder or GCS bucket.

        If folder_path is provided in conf, scans the local filesystem at
        /opt/airflow/<folder_path>. Otherwise uses google.cloud.storage to
        list blobs from the configured GCS bucket. Maps paths to area_funcional.
        Optionally skips documents already indexed (by file_hash).
        """
        conf = context["dag_run"].conf or {}
        folder_path = conf.get("folder_path")
        gcs_bucket = conf.get("gcs_bucket", "macro-ai-dev-backend-samples")
        skip_existing = conf.get("skip_existing", True)

        # ── Local mode ──────────────────────────────────────────────────────
        if folder_path:
            # Support both absolute paths and paths relative to /opt/airflow
            fp = folder_path.strip("/")
            local_dir = Path(f"/opt/airflow/{fp}") if not folder_path.startswith("/") else Path(folder_path)

            if not local_dir.exists():
                raise FileNotFoundError(f"Local folder not found: {local_dir}")

            logger.info("discover_local folder=%s skip_existing=%s", local_dir, skip_existing)

            documents_to_index = []
            skipped = []
            skipped_unsupported = 0

            for file_path in sorted(local_dir.iterdir()):
                if not file_path.is_file():
                    continue
                if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    skipped_unsupported += 1
                    continue

                filename = file_path.name
                file_hash = _compute_file_hash(file_path)
                file_size = file_path.stat().st_size
                area = _determine_area_from_filename(filename)
                container_path = str(file_path)

                if skip_existing and _check_hash_exists(file_hash):
                    logger.info("skip_existing file=%s hash=%s", filename, file_hash[:16])
                    skipped.append(filename)
                    continue

                documents_to_index.append(
                    {
                        "local_path": container_path,
                        "filename": filename,
                        "file_hash": file_hash,
                        "file_size": file_size,
                        "area": area,
                    }
                )

            logger.info(
                "discover_done to_index=%d skipped_existing=%d skipped_unsupported=%d",
                len(documents_to_index),
                len(skipped),
                skipped_unsupported,
            )

            return {
                "mode": "local",
                "folder_path": str(local_dir),
                "documents": documents_to_index,
                "skipped": skipped,
                "skipped_unsupported": skipped_unsupported,
                "total_found": len(documents_to_index) + len(skipped),
            }

        # ── GCS mode (existing logic, unchanged) ────────────────────────────
        from google.cloud import storage

        logger.info(
            "discover_documents bucket=%s skip_existing=%s",
            gcs_bucket,
            skip_existing,
        )

        client = storage.Client()
        bucket = client.bucket(gcs_bucket)

        documents_to_index = []
        skipped = []
        skipped_unsupported = 0

        # Create a temp dir for hash computation (download each file briefly)
        with tempfile.TemporaryDirectory(prefix="airflow_discover_") as tmpdir:
            for blob in bucket.list_blobs():
                # Skip directory markers
                if blob.name.endswith("/"):
                    continue

                # Skip muestras-banco/ (duplicate of root folders)
                if any(blob.name.startswith(prefix) for prefix in SKIP_PREFIXES):
                    continue

                # Check extension
                ext = Path(blob.name).suffix.lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    skipped_unsupported += 1
                    continue

                filename = blob.name.rsplit("/", 1)[-1]
                gcs_uri = f"gs://{gcs_bucket}/{blob.name}"
                area = _determine_area(blob.name)

                # Download to compute hash
                local_path = Path(tmpdir) / f"{uuid.uuid4().hex}_{filename}"
                blob.download_to_filename(str(local_path))
                file_hash = _compute_file_hash(local_path)
                file_size = local_path.stat().st_size

                # Clean up the temp file to save disk space
                local_path.unlink()

                if skip_existing and _check_hash_exists(file_hash):
                    logger.info("skip_existing file=%s hash=%s", filename, file_hash[:16])
                    skipped.append(filename)
                    continue

                documents_to_index.append(
                    {
                        "gcs_uri": gcs_uri,
                        "blob_name": blob.name,
                        "filename": filename,
                        "file_hash": file_hash,
                        "file_size": file_size,
                        "area": area,
                    }
                )

        logger.info(
            "discover_done to_index=%d skipped_existing=%d skipped_unsupported=%d",
            len(documents_to_index),
            len(skipped),
            skipped_unsupported,
        )

        return {
            "mode": "gcs",
            "gcs_bucket": gcs_bucket,
            "documents": documents_to_index,
            "skipped": skipped,
            "skipped_unsupported": skipped_unsupported,
            "total_found": len(documents_to_index) + len(skipped),
        }

    @task()
    def index_documents(discovery_result: dict, **context) -> dict:
        """Index all discovered documents sequentially.

        For each document: acquire local path (download from GCS or use directly) ->
        register in DB -> validate -> load & chunk -> generate embeddings ->
        store in pgvector -> update status.

        Supports both local mode (local_path key in doc_info) and GCS mode
        (gcs_uri key). Uses the same infrastructure components as rag_indexing DAG.
        """
        documents = discovery_result["documents"]
        dag_run_id = context["dag_run"].run_id
        batch_start = time.time()

        if not documents:
            logger.info("no_documents_to_index")
            return {
                "indexed": [],
                "failed": [],
                "metrics": {
                    "total_chunks": 0,
                    "total_tokens": 0,
                    "duration_seconds": 0,
                    "chunk_sizes": [],
                },
            }

        # Import infrastructure components (deferred to avoid import errors at DAG parse time)
        from src.infrastructure.rag.chunking.adaptive_chunker import AdaptiveChunker
        from src.infrastructure.rag.embeddings.gemini_embeddings import GeminiEmbeddingService
        from src.infrastructure.rag.loaders.factory import LoaderFactory
        from src.infrastructure.rag.loaders.validator import FileValidator

        loader_factory = LoaderFactory()
        validator = FileValidator()
        chunker = AdaptiveChunker()
        embedding_service = GeminiEmbeddingService()

        indexed_results = []
        failed_results = []
        all_chunk_sizes = []
        total_chunks = 0
        total_tokens = 0

        # Create a temp directory for GCS downloads (not used in local mode)
        with tempfile.TemporaryDirectory(prefix="airflow_index_") as tmpdir:
            for doc_idx, doc_info in enumerate(documents, 1):
                filename = doc_info["filename"]
                file_hash = doc_info["file_hash"]
                area = doc_info["area"]
                is_local = "local_path" in doc_info
                doc_start = time.time()
                pipeline_run_id: str | None = None

                logger.info(
                    "processing_document %d/%d file=%s area=%s mode=%s",
                    doc_idx,
                    len(documents),
                    filename,
                    area,
                    "local" if is_local else "gcs",
                )

                try:
                    # 0. Acquire local path (local mode: use directly; GCS mode: download)
                    if is_local:
                        local_path = Path(doc_info["local_path"])
                        logger.info("local_file file=%s size=%d", filename, local_path.stat().st_size)
                        document_id = _register_or_update_document_local(
                            filename=filename,
                            container_path=doc_info["local_path"],
                            file_size=doc_info["file_size"],
                            file_hash=file_hash,
                            area=area,
                        )
                    else:
                        gcs_uri = doc_info["gcs_uri"]
                        local_path = _download_from_gcs(gcs_uri, tmpdir)
                        logger.info("downloaded file=%s size=%d", filename, local_path.stat().st_size)
                        document_id = _register_document(
                            filename=filename,
                            gcs_uri=gcs_uri,
                            file_size=local_path.stat().st_size,
                            file_hash=file_hash,
                            area=area,
                        )

                    # 1. Register document in DB
                    pipeline_run_id = _create_pipeline_run(document_id, dag_run_id)
                    _update_pipeline_run(pipeline_run_id, "running", set_started=True)

                    # 2. Validate
                    mime_type = validator.validate(local_path)
                    logger.info(
                        "validated doc_id=%s file=%s mime=%s",
                        document_id,
                        filename,
                        mime_type,
                    )

                    # 3. Load and chunk
                    loaded_doc = loader_factory.load(local_path)
                    chunks = chunker.chunk(loaded_doc)
                    logger.info(
                        "chunked doc_id=%s chunks=%d tokens=%d",
                        document_id,
                        len(chunks),
                        sum(c.token_count for c in chunks),
                    )

                    # 4. Generate embeddings
                    texts = [c.text for c in chunks]
                    embeddings = asyncio.run(embedding_service.embed_documents(texts))
                    logger.info(
                        "embedded doc_id=%s embeddings=%d",
                        document_id,
                        len(embeddings),
                    )

                    # 5. Store in pgvector
                    areas_distribution: dict[str, int] = {}
                    chunk_ids = []

                    with _get_sync_connection() as conn:
                        with conn.cursor() as cur:
                            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
                                # Use the area determined from folder mapping, not chunk metadata
                                chunk_area = area
                                embedding_str = "[" + ",".join(map(str, embedding)) + "]"

                                cur.execute(
                                    """
                                    INSERT INTO document_chunks
                                        (document_id, chunk_index, content, embedding, area,
                                         token_count, metadata)
                                    VALUES
                                        (%s, %s, %s, CAST(%s AS halfvec), %s, %s, %s)
                                    RETURNING id
                                    """,
                                    (
                                        document_id,
                                        idx,
                                        chunk.text,
                                        embedding_str,
                                        chunk_area,
                                        chunk.token_count,
                                        json.dumps(chunk.metadata or {}),
                                    ),
                                )
                                row = cur.fetchone()
                                chunk_ids.append(str(row[0]))
                                areas_distribution[chunk_area] = areas_distribution.get(chunk_area, 0) + 1
                                all_chunk_sizes.append(chunk.token_count)

                            # Update document metadata
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
                                "total_tokens": sum(c.token_count for c in chunks),
                                "areas": areas_distribution,
                            }

                            cur.execute(
                                "UPDATE documents SET file_hash = %s, metadata = %s WHERE id = %s",
                                (file_hash, json.dumps(current_meta), document_id),
                            )
                        conn.commit()

                    # 6. Update pipeline run
                    doc_duration = time.time() - doc_start
                    _update_pipeline_run(pipeline_run_id, "completed", set_finished=True)

                    doc_chunks = len(chunks)
                    doc_tokens = sum(c.token_count for c in chunks)
                    total_chunks += doc_chunks
                    total_tokens += doc_tokens

                    source_ref = doc_info.get("local_path") or doc_info.get("gcs_uri", "")
                    indexed_results.append(
                        {
                            "document_id": document_id,
                            "filename": filename,
                            "source": source_ref,
                            "area": area,
                            "chunk_count": doc_chunks,
                            "total_tokens": doc_tokens,
                            "areas": areas_distribution,
                            "duration_seconds": round(doc_duration, 2),
                        }
                    )

                    logger.info(
                        "indexed_ok doc_id=%s file=%s chunks=%d tokens=%d duration=%.1fs",
                        document_id,
                        filename,
                        doc_chunks,
                        doc_tokens,
                        doc_duration,
                    )

                    # Clean up downloaded GCS file to save disk space (skip for local files)
                    if not is_local:
                        with contextlib.suppress(OSError):
                            local_path.unlink()

                except Exception as exc:
                    doc_duration = time.time() - doc_start
                    logger.exception(
                        "indexing_failed file=%s error=%s",
                        filename,
                        str(exc),
                    )
                    source_ref = doc_info.get("local_path") or doc_info.get("gcs_uri", "")
                    failed_results.append(
                        {
                            "filename": filename,
                            "source": source_ref,
                            "error": str(exc),
                            "duration_seconds": round(doc_duration, 2),
                        }
                    )

                    # Try to update pipeline run if it was created
                    try:
                        if pipeline_run_id is not None:
                            _update_pipeline_run(
                                pipeline_run_id,
                                "failed",
                                set_finished=True,
                                error_message=str(exc),
                            )
                    except Exception:
                        logger.exception("failed_to_update_pipeline_run")

        batch_duration = time.time() - batch_start

        # Compute chunk size distribution
        chunk_size_stats = {}
        if all_chunk_sizes:
            all_chunk_sizes.sort()
            chunk_size_stats = {
                "min": min(all_chunk_sizes),
                "max": max(all_chunk_sizes),
                "avg": round(sum(all_chunk_sizes) / len(all_chunk_sizes), 1),
                "median": all_chunk_sizes[len(all_chunk_sizes) // 2],
                "p95": all_chunk_sizes[int(len(all_chunk_sizes) * 0.95)]
                if len(all_chunk_sizes) > 1
                else all_chunk_sizes[0],
            }

        return {
            "indexed": indexed_results,
            "failed": failed_results,
            "metrics": {
                "total_documents_indexed": len(indexed_results),
                "total_documents_failed": len(failed_results),
                "total_chunks": total_chunks,
                "total_tokens": total_tokens,
                "chunk_size_distribution": chunk_size_stats,
                "duration_seconds": round(batch_duration, 2),
            },
        }

    @task()
    def report_results(index_result: dict) -> dict:
        """Generate and log a summary report of the batch indexing operation."""
        metrics = index_result["metrics"]
        indexed = index_result["indexed"]
        failed = index_result["failed"]

        # Build summary
        summary_lines = [
            "=" * 60,
            "BATCH INDEXING REPORT - load_demo_data",
            "=" * 60,
            f"Documents indexed:  {metrics.get('total_documents_indexed', 0)}",
            f"Documents failed:   {metrics.get('total_documents_failed', 0)}",
            f"Total chunks:       {metrics.get('total_chunks', 0)}",
            f"Total tokens:       {metrics.get('total_tokens', 0)}",
            f"Duration:           {metrics.get('duration_seconds', 0):.1f}s",
        ]

        chunk_dist = metrics.get("chunk_size_distribution", {})
        if chunk_dist:
            summary_lines.extend(
                [
                    "",
                    "Chunk size distribution (tokens):",
                    f"  Min:    {chunk_dist.get('min', 'N/A')}",
                    f"  Max:    {chunk_dist.get('max', 'N/A')}",
                    f"  Avg:    {chunk_dist.get('avg', 'N/A')}",
                    f"  Median: {chunk_dist.get('median', 'N/A')}",
                    f"  P95:    {chunk_dist.get('p95', 'N/A')}",
                ]
            )

        # Area distribution summary
        area_totals: dict[str, int] = {}
        if indexed:
            for doc in indexed:
                area = doc.get("area", "general")
                area_totals[area] = area_totals.get(area, 0) + 1

            summary_lines.extend(["", "Documents per area:"])
            for area, count in sorted(area_totals.items()):
                summary_lines.append(f"  {area}: {count}")

        if indexed:
            summary_lines.extend(["", "Indexed documents:"])
            for doc in indexed:
                summary_lines.append(
                    f"  [{doc['area']}] {doc['filename']}: {doc['chunk_count']} chunks, "
                    f"{doc['total_tokens']} tokens, {doc['duration_seconds']}s"
                )

        if failed:
            summary_lines.extend(["", "Failed documents:"])
            for doc in failed:
                summary_lines.append(f"  {doc['filename']}: {doc['error']}")

        summary_lines.append("=" * 60)
        summary = "\n".join(summary_lines)

        logger.info("batch_indexing_report\n%s", summary)
        print(summary)

        return {
            "status": "completed" if not failed else "completed_with_errors",
            "metrics": metrics,
            "indexed_count": len(indexed),
            "failed_count": len(failed),
            "area_distribution": area_totals,
        }

    # Task dependencies: discover -> index -> report
    discovered = discover_documents()
    indexed = index_documents(discovered)
    report_results(indexed)
