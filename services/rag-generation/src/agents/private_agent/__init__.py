"""Módulo Private Agent para el servicio RAG Generation.

Este módulo contiene el agente especializado en consultas sobre
información privada (mecánica, tecnología, contenido académico, etc.).
"""

from src.agents.private_agent.node import private_agent_node

__all__ = ["private_agent_node"]
