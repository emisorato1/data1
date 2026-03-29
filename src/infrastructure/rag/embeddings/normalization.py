"""L2 normalization for truncated Matryoshka embeddings.

When using ``output_dimensionality=768`` (< 3072 native), Gemini returns
vectors whose L2 norm is **not** 1.0.  Cosine distance (``<=>``) in pgvector
assumes unit-length vectors for optimal accuracy, so we **must** normalize
after every embedding call.

See: rag-indexing/references/embedding-normalization.md
"""

from __future__ import annotations

import math

import numpy as np


def normalize_l2(embedding: list[float]) -> list[float]:
    """Normalize a single embedding to unit length (L2 norm = 1.0).

    Returns the original list unchanged when the norm is zero (degenerate
    case — avoids division by zero).
    """
    norm = math.sqrt(sum(x * x for x in embedding))
    if norm == 0:
        return embedding
    return [x / norm for x in embedding]


def normalize_l2_batch(embeddings: list[list[float]]) -> list[list[float]]:
    """Normalize a batch of embeddings using numpy (vectorized, faster).

    Returns a plain Python list-of-lists so the result is JSON-serializable
    and compatible with pgvector string casting.
    """
    if not embeddings:
        return []
    arr = np.array(embeddings, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    # Avoid division by zero for degenerate zero-vectors
    norms[norms == 0] = 1.0
    normalized = arr / norms
    result: list[list[float]] = normalized.tolist()
    return result
