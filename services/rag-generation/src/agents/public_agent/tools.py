"""Tools para el Agente Público.

Contiene wrappers y utilidades para las herramientas de búsqueda
específicas del agente público.
"""

import asyncio

from src.tools.vector_search import search_documents
from src.tools.query_rewriter import rewrite_query, contextualize_query


async def search_public_documents(
    query: str,
    k: int = 8,
    score_threshold: float = 0.5,
) -> list[dict]:
    """Busca documentos públicos relevantes para la consulta.
    
    Esta función es un wrapper de search_documents que filtra
    automáticamente solo documentos públicos.
    
    Args:
        query: La consulta de búsqueda.
        k: Número máximo de documentos a retornar.
        score_threshold: Umbral mínimo de relevancia.
        
    Returns:
        Lista de documentos públicos relevantes.
    """
    return await asyncio.to_thread(
        search_documents,
        query=query,
        document_type="public",
        k=k,
        score_threshold=score_threshold,
    )


async def rewrite_search_query(
    message: str,
    chat_history: list[tuple[str, str]] | None = None,
    memory_context: str = "",
) -> str:
    """Contextualiza y reescribe una consulta para optimizar la búsqueda.
    
    Primero resuelve referencias anafóricas usando el historial y/o memoria
    (ej: "dime la receta" + memoria "le gusta cocinar tacos" → "dime la receta de tacos"),
    luego extrae keywords para búsqueda vectorial.
    
    Args:
        message: Mensaje original del usuario.
        chat_history: Lista de tuplas (role, content) con mensajes recientes.
        memory_context: Contexto de memoria long-term del usuario.
        
    Returns:
        Query optimizada para búsqueda.
    """
    # Paso 1: Contextualizar (resolver referencias del historial o memoria)
    if chat_history or memory_context:
        message = await asyncio.to_thread(
            contextualize_query, message, chat_history, memory_context
        )

    # Paso 2: Reescribir a keywords
    return await asyncio.to_thread(rewrite_query, message)
