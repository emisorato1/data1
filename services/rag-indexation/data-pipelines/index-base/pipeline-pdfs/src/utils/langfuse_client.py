"""
Cliente Singleton de Langfuse para el pipeline de indexación.
"""
from langfuse import Langfuse
import config

_langfuse_client: Langfuse | None = None

def init_langfuse() -> Langfuse | None:
    """Inicializa el cliente de Langfuse."""
    global _langfuse_client
    
    if config.LANGFUSE_ENABLED and _langfuse_client is None:
        try:
            _langfuse_client = Langfuse(
                public_key=config.LANGFUSE_PUBLIC_KEY,
                secret_key=config.LANGFUSE_SECRET_KEY,
                base_url=config.LANGFUSE_BASE_URL
            )
        except Exception as e:
            print(f"⚠️ Error inicializando Langfuse: {e}")
            _langfuse_client = None
            
    return _langfuse_client

def get_langfuse() -> Langfuse | None:
    """Retorna el cliente global."""
    return _langfuse_client

def flush_langfuse():
    """Flushea los eventos pendientes."""
    if _langfuse_client:
        _langfuse_client.flush()
