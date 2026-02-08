"""Función de routing para el grafo de agentes RAG.

Este módulo contiene la función que determina a qué agente
debe ser dirigida cada consulta basándose en el estado actual.
"""

from typing import Literal

from src.agents.state import RAGState


def route_to_agent(state: RAGState) -> Literal["public_agent", "private_agent"]:
    """Determina el agente al que debe dirigirse la consulta.
    
    Esta función es utilizada por LangGraph para el routing condicional
    después del nodo orquestador. Lee el campo `current_agent` del estado
    que fue establecido por el orquestador.
    
    Args:
        state: Estado actual del grafo RAG con la decisión del orquestador.
        
    Returns:
        Nombre del agente destino: "public_agent" o "private_agent".
        
    Example:
        ```python
        graph.add_conditional_edges(
            "orchestrator",
            route_to_agent,
            {
                "public_agent": "public_agent",
                "private_agent": "private_agent",
            },
        )
        ```
    """
    current_agent = state.get("current_agent", "public_agent")
    
    # Validar que el agente sea válido
    if current_agent not in ("public_agent", "private_agent"):
        # Default a public_agent si hay un valor inválido
        return "public_agent"
    
    return current_agent
