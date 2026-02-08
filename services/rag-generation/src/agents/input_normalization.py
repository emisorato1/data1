"""Utilidades para normalizar y validar input del estado RAG."""

from collections.abc import Mapping
from typing import Any, Literal


def normalize_user_role(value: Any) -> Literal["public", "private"]:
    """Normaliza el rol de usuario a un valor soportado."""
    role = str(value or "public").strip().lower()
    return "private" if role == "private" else "public"


def extract_message(state: Mapping[str, Any]) -> str:
    """Obtiene el mensaje actual desde `message` o desde `messages`.

    Prioridad:
    1. `state["message"]` si existe y no está vacío.
    2. Último HumanMessage dentro de `state["messages"]`.
    """
    direct_message = state.get("message")
    if isinstance(direct_message, str) and direct_message.strip():
        return direct_message.strip()

    for msg in reversed(state.get("messages", [])):
        msg_type = getattr(msg, "type", None)
        content = getattr(msg, "content", None)
        if msg_type == "human" and isinstance(content, str) and content.strip():
            return content.strip()

    return ""
