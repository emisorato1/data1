"""Factory for selecting the appropriate document loader based on MIME type."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.infrastructure.rag.loaders.docx_loader import DOCXLoader
from src.infrastructure.rag.loaders.pdf_loader import PDFLoader
from src.infrastructure.rag.loaders.validator import FileValidator

if TYPE_CHECKING:
    from pathlib import Path

    from src.infrastructure.rag.loaders.base import DocumentLoader
    from src.infrastructure.rag.loaders.models import LoadedDocument

logger = logging.getLogger(__name__)

# Map MIME types to their loader classes
_MIME_TO_LOADER: dict[str, type[DocumentLoader]] = {
    "application/pdf": PDFLoader,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DOCXLoader,
}


class LoaderFactory:
    """Selects PDFLoader or DOCXLoader based on the file's MIME type.

    Uses ``FileValidator`` to detect the real MIME type via magic bytes,
    then instantiates the corresponding loader.

    Parameters
    ----------
    validator:
        Optional ``FileValidator`` instance.  A default one is created
        if not provided.
    """

    def __init__(self, validator: FileValidator | None = None) -> None:
        self._validator = validator or FileValidator()

    def load(self, file_path: Path) -> LoadedDocument:
        """Validate the file, select the right loader, and load the document.

        Parameters
        ----------
        file_path:
            Path to the file on disk.

        Returns
        -------
        LoadedDocument
            The loaded document with text, metadata, and page count.

        Raises
        ------
        FileValidationError
            If the file fails validation (wrong type, too large, etc.).
        ValueError
            If the detected MIME type has no registered loader.
        """
        mime_type = self._validator.validate(file_path)

        loader_cls = _MIME_TO_LOADER.get(mime_type)
        if loader_cls is None:
            raise ValueError(f"No loader registered for MIME type: {mime_type}")

        loader = loader_cls()

        logger.info(
            "loading_document file=%s mime=%s loader=%s",
            file_path.name,
            mime_type,
            loader_cls.__name__,
        )

        return loader.load(file_path)
