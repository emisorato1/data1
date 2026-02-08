"""
Módulo para el cliente global de Langfuse.
Se inicializa en main.py y se puede acceder desde cualquier parte de la aplicación.
"""
from langfuse import Langfuse

from app.core.config import settings


# Cliente global de Langfuse (inicializado en main.py)
_langfuse_client: Langfuse | None = None


def init_langfuse() -> Langfuse | None:
    """Inicializa el cliente global de Langfuse si está habilitado."""
    global _langfuse_client
    
    if settings.LANGFUSE_ENABLED and _langfuse_client is None:
        try:
            _langfuse_client = Langfuse(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                base_url=settings.LANGFUSE_BASE_URL,
            )
        except Exception:
            # Si falla la inicialización, simplemente no tenemos cliente
            _langfuse_client = None

    return _langfuse_client


def get_langfuse_client() -> Langfuse | None:
    """Retorna el cliente global de Langfuse si está inicializado."""
    return _langfuse_client


def flush_langfuse() -> None:
    """Envía todos los traces pendientes a Langfuse."""
    if _langfuse_client:
        _langfuse_client.flush()
