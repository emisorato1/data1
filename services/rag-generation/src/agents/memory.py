"""Módulo de memoria para el grafo RAG.

Proporciona utilidades para gestionar memoria a largo plazo (cross-session)
usando LangGraph Store. La memoria permite recordar información del usuario
entre diferentes conversaciones.
"""

import uuid
import logging
from typing import Any
from datetime import datetime, timezone

from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

logger = logging.getLogger(__name__)


# =============================================================================
# Constantes y Configuración
# =============================================================================

MEMORY_TYPE_FACTS = "facts"


# =============================================================================
# Funciones de Namespace
# =============================================================================

def get_user_namespace(user_id: str, memory_type: str = MEMORY_TYPE_FACTS) -> tuple[str, str]:
    """Genera el namespace para memorias de un usuario.
    
    Args:
        user_id: ID único del usuario.
        memory_type: Tipo de memoria (facts, etc.).
        
    Returns:
        Tupla con el namespace (user_id, memory_type).
    """
    return (user_id, memory_type)


# =============================================================================
# Funciones de Extracción de Config
# =============================================================================

def get_user_id_from_config(config: RunnableConfig) -> str:
    """Extrae el user_id del config de LangGraph.
    
    Args:
        config: Configuración del runnable con configurable.
        
    Returns:
        user_id o "anonymous" si no está presente.
    """
    configurable = config.get("configurable", {})
    return configurable.get("user_id", "anonymous")


# =============================================================================
# Funciones de Búsqueda de Memorias (Asíncronas)
# =============================================================================

async def search_user_memories(
    store: BaseStore,
    user_id: str,
    query: str,
    memory_type: str = MEMORY_TYPE_FACTS,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Busca memorias relevantes para un usuario usando búsqueda semántica.
    
    Args:
        store: Instancia del store de LangGraph.
        user_id: ID del usuario.
        query: Consulta para búsqueda semántica.
        memory_type: Tipo de memoria a buscar.
        limit: Número máximo de resultados.
        
    Returns:
        Lista de memorias encontradas con sus valores.
    """
    if not store or user_id == "anonymous":
        return []
    
    try:
        namespace = get_user_namespace(user_id, memory_type)
        items = await store.asearch(namespace, query=query, limit=min(limit, 50))
        
        return [
            {
                "key": item.key,
                "data": item.value.get("data", ""),
                "type": item.value.get("type", memory_type),
                "created_at": item.value.get("created_at"),
                "metadata": item.value.get("metadata", {}),
            }
            for item in items
        ]
    except Exception as e:
        logger.warning(f"Error buscando memorias para user {user_id}: {e}")
        return []


# =============================================================================
# Funciones de Almacenamiento de Memorias (Asíncronas)
# =============================================================================

async def save_user_memory(
    store: BaseStore,
    user_id: str,
    data: str,
    memory_type: str = MEMORY_TYPE_FACTS,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    """Guarda una nueva memoria para un usuario.
    
    Args:
        store: Instancia del store de LangGraph.
        user_id: ID del usuario.
        data: Contenido de la memoria a guardar.
        memory_type: Tipo de memoria.
        metadata: Metadata adicional opcional.
        
    Returns:
        ID de la memoria creada o None si falló.
    """
    if not store or user_id == "anonymous" or not data:
        return None
    
    try:
        namespace = get_user_namespace(user_id, memory_type)
        memory_id = str(uuid.uuid4())
        
        value = {
            "data": data,
            "type": memory_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        
        await store.aput(namespace, memory_id, value)
        logger.info(f"Memoria guardada para user {user_id}: {memory_id}")
        return memory_id
        
    except Exception as e:
        logger.error(f"Error guardando memoria para user {user_id}: {e}")
        return None


# =============================================================================
# Funciones de Formato para Contexto
# =============================================================================

def format_memories_as_context(memories: list[dict[str, Any]]) -> str:
    """Formatea las memorias como contexto para el LLM.
    
    Args:
        memories: Lista de memorias a formatear.
        
    Returns:
        String formateado con las memorias para incluir en el prompt.
    """
    if not memories:
        return ""
    
    context_parts = ["## Información recordada sobre el usuario:"]
    
    for memory in memories:
        data = memory.get("data", "")
        if data:
            context_parts.append(f"- {data}")
    
    return "\n".join(context_parts)


# =============================================================================
# Funciones de Detección de Memorias
# =============================================================================

def should_remember(message: str) -> bool:
    """Detecta si el mensaje contiene información que debería recordarse.
    
    Busca patrones como:
    - "me llamo...", "mi nombre es..."
    - "recuerda que...", "no olvides que..."
    - "prefiero...", "me gusta..."
    - "trabajo en...", "soy..."
    
    Args:
        message: Mensaje del usuario.
        
    Returns:
        True si el mensaje contiene información memorable.
    """
    message_lower = message.lower()
    
    remember_patterns = [
        "me llamo",
        "mi nombre es",
        "soy ",
        "trabajo en",
        "trabajo como",
        "recuerda que",
        "no olvides",
        "prefiero",
        "me gusta",
        "no me gusta",
        "mi email es",
        "mi correo es",
        "vivo en",
        "mi empresa es",
        "mi equipo es",
        "mi departamento es",
    ]
    
    return any(pattern in message_lower for pattern in remember_patterns)


def extract_memorable_info(message: str) -> str | None:
    """Extrae información memorable de un mensaje.
    
    Esta es una implementación básica. Para producción, considera
    usar un LLM para extraer información estructurada.
    
    Args:
        message: Mensaje del usuario.
        
    Returns:
        Información extraída o None si no se encontró nada memorable.
    """
    if not should_remember(message):
        return None
    
    return message.strip()
