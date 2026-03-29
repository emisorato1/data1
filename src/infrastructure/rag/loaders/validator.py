import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


@dataclass(frozen=True)
class FileSignature:
    """Firma binaria de un tipo de archivo."""

    magic_bytes: bytes
    offset: int = 0
    mime_type: str = ""
    description: str = ""


class AllowedFileType(Enum):
    """Tipos de archivo permitidos con sus magic bytes."""

    PDF = FileSignature(
        magic_bytes=b"%PDF",
        mime_type="application/pdf",
        description="PDF document",
    )
    DOCX = FileSignature(
        magic_bytes=b"PK\x03\x04",  # ZIP-based
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        description="Microsoft Word (DOCX)",
    )
    TXT = FileSignature(
        magic_bytes=b"",  # Sin magic bytes para texto plano
        mime_type="text/plain",
        description="Plain Text",
    )
    CSV = FileSignature(
        magic_bytes=b"",  # Sin magic bytes consistentes para CSV
        mime_type="text/csv",
        description="Comma-Separated Values",
    )


DANGEROUS_SIGNATURES = [
    b"MZ",  # Windows executables
    b"\x7fELF",  # Linux executables
    b"#!/",  # Shell scripts
    b"<?php",  # PHP scripts
    b"<script",  # HTML/JS
]


class FileValidationError(Exception):
    """Error de validación de archivo."""

    pass


class FileSizeError(FileValidationError):
    """Error específico para archivos que exceden el tamaño máximo."""

    pass


class FileValidator:
    """Valida archivos por magic bytes y contenido."""

    def __init__(
        self,
        allowed_types: list[AllowedFileType] | None = None,
        max_file_size: int = 50 * 1024 * 1024,  # 50 MB
    ):
        self.allowed_types = allowed_types or list(AllowedFileType)
        self.max_file_size = max_file_size

    def validate(self, file_path: Path) -> str:
        """
        Valida el archivo y retorna el MIME type real detectado.
        """
        if not file_path.exists():
            raise FileValidationError(f"El archivo no existe: {file_path}")

        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            raise FileSizeError(f"Archivo excede el tamaño máximo ({file_size} > {self.max_file_size} bytes)")

        if file_size == 0:
            raise FileValidationError("Archivo vacío")

        with open(file_path, "rb") as f:
            content = f.read(4096)  # Leer suficiente para magic bytes e inspección inicial

        # 1. Verificar firmas peligrosas
        for sig in DANGEROUS_SIGNATURES:
            if content.startswith(sig):
                raise FileValidationError("Archivo rechazado: formato potencialmente peligroso")

        # 2. Detectar tipo por magic bytes o extension para texto plano
        detected_type = self._detect_type(content, file_path)
        if not detected_type:
            raise FileValidationError(f"Tipo de archivo no reconocido o no permitido: {file_path.name}")

        # 3. Validación adicional para DOCX (ZIP-based)
        if detected_type == AllowedFileType.DOCX and not self._is_valid_docx(file_path):
            raise FileValidationError(f"El archivo no es un documento DOCX válido: {file_path.name}")

        # 4. Validar que la extensión coincida con el tipo detectado
        self._validate_extension(file_path, detected_type)

        return detected_type.value.mime_type

    def _detect_type(self, content: bytes, file_path: Path) -> AllowedFileType | None:
        """Detecta el tipo de archivo por magic bytes o por extensión si no tiene magic bytes fijos."""
        for file_type in self.allowed_types:
            sig = file_type.value
            if sig.magic_bytes:
                # Comprobar magic bytes para archivos binarios
                if content[sig.offset : sig.offset + len(sig.magic_bytes)] == sig.magic_bytes:
                    return file_type
            else:
                # Para archivos de texto (txt, csv), comprobamos la extensión y si es decodificable
                ext = file_path.suffix.lower()
                if (file_type == AllowedFileType.TXT and ext == ".txt") or (
                    file_type == AllowedFileType.CSV and ext == ".csv"
                ):
                    try:
                        content.decode("utf-8")
                        return file_type
                    except UnicodeDecodeError:
                        pass  # No es texto plano valido

        return None

    def _is_valid_docx(self, file_path: Path) -> bool:
        """Verifica si un archivo ZIP es realmente un DOCX."""
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                names = zf.namelist()
                return "word/document.xml" in names
        except zipfile.BadZipFile:
            return False

    def _validate_extension(self, file_path: Path, detected_type: AllowedFileType) -> None:
        ext = file_path.suffix.lower()
        if detected_type == AllowedFileType.PDF and ext != ".pdf":
            raise FileValidationError(f"Extensión '{ext}' no coincide con tipo detectado PDF")
        if detected_type == AllowedFileType.DOCX and ext != ".docx":
            raise FileValidationError(f"Extensión '{ext}' no coincide con tipo detectado DOCX")
        if detected_type == AllowedFileType.TXT and ext != ".txt":
            raise FileValidationError(f"Extensión '{ext}' no coincide con tipo detectado TXT")
        if detected_type == AllowedFileType.CSV and ext != ".csv":
            raise FileValidationError(f"Extensión '{ext}' no coincide con tipo detectado CSV")
