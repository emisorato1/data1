"""DTOs para el pipeline de retrieval RAG.

Clases de datos usadas en búsqueda híbrida, reranking y ensamblado de
contexto.  Son dataclasses puras (sin dependencias de ORM/framework) para
facilitar testing y portabilidad.

Ver spec T4-S2-01 y rag-retrieval/SKILL.md (sección Clases de datos).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


@dataclass
class StoredChunk:
    """Chunk recuperado de la base de datos con su score de relevancia.

    Attributes
    ----------
    id:
        PK interno del chunk (UUID generado por PostgreSQL).
    document_id:
        BIGINT — alineado con ``documents.id`` (y DTREE.DataID de OpenText).
    chunk_index:
        Posición ordinal del chunk dentro del documento.
    content:
        Texto del chunk.
    area:
        Área funcional (``"riesgos"``, ``"cumplimiento"``, etc.).
    metadata:
        JSONB con metadatos arbitrarios del chunk.
    score:
        Score de relevancia asignado por la etapa de búsqueda o reranking.
        Mayor es más relevante.
    document_name:
        Nombre del archivo fuente (``documents.filename``).
    page_number:
        Número de página dentro del documento (si está disponible en metadata).
    """

    id: UUID
    document_id: int
    chunk_index: int
    content: str
    area: str
    metadata: dict
    score: float = 0.0
    document_name: str | None = None
    page_number: int | None = None

    @classmethod
    def from_row(cls, row: dict) -> StoredChunk:
        """Construye un ``StoredChunk`` desde un dict de fila SQL.

        Compatible con los resultados de ``PgVectorStore.similarity_search``,
        ``bm25_search`` e ``hybrid_search``.
        """
        return cls(
            id=row["id"],
            document_id=row["document_id"],
            chunk_index=row["chunk_index"],
            content=row["content"],
            area=row.get("area", "general"),
            metadata=row.get("metadata") or {},
            score=float(row.get("score", 0.0)),
            document_name=row.get("document_name"),
            page_number=(row.get("metadata") or {}).get("page_number"),
        )


@dataclass
class RetrievalMetrics:
    """Métricas de latencia por componente del pipeline de retrieval.

    Todos los valores están en milisegundos.
    """

    cache_ms: float = 0.0
    embedding_ms: float = 0.0
    vector_search_ms: float = 0.0
    bm25_search_ms: float = 0.0
    rrf_fusion_ms: float = 0.0
    rerank_ms: float = 0.0
    total_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "cache_ms": self.cache_ms,
            "embedding_ms": self.embedding_ms,
            "vector_search_ms": self.vector_search_ms,
            "bm25_search_ms": self.bm25_search_ms,
            "rrf_fusion_ms": self.rrf_fusion_ms,
            "rerank_ms": self.rerank_ms,
            "total_ms": self.total_ms,
        }


@dataclass
class RetrievalResult:
    """Resultado completo de una operación de retrieval.

    Attributes
    ----------
    chunks:
        Lista ordenada de chunks recuperados (mayor score = más relevante).
    query:
        Query original del usuario.
    metrics:
        Métricas de latencia por componente.
    from_cache:
        ``True`` si el resultado fue servido desde caché semántica.
    """

    chunks: list[StoredChunk]
    query: str
    metrics: RetrievalMetrics = field(default_factory=RetrievalMetrics)
    from_cache: bool = False

    def to_dict(self) -> dict:
        return {
            "chunks": [
                {
                    "id": str(c.id),
                    "document_id": c.document_id,
                    "chunk_index": c.chunk_index,
                    "content": c.content,
                    "area": c.area,
                    "score": c.score,
                    "metadata": c.metadata,
                    "document_name": c.document_name,
                    "page_number": c.page_number,
                }
                for c in self.chunks
            ],
            "query": self.query,
            "metrics": self.metrics.to_dict(),
            "from_cache": self.from_cache,
        }
