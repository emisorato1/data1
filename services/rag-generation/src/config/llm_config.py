"""Configuración de LLMs para cada agente del servicio RAG Generation.

Este módulo centraliza la configuración de los modelos de lenguaje utilizados
por cada agente del sistema, permitiendo ajustar parámetros específicos
según el rol de cada uno.
"""

import os
from dataclasses import dataclass
from functools import lru_cache

from langchain_openai import ChatOpenAI


@dataclass
class LLMConfig:
    """Configuración de un modelo LLM."""
    
    model: str
    temperature: float
    max_tokens: int
    timeout: int = 30


# Configuraciones para cada agente
ORCHESTRATOR_CONFIG = LLMConfig(
    model="gpt-4o-mini",  # Modelo ligero para clasificación rápida
    temperature=0.0,      # Determinístico para routing consistente
    max_tokens=256,       # Solo necesita clasificar
    timeout=15,
)

PUBLIC_AGENT_CONFIG = LLMConfig(
    model="gpt-4o",       # Modelo completo para respuestas de calidad
    temperature=0.3,      # Algo de creatividad para respuestas naturales
    max_tokens=1024,
    timeout=30,
)

PRIVATE_AGENT_CONFIG = LLMConfig(
    model="gpt-4o",       # Modelo completo para datos sensibles
    temperature=0.1,      # Más conservador con información privada
    max_tokens=1024,
    timeout=30,
)


def _get_api_key() -> str:
    """Obtiene la API key de OpenAI desde variable de entorno."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY no está configurada. "
            "Por favor, configura la variable de entorno."
        )
    return api_key


def _create_llm(config: LLMConfig) -> ChatOpenAI:
    """Crea una instancia de ChatOpenAI con la configuración especificada."""
    return ChatOpenAI(
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout=config.timeout,
        api_key=_get_api_key(),
        streaming=True,
    )


@lru_cache(maxsize=1)
def get_orchestrator_llm() -> ChatOpenAI:
    """Obtiene el LLM para el Orquestador (clasificación de consultas)."""
    return _create_llm(ORCHESTRATOR_CONFIG)


@lru_cache(maxsize=1)
def get_public_agent_llm() -> ChatOpenAI:
    """Obtiene el LLM para el Agente de Información Pública."""
    return _create_llm(PUBLIC_AGENT_CONFIG)


@lru_cache(maxsize=1)
def get_private_agent_llm() -> ChatOpenAI:
    """Obtiene el LLM para el Agente de Información Privada."""
    return _create_llm(PRIVATE_AGENT_CONFIG)