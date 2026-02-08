"""Módulo Classifier para routing de agentes.

Contiene la lógica de clasificación y routing para determinar
qué agente debe procesar cada consulta.
"""

from src.agents.routes.classifier.route import route_to_agent

__all__ = ["route_to_agent"]
