"""Nodo Orquestador para el grafo RAG.

Este nodo es responsable de:
1. Recibir la consulta del usuario
2. Cargar memorias del usuario (long-term memory)
3. Clasificarla como pública o privada
4. Determinar el agente apropiado para procesarla
"""

from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from src.config.llm_config import get_orchestrator_llm
from src.agents.state import RAGState
from src.agents.memory import (
    get_user_id_from_config,
    search_user_memories,
    format_memories_as_context,
    MEMORY_TYPE_FACTS,
)
from src.agents.orchestrator.prompt import CLASSIFIER_SYSTEM_PROMPT, CLASSIFIER_QUERY_TEMPLATE


async def classify_query(query: str) -> Literal["public", "private"]:
    """Clasifica una consulta como pública o privada usando el LLM.
    
    Args:
        query: La consulta del usuario a clasificar.
        
    Returns:
        "public" o "private" según la clasificación.
    """
    llm = get_orchestrator_llm()
    
    messages = [
        SystemMessage(content=CLASSIFIER_SYSTEM_PROMPT),
        HumanMessage(content=CLASSIFIER_QUERY_TEMPLATE.format(query=query)),
    ]
    
    response = await llm.ainvoke(messages)
    classification = response.content.strip().lower()
    
    # Normalizar la respuesta
    if "private" in classification or "privado" in classification:
        return "private"
    return "public"


async def orchestrator_node(
    state: RAGState,
    config: RunnableConfig,
    *,
    store: BaseStore,
) -> dict:
    """Nodo orquestador que determina el agente apropiado para procesar la consulta.
    
    Este nodo:
    1. Carga memorias del usuario desde el store (long-term memory)
    2. Analiza el rol del usuario y el contenido de la consulta
    3. Decide si debe ser procesada por el agente público o privado
    
    Args:
        state: Estado actual del grafo RAG con la información de la consulta.
        config: Configuración del runnable con user_id, tenant_id, etc.
        store: Store de LangGraph para memoria a largo plazo.
        
    Returns:
        Diccionario con el agente seleccionado, memorias y metadata.
    """
    user_role = state["user_role"]
    message = state["message"]
    
    # 1. Cargar memorias del usuario (long-term memory)
    user_id = get_user_id_from_config(config)
    user_memories = []
    memory_context = ""
    
    if store and user_id != "anonymous":
        # Buscar memorias relevantes para la consulta actual (async)
        user_memories = await search_user_memories(
            store=store,
            user_id=user_id,
            query=message,
            memory_type=MEMORY_TYPE_FACTS,
            limit=5,
        )
        memory_context = format_memories_as_context(user_memories)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
    # 2. Determinar el agente destino
    if user_role == "public":
        target_agent = "public_agent"
    else:
        # Usuario privado: clasificar la consulta
        query_type = await classify_query(message)
        target_agent = "public_agent" if query_type == "public" else "private_agent"
    
    # 3. Retornar estado actualizado con memorias
    return {
        "current_agent": target_agent,
        "user_memories": user_memories,
        "memory_context": memory_context,
        "metadata": {
            **state.get("metadata", {}),
            "routing_decision": target_agent,
            "user_role": user_role,
            "user_id": user_id,
            "memories_loaded": len(user_memories),
        },
    }
