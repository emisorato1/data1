"""Cliente para Google Cloud Storage."""

import logging

from google.cloud import storage  # type: ignore[attr-defined]

from src.config.settings import settings

logger = logging.getLogger(__name__)


class GCSClient:
    """Cliente para interactuar con Google Cloud Storage."""

    def __init__(self, bucket_name: str | None = None):
        """Inicializa el cliente de GCS."""
        self.bucket_name = bucket_name or settings.gcs_bucket_name
        self.project_id = settings.gcp_project_id
        self._kms_key_name = settings.gcs_kms_key_name or None

        # La inicializacion real depende de las credenciales en el entorno
        # (ej. GOOGLE_APPLICATION_CREDENTIALS) o configuracion de workload identity
        try:
            if settings.use_vertex_ai:
                import google.auth

                effective_quota = settings.gcp_quota_project_id or settings.gcp_project_id
                credentials, _ = google.auth.default(quota_project_id=effective_quota)
                self._client = storage.Client(project=self.project_id, credentials=credentials)
            else:
                self._client = storage.Client(project=self.project_id)
            self._bucket = self._client.bucket(self.bucket_name)
        except Exception as e:
            logger.warning("No se pudo inicializar GCS Client (podría fallar si no hay credenciales): %s", e)
            self._client = None
            self._bucket = None

    async def upload_file(self, file_content: bytes, destination_blob_name: str, content_type: str) -> str:
        """Sube un archivo al bucket de GCS y retorna su URI.

        Args:
            file_content: Contenido del archivo en bytes.
            destination_blob_name: Ruta destino en el bucket.
            content_type: MIME type del archivo.

        Returns:
            URI del archivo subido (ej. gs://bucket_name/destination_blob_name)
        """
        if not self._bucket:
            raise RuntimeError("El cliente de GCS no está inicializado correctamente.")

        logger.info(f"Subiendo archivo a gs://{self.bucket_name}/{destination_blob_name}")
        blob = self._bucket.blob(destination_blob_name, kms_key_name=self._kms_key_name)

        # Sube el contenido desde el string de bytes
        blob.upload_from_string(file_content, content_type=content_type)

        return f"gs://{self.bucket_name}/{destination_blob_name}"

    async def delete_file(self, blob_name: str) -> None:
        """Elimina un archivo del bucket de GCS.

        Args:
            blob_name: Ruta del archivo a eliminar en el bucket.
        """
        if not self._bucket:
            raise RuntimeError("El cliente de GCS no está inicializado correctamente.")

        blob = self._bucket.blob(blob_name)
        if blob.exists():
            logger.info(f"Eliminando archivo gs://{self.bucket_name}/{blob_name}")
            blob.delete()
        else:
            logger.warning(f"El archivo gs://{self.bucket_name}/{blob_name} no existe para eliminación.")
