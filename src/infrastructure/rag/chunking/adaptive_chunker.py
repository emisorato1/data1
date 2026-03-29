"""
Adaptive chunker para documentos bancarios.

Segmenta documentos en chunks de ~4KB (1000 tokens) con 15% overlap,
detectando y preservando tablas como unidades atómicas.
"""

import re
from dataclasses import dataclass, field
from typing import Any

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config.settings import settings
from src.infrastructure.rag.loaders.models import LoadedDocument


@dataclass(frozen=True)
class Chunk:
    """Representa un chunk de documento procesado."""

    text: str
    metadata: dict[str, Any]
    token_count: int


@dataclass
class ChunkingConfig:
    """Configuración para el chunker adaptativo."""

    chunk_size: int = settings.chunk_size
    chunk_overlap: int = settings.chunk_overlap
    # Separadores jerárquicos para split
    separators: list[str] = field(default_factory=lambda: ["\n\n", "\n", ". ", " "])
    # Encoding de tiktoken
    encoding_name: str = "cl100k_base"


class AdaptiveChunker:
    """
    Chunker adaptativo para documentos bancarios.

    Características:
    - Usa RecursiveCharacterTextSplitter como base
    - Preserva tablas como chunks atómicos (no se parten)
    - Cada chunk preserva metadata del documento padre
    - Configurable por tipo de documento
    """

    # Patrones para detectar tablas
    # Tablas markdown/ASCII con |
    TABLE_PATTERN_PIPE = re.compile(
        r"(?:^|\n)(\|[^\n]+\|\n(?:\|[-:| ]+\|\n)?(?:\|[^\n]+\|\n?)+)",
        re.MULTILINE,
    )
    # Tablas con separadores de espacios/tabs alineados
    TABLE_PATTERN_ALIGNED = re.compile(
        r"(?:^|\n)((?:[ \t]*\S+[ \t]{2,}\S+[^\n]*\n){3,})",
        re.MULTILINE,
    )
    # Tablas envueltas en [TABLA]...[/TABLA] por loaders
    TABLE_PATTERN_TAGGED = re.compile(
        r"\[TABLA\].*?\[/TABLA\]",
        re.DOTALL,
    )

    def __init__(self, config: ChunkingConfig | None = None) -> None:
        """
        Inicializa el chunker con configuración opcional.

        Args:
            config: Configuración de chunking. Si es None, usa valores default.
        """
        self.config = config or ChunkingConfig()
        self._tokenizer = tiktoken.get_encoding(self.config.encoding_name)

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=self.config.separators,
            length_function=self._count_tokens,
        )

    def _count_tokens(self, text: str) -> int:
        """Cuenta tokens usando tiktoken."""
        return len(self._tokenizer.encode(text))

    def _detect_tables(self, text: str) -> list[tuple[int, int, str]]:
        """
        Detecta tablas en el texto y retorna sus posiciones.

        Returns:
            Lista de tuplas (start, end, table_text) ordenadas por posición.
        """
        tables: list[tuple[int, int, str]] = []

        # Buscar tablas con pipes
        for match in self.TABLE_PATTERN_PIPE.finditer(text):
            tables.append((match.start(1), match.end(1), match.group(1)))

        # Buscar tablas alineadas
        for match in self.TABLE_PATTERN_ALIGNED.finditer(text):
            table_text = match.group(1)
            # Verificar que tenga al menos 3 columnas implícitas
            lines = table_text.strip().split("\n")
            if len(lines) >= 3:
                tables.append((match.start(1), match.end(1), table_text))

        # Buscar tablas envueltas en [TABLA]...[/TABLA]
        for match in self.TABLE_PATTERN_TAGGED.finditer(text):
            tables.append((match.start(), match.end(), match.group()))

        # Eliminar solapamientos (mantener la tabla más larga)
        tables.sort(key=lambda x: x[0])
        filtered: list[tuple[int, int, str]] = []
        for table in tables:
            if not filtered or table[0] >= filtered[-1][1]:
                filtered.append(table)
            elif len(table[2]) > len(filtered[-1][2]):
                filtered[-1] = table

        return filtered

    def _extract_segments(self, text: str, tables: list[tuple[int, int, str]]) -> list[tuple[str, bool]]:
        """
        Extrae segmentos de texto y tablas en orden.

        Returns:
            Lista de tuplas (segment_text, is_table).
        """
        if not tables:
            return [(text, False)]

        segments: list[tuple[str, bool]] = []
        last_end = 0

        for start, end, table_text in tables:
            # Texto antes de la tabla
            if start > last_end:
                text_before = text[last_end:start].strip()
                if text_before:
                    segments.append((text_before, False))

            # La tabla misma
            segments.append((table_text.strip(), True))
            last_end = end

        # Texto después de la última tabla
        if last_end < len(text):
            text_after = text[last_end:].strip()
            if text_after:
                segments.append((text_after, False))

        return segments

    def chunk(self, document: LoadedDocument) -> list[Chunk]:
        """
        Divide un documento en chunks preservando tablas como unidades atómicas.

        Args:
            document: Documento cargado con texto y metadata.

        Returns:
            Lista de chunks con metadata preservada.
        """
        return self._chunk_with_splitter(document, self._splitter)

    def chunk_with_separators(
        self,
        document: LoadedDocument,
        separators: list[str],
    ) -> list[Chunk]:
        """
        Divide documento con separadores personalizados.

        Args:
            document: Documento cargado.
            separators: Lista de separadores a usar.

        Returns:
            Lista de chunks.
        """
        custom_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=separators,
            length_function=self._count_tokens,
        )
        return self._chunk_with_splitter(document, custom_splitter)

    def _chunk_with_splitter(
        self,
        document: LoadedDocument,
        splitter: RecursiveCharacterTextSplitter,
    ) -> list[Chunk]:
        """Lógica interna de chunking con un splitter dado (thread-safe)."""
        text = document.text
        base_metadata = document.metadata

        # Detectar tablas
        tables = self._detect_tables(text)

        # Extraer segmentos (texto y tablas)
        segments = self._extract_segments(text, tables)

        chunks: list[Chunk] = []
        chunk_index = 0

        for segment_text, is_table in segments:
            if is_table:
                # Tabla completa = 1 chunk (no se parte)
                token_count = self._count_tokens(segment_text)
                chunk_metadata = {
                    "doc_id": base_metadata.get("doc_id"),
                    "chunk_index": chunk_index,
                    "page_number": base_metadata.get("page_number"),
                    "source_file": base_metadata.get("source_file") or base_metadata.get("source"),
                    "has_table": True,
                }
                chunks.append(
                    Chunk(
                        text=segment_text,
                        metadata=chunk_metadata,
                        token_count=token_count,
                    )
                )
                chunk_index += 1
            else:
                # Texto normal: usar el splitter recibido
                split_texts = splitter.split_text(segment_text)
                for split_text in split_texts:
                    token_count = self._count_tokens(split_text)
                    chunk_metadata = {
                        "doc_id": base_metadata.get("doc_id"),
                        "chunk_index": chunk_index,
                        "page_number": base_metadata.get("page_number"),
                        "source_file": base_metadata.get("source_file") or base_metadata.get("source"),
                        "has_table": False,
                    }
                    chunks.append(
                        Chunk(
                            text=split_text,
                            metadata=chunk_metadata,
                            token_count=token_count,
                        )
                    )
                    chunk_index += 1

        return chunks
