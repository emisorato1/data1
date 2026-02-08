"""Módulo Routes para el servicio RAG Generation.

Contiene las funciones de routing para el grafo de agentes.
"""

from src.agents.routes.classifier.route import route_to_agent

__all__ = ["route_to_agent"]
