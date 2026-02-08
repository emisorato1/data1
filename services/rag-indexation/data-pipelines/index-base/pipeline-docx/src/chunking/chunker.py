from chunking.semantic_chunker import semantic_chunk


def chunk_document(document):
    raw_chunks = semantic_chunk(document.content)

    chunks = []
    for i, text in enumerate(raw_chunks):
        chunks.append({
            "content": text,
            "metadata": {
                **document.metadata,
                "chunk_id": i,
                "chunk_type": "semantic",
            }
        })

    return chunks
