"""Configuración central del proyecto.

La idea es evitar valores hardcodeados repartidos por el código
para que sea más fácil cambiar parámetros desde un solo lugar.
"""

import os


def _get_env(name: str, default: str | None = None) -> str:
    """Helper simple para leer variables de entorno con default.

    No levanta error si falta, simplemente devuelve el default.
    """

    value = os.getenv(name)
    if value is None:
        return default  # type: ignore[return-value]
    return value


# ---------------- Embeddings / modelos ---------------- #

# Nombre del modelo de embeddings (SentenceTransformers)
EMBEDDING_MODEL_NAME: str = _get_env(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/all-MiniLM-L6-v2",
)


# ---------------- Chunking determinístico ---------------- #

# Tamaño de cada chunk en caracteres
CHUNK_SIZE: int = int(_get_env("CHUNK_SIZE", "1000"))

# Solapamiento entre chunks en caracteres
CHUNK_OVERLAP: int = int(_get_env("CHUNK_OVERLAP", "200"))


# ---------------- Ingesta / paths ---------------- #

DEFAULT_INPUT_FILE: str = _get_env(
    "DEFAULT_INPUT_FILE",
    "data/raw/ejemplo.pdf",
)


# ---------------- Query / búsqueda ---------------- #

DEFAULT_QUERY_TEXT: str = _get_env(
    "DEFAULT_QUERY_TEXT",
    "Operaciones entre objetos en Python",
)

DEFAULT_QUERY_LIMIT: int = int(_get_env("DEFAULT_QUERY_LIMIT", "5"))


# ---------------- Langfuse Observability ---------------- #

LANGFUSE_PUBLIC_KEY: str = _get_env("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY: str = _get_env("LANGFUSE_SECRET_KEY", "")
LANGFUSE_BASE_URL: str = _get_env("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")
LANGFUSE_ENABLED: bool = _get_env("LANGFUSE_ENABLED", "false").lower() == "true"

