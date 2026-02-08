from chunking.deterministic_chunker import chunk_text


def chunk_document(document):
    raw_chunks = chunk_text(document.content)

    chunks = []
    for i, text in enumerate(raw_chunks):
        chunks.append({
            "content": text,
            "metadata": {
                **document.metadata,
                "chunk_id": i,
                "chunk_type": "fixed_size"
            }
        })

    return chunks
