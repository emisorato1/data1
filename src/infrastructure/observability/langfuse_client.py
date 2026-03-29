"""Langfuse observability wrapper.

Centraliza la interacción con el SDK de Langfuse proveyendo:
- Feature flag ``LANGFUSE_ENABLED`` para activar/desactivar toda la instrumentación.
- Degradación graceful si el paquete ``langfuse`` no está instalado.
- Factory ``create_callback_handler()`` que crea un handler fresh por request
  (requerido por SDK v3 para heredar el trace context actual).
- ``flush_langfuse()`` / ``shutdown_langfuse()`` centralizados.

Ref: https://langfuse.com/docs/sdk/python
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

import structlog

from src.config.settings import settings

if TYPE_CHECKING:
    from collections.abc import Generator

logger = structlog.get_logger()

try:
    from langfuse import Langfuse
    from langfuse import observe as langfuse_observe
    from langfuse import propagate_attributes as langfuse_propagate_attributes
    from langfuse.langchain import CallbackHandler

    _langfuse_available = True
except ImportError:
    logger.warning("langfuse package not installed — observability features disabled")
    _langfuse_available = False
    Langfuse = None  # type: ignore[assignment,misc]
    CallbackHandler = None  # type: ignore[assignment,misc]
    langfuse_observe = None  # type: ignore[assignment]
    langfuse_propagate_attributes = None  # type: ignore[assignment]

_langfuse: Langfuse | None = None


def is_langfuse_enabled() -> bool:
    """Return True if Langfuse is available and enabled."""
    return _langfuse_available and settings.langfuse_enabled


def get_langfuse() -> Langfuse | None:
    """Obtiene o inicializa el cliente singleton de Langfuse."""
    global _langfuse
    if not _langfuse_available:
        return None
    if _langfuse is None and settings.langfuse_enabled:
        try:
            _langfuse = Langfuse(
                public_key=settings.langfuse_public_key.get_secret_value(),
                secret_key=settings.langfuse_secret_key.get_secret_value(),
                base_url=settings.langfuse_host,
            )
            logger.info("Langfuse client initialized")
        except Exception as e:
            logger.error("Failed to initialize Langfuse client", error=str(e))
    return _langfuse


def create_callback_handler() -> CallbackHandler | None:
    """Crea un CallbackHandler fresh para LangChain/LangGraph.

    IMPORTANTE: Debe llamarse dentro de una función decorada con ``@observe``
    para que el handler herede el trace context de la traza actual.
    Un handler por request garantiza aislamiento de trazas entre requests
    concurrentes.
    """
    if not is_langfuse_enabled():
        return None
    return CallbackHandler()  # type: ignore[misc]


def observe(*args: Any, **kwargs: Any) -> Any:
    """Decorator wrapper de ``@observe`` del SDK.

    Si Langfuse está deshabilitado o no instalado, retorna un no-op decorator.
    """
    if not is_langfuse_enabled():

        def no_op_decorator(func: Any) -> Any:
            return func

        return no_op_decorator

    return langfuse_observe(*args, **kwargs)


@contextmanager
def propagate_attributes(**kwargs: Any) -> Generator[None, None, None]:
    """Context manager wrapper de ``propagate_attributes`` del SDK v3.

    Propaga ``user_id``, ``session_id``, ``tags``, ``metadata`` y ``version``
    a todas las observaciones anidadas.
    """
    if not is_langfuse_enabled() or langfuse_propagate_attributes is None:
        yield
        return

    with langfuse_propagate_attributes(**kwargs):
        yield


def flush_langfuse() -> None:
    """Asegura que todos los traces se envíen antes de cerrar."""
    if _langfuse:
        _langfuse.flush()


def shutdown_langfuse() -> None:
    """Finaliza el cliente para procesos batch cortos como Airflow tasks."""
    global _langfuse
    if _langfuse:
        _langfuse.shutdown()
        _langfuse = None
