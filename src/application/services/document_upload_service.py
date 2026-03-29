"""Service for handling document uploads and validations."""

import hashlib
import tempfile
import uuid
from pathlib import Path
from typing import Any

import structlog

from src.config.settings import settings as app_settings
from src.infrastructure.rag.loaders.validator import FileSizeError, FileValidationError, FileValidator

logger = structlog.get_logger(__name__)


class DocumentUploadService:
    """Service to handle document uploads, validation, and metadata extraction."""

    def __init__(self, validator: FileValidator | None = None) -> None:
        self.validator = validator or FileValidator(max_file_size=app_settings.max_request_size_bytes)

    async def process_upload(
        self,
        file_content: bytes,
        filename: str,
    ) -> dict[str, Any]:
        """
        Process the uploaded file: write to temp file, validate, calculate hash.

        Returns:
            dict with document_id, filename, mime_type, size_bytes, file_hash, status.

        Raises:
            FileValidationError if validation fails.
            ValueError if content is empty or exceeds limit before validation.
        """
        size_bytes = len(file_content)

        # Early check for size limit (50MB) to prevent writing huge files to disk unnecessarily
        # though the FileValidator also checks this.
        if size_bytes > self.validator.max_file_size:
            raise FileSizeError(
                f"Archivo excede el tamaño máximo ({size_bytes} > {self.validator.max_file_size} bytes)"
            )

        if size_bytes == 0:
            raise FileValidationError("Archivo vacío")

        # Calculate SHA-256 hash
        file_hash = hashlib.sha256(file_content).hexdigest()

        # Create a temporary file to run the FileValidator against
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(file_content)
            temp_file.flush()

        try:
            # Validate file and get real MIME type
            mime_type = self.validator.validate(temp_path)

            # Generate a mock document_id (since actual persistence is T2-S5-02)
            document_id = str(uuid.uuid4())

            logger.info(
                "document_uploaded",
                filename=filename,
                size_bytes=size_bytes,
                mime_type=mime_type,
                file_hash=file_hash,
            )

            return {
                "document_id": document_id,
                "filename": filename,
                "mime_type": mime_type,
                "size_bytes": size_bytes,
                "file_hash": file_hash,
                "status": "pending",
            }
        finally:
            # Cleanup temp file
            if temp_path.exists():
                temp_path.unlink()
