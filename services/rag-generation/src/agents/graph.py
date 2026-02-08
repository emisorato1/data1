"""StateGraph principal del servicio RAG Generation.

Define el grafo de ejecución multi-agente usando LangGraph,
orquestando el flujo entre el Orchestrator, Public Agent y Private Agent.

Uso:
  El servidor custom (src/server.py) llama a create_graph_builder()
  para obtener el builder sin compilar, y lo compila con
  AsyncPostgresSaver + AsyncPostgresStore.
"""

from langgraph.graph import StateGraph, START, END

from src.agents.state import RAGState
from src.agents.orchestrator import orchestrator_node
from src.agents.public_agent import public_agent_node
from src.agents.private_agent import private_agent_node
from src.agents.routes import route_to_agent


def create_graph_builder() -> StateGraph:
    """Crea el StateGraph builder SIN compilar.

    Usado por src/server.py para compilar con checkpointer y store propios.

    Define la topología del grafo multi-agente:
      START → orchestrator → (routing) → public_agent | private_agent → END

    Returns:
        StateGraph configurado con nodos y edges, listo para compilar.
    """
    graph = StateGraph(RAGState)

    # Nodos del grafo
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("public_agent", public_agent_node)
    graph.add_node("private_agent", private_agent_node)

    # Flujo del grafo
    # 1. START → orchestrator
    graph.add_edge(START, "orchestrator")

    # 2. orchestrator → routing condicional basado en current_agent
    graph.add_conditional_edges(
        "orchestrator",
        route_to_agent,
        {
            "public_agent": "public_agent",
            "private_agent": "private_agent",
        },
    )

    # 3. Agentes → END
    graph.add_edge("public_agent", END)
    graph.add_edge("private_agent", END)

    return graph
