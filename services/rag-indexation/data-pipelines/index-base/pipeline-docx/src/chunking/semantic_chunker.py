from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from config import (
    SEMANTIC_MODEL_NAME,
    SEMANTIC_THRESHOLD,
    MAX_SENTENCES_PER_CHUNK,
)

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(SEMANTIC_MODEL_NAME)
    return _model


def semantic_chunk(text: str, threshold: float | None = None, max_sentences: int | None = None):
    if not text:
        return []

    if threshold is None:
        threshold = SEMANTIC_THRESHOLD
    if max_sentences is None:
        max_sentences = MAX_SENTENCES_PER_CHUNK

    sentences = sent_tokenize(text)
    if not sentences:
        return []

    model = get_model()
    embeddings = model.encode(sentences)

    chunks: list[str] = []
    current: list[str] = [sentences[0]]

    for i in range(1, len(sentences)):
        sim = cosine_similarity(
            [embeddings[i - 1]],
            [embeddings[i]],
        )[0][0]

        if sim < threshold or len(current) >= max_sentences:
            chunks.append(" ".join(current))
            current = [sentences[i]]
        else:
            current.append(sentences[i])

    if current:
        chunks.append(" ".join(current))

    return chunks
