"""Configuración central del pipeline DOCX.

La idea es evitar valores hardcodeados repartidos por el código
para que sea más fácil cambiar parámetros desde un solo lugar.
"""

import os


def _get_env(name: str, default: str | None = None) -> str:
    """Helper simple para leer variables de entorno con default."""
    value = os.getenv(name)
    if value is None:
        return default  # type: ignore[return-value]
    return value


# ---------------- Embeddings / modelos ---------------- #

EMBEDDING_MODEL_NAME: str = _get_env(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/all-MiniLM-L6-v2",
)


# ---------------- Chunking semántico ---------------- #

SEMANTIC_MODEL_NAME: str = _get_env(
    "SEMANTIC_MODEL_NAME",
    EMBEDDING_MODEL_NAME,
)

SEMANTIC_THRESHOLD: float = float(_get_env("SEMANTIC_THRESHOLD", "0.7"))

MAX_SENTENCES_PER_CHUNK: int = int(_get_env("MAX_SENTENCES_PER_CHUNK", "5"))


# ---------------- Ingesta / paths ---------------- #

DEFAULT_INPUT_FILE: str = _get_env(
    "DEFAULT_INPUT_FILE",
    "data/raw/ejemplo.docx",
)


# ---------------- Query / búsqueda ---------------- #

DEFAULT_QUERY_TEXT: str = _get_env(
    "DEFAULT_QUERY_TEXT",
    "Operaciones entre objetos en Python",
)

DEFAULT_QUERY_LIMIT: int = int(_get_env("DEFAULT_QUERY_LIMIT", "5"))
