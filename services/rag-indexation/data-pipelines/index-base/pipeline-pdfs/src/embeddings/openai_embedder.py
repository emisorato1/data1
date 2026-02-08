"""
Embeddings con OpenAI API.
"""

import os
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("EMBEDDING_MODEL") or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

_client = None


def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def get_embeddings(texts: list[str], trace=None) -> list[list[float]]:
    """
    Genera embeddings para una lista de textos.
    
    Args:
        texts: Lista de strings
        trace: Optional Langfuse trace object to link generation
    
    Returns:
        Lista de embeddings (cada uno es una lista de floats)
    """
    if not texts:
        return []
    
    client = get_client()
    
    response = client.embeddings.create(
        model=OPENAI_MODEL,
        input=texts
    )
    
    # Langfuse Generation Logging for Cost Tracking
    if trace:
        try:
            # Langfuse expects usage in a specific format compatible with OpenAI's response
            trace.generation(
                name="openai_embeddings",
                model=OPENAI_MODEL,
                input=texts,
                output={"object": "list", "data_len": len(response.data)},
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            )
        except Exception as e:
            print(f"⚠️ Error logging embedding generation: {e}")
    
    return [item.embedding for item in response.data]


def get_embedding(text: str, trace=None) -> list[float]:
    """Genera embedding para un solo texto."""
    return get_embeddings([text], trace=trace)[0]
