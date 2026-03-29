"""Document upload and management routes."""

from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.document_service import DocumentService
from src.application.services.document_upload_service import DocumentUploadService
from src.infrastructure.api.dependencies import get_current_user, get_db
from src.infrastructure.api.schemas.documents import (
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentStatus,
    DocumentUploadResponse,
    PaginationLinks,
)
from src.infrastructure.database.models.user import User
from src.infrastructure.database.repositories.document_repository import DocumentRepository
from src.infrastructure.rag.loaders.validator import FileSizeError, FileValidationError
from src.shared.exceptions import NotFoundError, ValidationError

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


def get_document_upload_service() -> DocumentUploadService:
    """Dependency provider for DocumentUploadService."""
    return DocumentUploadService()


def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    """Dependency provider for DocumentService."""
    repository = DocumentRepository(session=db)
    return DocumentService(document_repository=repository)


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="Lista documentos con paginacion y filtros",
    description="""
Lista documentos accesibles al usuario actual con paginación y filtros opcionales.

**Autorización:**
- Usuarios regulares solo ven sus propios documentos
- Administradores ven todos los documentos

**Filtros disponibles:**
- `status`: pending, indexing, indexed, failed
- `file_type`: MIME type (application/pdf, etc.)
- `date_from` / `date_to`: Rango de fechas de creación
""",
)
async def list_documents(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="Número máximo de documentos a retornar"),
    offset: int = Query(0, ge=0, description="Número de documentos a saltar"),
    status: DocumentStatus | None = Query(None, description="Filtrar por estado"),
    file_type: str | None = Query(None, description="Filtrar por MIME type"),
    date_from: datetime | None = Query(None, description="Fecha desde (ISO 8601)"),
    date_to: datetime | None = Query(None, description="Fecha hasta (ISO 8601)"),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    """List documents with pagination and filters."""
    result = await document_service.list_documents(
        user=current_user,
        status=status.value if status else None,
        file_type=file_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )

    # Build pagination links
    base_url = str(request.url).split("?")[0]
    query_params = dict(request.query_params)
    query_params.pop("offset", None)

    next_link = None
    prev_link = None

    if offset + limit < result.total_count:
        next_offset = offset + limit
        next_params = {**query_params, "offset": str(next_offset)}
        next_link = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in next_params.items())}"

    if offset > 0:
        prev_offset = max(0, offset - limit)
        prev_params = {**query_params, "offset": str(prev_offset)}
        prev_link = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in prev_params.items())}"

    items = [
        DocumentListItem(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            status=doc.status,
            area=str(doc.area.value) if doc.area else "general",
            uploaded_by=doc.uploaded_by,
            created_at=doc.created_at,
        )
        for doc in result.items
    ]

    return DocumentListResponse(
        items=items,
        total_count=result.total_count,
        limit=limit,
        offset=offset,
        links=PaginationLinks(next=next_link, prev=prev_link),
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Obtiene detalle de un documento",
    description="""
Obtiene información detallada de un documento incluyendo:
- Metadata completa (filename, size, hash, etc.)
- Estado del pipeline de indexación
- Número de chunks generados
- Información de clasificación y área funcional

**Autorización:**
- Usuarios regulares solo pueden ver sus propios documentos
- Administradores pueden ver cualquier documento
""",
)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentDetailResponse:
    """Get document details."""
    detail = await document_service.get_document(document_id, current_user)

    return DocumentDetailResponse(
        id=detail.id,
        filename=detail.filename,
        file_path=detail.file_path,
        file_type=detail.file_type,
        file_size=detail.file_size,
        file_hash=detail.file_hash,
        version=detail.version,
        status=detail.status,
        area=detail.area,
        classification_level=detail.classification_level,
        uploaded_by=detail.uploaded_by,
        chunk_count=detail.chunk_count,
        metadata=detail.metadata,
        created_at=detail.created_at,
        updated_at=detail.updated_at,
    )


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Elimina un documento (soft delete)",
    description="""
Marca un documento como eliminado (soft delete).

El documento se marca inmediatamente como inactivo, pero la limpieza de:
- Chunks en base de datos
- Embeddings vectoriales
- Archivo en GCS

se realiza de forma asíncrona para no bloquear el request.

**Autorización:**
- Usuarios regulares solo pueden eliminar sus propios documentos
- Administradores pueden eliminar cualquier documento
""",
)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
    db: AsyncSession = Depends(get_db),
) -> DocumentDeleteResponse:
    """Soft delete a document."""
    await document_service.delete_document(document_id, current_user)
    await db.commit()

    logger.info(
        "document_deleted",
        document_id=document_id,
        user_id=current_user.id,
        is_admin=current_user.is_superuser,
    )

    return DocumentDeleteResponse(
        id=document_id,
        deleted=True,
        message="Document marked for deletion. Cleanup will proceed asynchronously.",
    )


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sube un documento para ser procesado",
    description="""
Este endpoint permite subir un documento para su posterior procesamiento e indexación.

**Proceso de Validación:**
Al recibir un archivo, se delega al `DocumentUploadService` y al `FileValidator`,
quienes realizan las siguientes verificaciones críticas de seguridad e integridad
antes de aceptarlo:
1. **Tamaño del Archivo:** Se verifica que el archivo no supere el tamaño máximo
   permitido configurado (actualmente 50MB) y que no sea un archivo vacío.
2. **Prevención de Código Malicioso:** Se realiza un escaneo de los "magic bytes"
   (firma binaria inicial) del contenido para asegurar que no coincide con firmas
   peligrosas conocidas (ej. ejecutables de Windows `MZ`, binarios de Linux `ELF`,
   scripts de Shell `#!/`, scripts de PHP `<?php`, o etiquetas HTML/JS `<script`).
3. **Validación de Magic Bytes (Tipos Binarios):** Para formatos como PDF y DOCX,
   no solo se confía en la extensión, sino que se valida criptográficamente que los
   primeros bytes del archivo correspondan efectivamente al formato declarado.
4. **Verificación Estructural profunda:** En el caso de archivos ZIP-based como
   `.docx`, el sistema abre temporalmente el archivo comprimido y verifica la
   existencia de archivos estructurales obligatorios (ej. `word/document.xml`) para
   asegurar que no es simplemente un ZIP renombrado.
5. **Comprobación de Extensión vs. Tipo Real:** Se asegura que la extensión
   proporcionada en el nombre del archivo coincide de forma unívoca con el verdadero
   tipo MIME detectado a través del análisis de los magic bytes o contenido.

**Formatos Soportados:** PDF, DOCX, TXT, CSV.
""",
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    upload_service: DocumentUploadService = Depends(get_document_upload_service),
) -> DocumentUploadResponse:
    """Handle document upload."""
    if not file.filename:
        raise ValidationError(message="Filename is required.")

    # Read the file content
    try:
        content = await file.read()
    except Exception as e:
        logger.error("file_read_error", error=str(e))
        raise ValidationError(message="Could not read file content.") from e

    try:
        result = await upload_service.process_upload(
            file_content=content,
            filename=file.filename,
        )
        return DocumentUploadResponse(**result)

    except FileSizeError as e:
        logger.warning("file_size_exceeded", error=str(e), filename=file.filename)
        raise ValidationError(message=str(e)) from e

    except FileValidationError as e:
        logger.warning("file_validation_failed", error=str(e), filename=file.filename)
        raise ValidationError(message=str(e)) from e

    except NotFoundError:
        raise

    except Exception as e:
        logger.error("unexpected_upload_error", error=str(e), filename=file.filename)
        raise
