from pathlib import Path
from typing import Protocol, runtime_checkable

from .models import LoadedDocument


@runtime_checkable
class DocumentLoader(Protocol):
    """Interfaz común para cargadores de documentos."""

    def load(self, file_path: Path) -> LoadedDocument:
        """
        Carga y procesa un archivo de documento.

        Args:
            file_path: Ruta al archivo en el sistema de archivos.

        Returns:
            LoadedDocument: Objeto con el contenido y metadata extraídos.

        Raises:
            Exception: Si ocurre un error durante la carga o procesamiento.
        """
        ...
