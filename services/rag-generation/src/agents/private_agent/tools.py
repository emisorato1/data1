"""Tools para el Agente Privado.

Contiene wrappers y utilidades para las herramientas de búsqueda
específicas del agente privado, incluyendo detección de departamentos.
"""

import asyncio
from typing import Optional

from src.tools.vector_search import search_documents
from src.tools.query_rewriter import rewrite_query, contextualize_query


# Mapeo de palabras clave a departamentos para filtrado
DEPARTMENT_KEYWORDS: dict[str, list[str]] = {
    "call_center": [
        "call center", "llamadas", "telefono", "atencion telefonica", "cliente llamó"
    ],
    "branch": [
        "sucursal", "ventanilla", "caja", "cajero", "oficina", "presencial", "branch"
    ],
    "hr": [
        "recursos humanos", "rrhh", "empleado", "nómina", "vacaciones",
        "licencia", "personal", "hr", "human resources"
    ],
}


def detect_department(query: str) -> Optional[str]:
    """Detecta el departamento relevante basándose en palabras clave de la consulta.
    
    Args:
        query: La consulta del usuario.
        
    Returns:
        Nombre del departamento detectado o None si no se detecta ninguno.
    """
    query_lower = query.lower()
    
    for department, keywords in DEPARTMENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                return department
    
    return None


async def search_private_documents(
    query: str,
    k: int = 5,
    score_threshold: float = 0.5,
    department: Optional[str] = None,
) -> list[dict]:
    """Busca documentos privados relevantes para la consulta.
    
    Esta función busca en documentos privados con filtrado opcional
    por departamento.
    
    Args:
        query: La consulta de búsqueda.
        k: Número máximo de documentos a retornar.
        score_threshold: Umbral mínimo de relevancia.
        department: Departamento específico para filtrar (opcional).
        
    Returns:
        Lista de documentos privados relevantes.
    """
    return await asyncio.to_thread(
        search_documents,
        query=query,
        document_type="private",
        k=k,
        score_threshold=score_threshold,
        department=department,
    )


async def search_public_documents(
    query: str,
    k: int = 5,
    score_threshold: float = 0.5,
) -> list[dict]:
    """Busca documentos públicos relevantes para la consulta.
    
    El agente privado también tiene acceso a documentos públicos.
    
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


def merge_and_deduplicate_documents(
    private_docs: list[dict],
    public_docs: list[dict],
    max_results: int = 8,
) -> list[dict]:
    """Combina y deduplica documentos de ambas fuentes.
    
    Ordena por relevancia y elimina duplicados basándose en document_id.
    
    Args:
        private_docs: Documentos privados recuperados.
        public_docs: Documentos públicos recuperados.
        max_results: Número máximo de documentos a retornar.
        
    Returns:
        Lista de documentos únicos ordenados por relevancia.
    """
    all_docs = private_docs + public_docs
    
    # Ordenar por relevance_score descendente y eliminar duplicados por document_id
    seen_ids: set[str] = set()
    unique_docs: list[dict] = []
    
    for doc in sorted(all_docs, key=lambda x: x["relevance_score"], reverse=True):
        doc_id = doc["document_id"]
        if doc_id not in seen_ids:
            seen_ids.add(doc_id)
            unique_docs.append(doc)
    
    return unique_docs[:max_results]
