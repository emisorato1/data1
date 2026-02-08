from loaders.local_loader import load_local_document
from chunking.chunker import chunk_document
from embeddings.minilm_embedder import embed_texts
from db.postgres import get_connection
from psycopg2.extras import Json
from utils.text import clean_text


def ingest_file(file_path: str):
    """Ingesta un archivo DOCX: carga, chunkea, embebe e inserta en pgvector."""
    # 1. Cargar documento
    document = load_local_document(file_path)

    # 2. Chunking → lista de dicts
    chunks = chunk_document(document)

    if not chunks:
        print("No se generaron chunks")
        return

    # 3. Limpiar texto y preparar embeddings
    texts = []
    cleaned_chunks = []

    for chunk in chunks:
        raw_text = chunk.get("content", "")
        text = clean_text(raw_text)

        if not text.strip():
            continue

        texts.append(text)
        cleaned_chunks.append(chunk)

    if not texts:
        print("Todos los chunks estaban vacíos luego de limpiar")
        return

    # 4. Embeddings (MiniLM → 384)
    embeddings = embed_texts(texts)

    # 5. Insertar en pgvector
    conn = get_connection()
    cur = conn.cursor()

    for i, (chunk, chunk_text, embedding) in enumerate(
        zip(cleaned_chunks, texts, embeddings)
    ):
        metadata = {
            **chunk.get("metadata", {}),
            "source": file_path,
            "chunk_id": i,
            "file_type": "docx",
        }

        cur.execute(
            """
            INSERT INTO documents (content, embedding, metadata)
            VALUES (%s, %s, %s)
            """,
            (
                chunk_text,
                embedding,
                Json(metadata),
            )
        )

    conn.commit()
    cur.close()
    conn.close()

    print(f"Ingestados {len(texts)} chunks desde {file_path}")
