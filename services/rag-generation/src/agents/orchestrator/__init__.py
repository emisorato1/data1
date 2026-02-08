"""Módulo Orchestrator para el servicio RAG Generation.

Este módulo contiene el nodo orquestador que clasifica las consultas
y determina qué agente debe procesarlas.
"""

from src.agents.orchestrator.node import orchestrator_node

__all__ = ["orchestrator_node"]
