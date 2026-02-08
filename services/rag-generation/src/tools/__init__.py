"""Herramientas para los agentes RAG.

Búsqueda vectorial adaptada al esquema del servicio rag-indexation.
Filtra documentos por metadata->>'description' (public/private).
"""

from src.tools.vector_search import search_documents

__all__ = ["search_documents"]
