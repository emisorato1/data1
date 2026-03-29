"""Embedding services for the RAG pipeline."""

from src.infrastructure.rag.embeddings.gemini_embeddings import GeminiEmbeddingService
from src.infrastructure.rag.embeddings.normalization import normalize_l2, normalize_l2_batch

__all__ = [
    "GeminiEmbeddingService",
    "normalize_l2",
    "normalize_l2_batch",
]
