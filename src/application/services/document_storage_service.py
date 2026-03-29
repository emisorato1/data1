"""Servicio de almacenamiento de documentos con transacciones y compensaciones."""

import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.infrastructure.database.models.document import AreaFuncional, Document, DocumentStatus
from src.infrastructure.storage.gcs_client import GCSClient

logger = logging.getLogger(__name__)


class DocumentStorageService:
    """Orquesta el almacenamiento en GCS y el registro en base de datos."""

    def __init__(self, db_session: AsyncSession, gcs_client: GCSClient | None = None):
        """Inicializa el servicio."""
        self.db = db_session
        self.gcs_client = gcs_client or GCSClient()

    async def store_document(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str,
        file_hash: str,
        user_id: int,
        document_id: int,  # Viene de OpenText/ID externo, dado que doc="ID de OpenText (DTREE.DataID)"
        area: str = "general",
        classification: str = "internal",
        file_size: int = 0,
    ) -> Document:
        """Almacena el documento en GCS y lo registra en la base de datos de manera atómica.

        Sigue el flujo compensatorio:
        1. Genera el path en GCS
        2. Intenta subir el archivo
        3. Si sube, inserta en BD
        4. Si BD falla, compensa eliminando de GCS.
        (Alternativa Spec: "Si falla DB insert, se elimina archivo de GCS").

        Args:
            file_content: Contenido del archivo
            filename: Nombre original
            mime_type: Tipo MIME
            file_hash: Hash SHA256 para deduplicacion (opcional/referencia)
            user_id: ID del usuario que sube
            document_id: ID proporcionado externamente o autogenerado (en este modelo es DataID)
            area: Area funcional
            classification: Nivel de clasificacion
            file_size: Tamano del archivo

        Returns:
            Modelo Document persistido con estado pending y su storage_uri.
        """
        now = datetime.datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        tenant_id = settings.tenant_id

        # Path estructura: {tenant_id}/{year}/{month}/{document_id}/{filename}
        blob_path = f"{tenant_id}/{year}/{month}/{document_id}/{filename}"

        # 1. Intentamos subir el archivo a GCS
        try:
            storage_uri = await self.gcs_client.upload_file(
                file_content=file_content, destination_blob_name=blob_path, content_type=mime_type
            )
        except Exception as e:
            logger.error("Fallo la subida a GCS. Abortando registro en BD. Error: %s", e)
            raise ValueError(f"Fallo al subir a GCS: {e}") from e

        # 2. Insertamos en base de datos
        try:
            # En SQLAlchemy 2, insertamos y hacemos flush/commit
            area_enum = AreaFuncional(area) if area in [e.value for e in AreaFuncional] else AreaFuncional.general

            new_doc = Document(
                id=document_id,
                filename=filename,
                file_path=storage_uri,  # Usamos file_path para la URI de storage
                file_type=mime_type,
                file_size=file_size,
                file_hash=file_hash,
                status=DocumentStatus.pending,
                area=area_enum,
                classification_level=classification,
                uploaded_by=user_id,
                is_active=True,
            )
            self.db.add(new_doc)

            # Intentamos persistir. Si esto falla, saltará la excepción
            await self.db.commit()
            await self.db.refresh(new_doc)
            return new_doc

        except Exception as db_err:
            # 3. COMPENSACIÓN: Si falla la BD, borramos el archivo de GCS
            logger.error("Fallo el registro en BD. Compensando: eliminando de GCS %s", blob_path)
            await self.db.rollback()
            try:
                await self.gcs_client.delete_file(blob_path)
            except Exception as gcs_err:
                logger.critical(
                    "Fallo crítico en compensación: No se pudo eliminar %s de GCS."
                    " Requiere intervención manual. Error: %s",
                    blob_path,
                    gcs_err,
                )

            raise ValueError(f"Fallo al registrar en BD: {db_err}") from db_err
