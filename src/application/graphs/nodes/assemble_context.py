"""Nodo assemble_context: formatea chunks rerankeados en contexto con citaciones.

Ensambla los chunks recuperados y rerankeados en un texto de contexto
con citaciones numeradas [1], [2], etc. y genera la lista de sources
para metadata de la respuesta.

Separado del nodo generate para permitir cambiar el formato de contexto
sin tocar la lógica de generación.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.infrastructure.observability.langfuse_client import observe

if TYPE_CHECKING:
    from src.application.graphs.state import RAGState

logger = logging.getLogger(__name__)

_NO_CONTEXT_TEXT = ""


@observe(name="rag_assemble_context")
def assemble_context_node(state: RAGState) -> dict:
    """Ensambla el contexto final con citaciones [N] desde chunks rerankeados.

    Cada chunk se formatea como:
        [N] <contenido>
        (Fuente: <nombre_documento>, p.<pagina>)

    Si no hay chunks disponibles, retorna contexto vacío y sources vacías,
    delegando al nodo generate la decisión de responder con fallback.

    Returns
    -------
    dict
        context_text: str con el contexto formateado.
        sources: list[dict] con metadata de cada fuente citada.
    """
    chunks = state.get("reranked_chunks") or state.get("retrieved_chunks") or []

    if not chunks:
        logger.info("assemble_context: sin chunks disponibles")
        return {
            "context_text": _NO_CONTEXT_TEXT,
            "sources": [],
        }

    sources: list[dict] = []
    context_parts: list[str] = []

    for i, chunk in enumerate(chunks, 1):
        content = chunk.get("content", "")
        document_name = chunk.get("document_name", "Documento desconocido")
        page = chunk.get("page", "N/A")
        document_id = chunk.get("document_id")

        context_parts.append(f"[{i}] {content}\n(Fuente: {document_name}, p.{page})")
        sources.append(
            {
                "index": i,
                "document_id": document_id,
                "document_name": document_name,
                "page": page,
                "chunk_text": content,
            }
        )

    context_text = "\n\n".join(context_parts)

    logger.info(
        "assemble_context: %d chunks ensamblados, %d caracteres de contexto",
        len(chunks),
        len(context_text),
    )

    return {
        "context_text": context_text,
        "sources": sources,
    }
