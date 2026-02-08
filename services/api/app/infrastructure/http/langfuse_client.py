from langfuse import Langfuse, get_client, observe
from app.core.config import settings

# Inicialización condicional del cliente
_langfuse: Langfuse | None = None

def get_langfuse() -> Langfuse | None:
    global _langfuse
    if settings.LANGFUSE_ENABLED and _langfuse is None:
        _langfuse = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_BASE_URL,
        )
    return _langfuse

def get_current_trace_id() -> str | None:
    """Obtiene el trace_id actual del contexto de Langfuse."""
    try:
        langfuse = get_client()
        return langfuse.get_current_trace_id()
    except Exception:
        return None