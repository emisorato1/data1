"""
Módulo de ingesta y embeddings para documentos.

Soporta dos modos de operación:
- API: Descarga desde OpenText Content Server
- Local: Carga desde archivos locales (para testing)

Uso:
    # Modo API (producción)
    from pipeline.ingest_and_embed import ingest_from_opentext
    ingest_from_opentext(data_id=12345, visibility="private")
    
    # Modo local (testing)
    from pipeline.ingest_and_embed import ingest_file
    ingest_file("path/to/file.pdf")
"""

from loaders.opentext_loader import load_from_opentext
from loaders.local_loader import load_local_document
from chunking.chunker import chunk_document
from embeddings.openai_embedder import get_embeddings
from db.postgres import get_connection
from utils.text import clean_text
import json


def _process_and_store(document, source_info: dict) -> int:
    """
    Procesa un documento y lo guarda en pgvector.
    
    Args:
        document: Objeto Document con content y metadata
        source_info: Info adicional para metadata (source, visibility, etc)
    
    Returns:
        Número de chunks insertados
    """
    # 1. Chunking
    chunks = chunk_document(document)
    
    if not chunks:
        print("No se generaron chunks")
        return 0
    
    # 2. Limpiar texto y preparar embeddings
    texts = []
    cleaned_chunks = []
    
    for chunk in chunks:
        raw_text = chunk.get("content", "")
        text = clean_text(raw_text)
        
        if text.strip():
            texts.append(text)
            cleaned_chunks.append(chunk)
    
    if not texts:
        print("Todos los chunks estaban vacíos después de limpiar")
        return 0
    
    # 3. Embeddings con OpenAI (1536 dims)
    embeddings = get_embeddings(texts)
    
    # 4. Insertar en pgvector
    conn = get_connection()
    cur = conn.cursor()
    
    inserted_count = 0
    
    try:
        for i, (chunk, chunk_text, embedding) in enumerate(
            zip(cleaned_chunks, texts, embeddings)
        ):
            # Construir metadata compatible con esquema existente
            metadata = {
                "description": source_info.get("visibility", "private"),
                "source": source_info.get("source", "unknown"),
                "chunk_index": i,
                "chunk_type": "fixed_size",
                **document.metadata,
                **chunk.get("metadata", {}),
            }
            
            cur.execute("""
                INSERT INTO documents (content, embedding, metadata)
                VALUES (%s, %s, %s)
            """, (
                chunk_text,
                embedding,
                json.dumps(metadata),
            ))
            inserted_count += 1
        
        conn.commit()
    finally:
        cur.close()
        conn.close()
    
    print(f"Ingestados {inserted_count} chunks desde {source_info.get('source', 'unknown')}")
    return inserted_count


def ingest_from_opentext(data_id: int, visibility: str = "private", metadata: dict = None) -> int:
    """
    Ingesta un documento desde OpenText Content Server.
    
    Args:
        data_id: ID del documento en OpenText
        visibility: 'public' o 'private'
        metadata: Metadata adicional opcional
    
    Returns:
        Número de chunks insertados
    """
    # Preparar metadata
    doc_metadata = {
        "visibility": visibility,
        "description": visibility,
        **(metadata or {}),
    }
    
    # Descargar y parsear
    document = load_from_opentext(data_id, metadata=doc_metadata)
    
    if not document.content.strip():
        print(f"Documento {data_id} está vacío o sin texto extraíble")
        return 0
    
    # Procesar y guardar
    source_info = {
        "source": f"opentext://{data_id}",
        "visibility": visibility,
    }
    
    return _process_and_store(document, source_info)


def ingest_file(file_path: str, visibility: str = "private") -> int:
    """
    Ingesta un documento desde archivo local (para testing).
    
    Args:
        file_path: Ruta al archivo
        visibility: 'public' o 'private'
    
    Returns:
        Número de chunks insertados
    """
    # Cargar documento local
    document = load_local_document(file_path)
    
    if not document.content.strip():
        print(f"Archivo {file_path} está vacío o sin texto extraíble")
        return 0
    
    # Procesar y guardar
    source_info = {
        "source": file_path,
        "visibility": visibility,
        "file_type": file_path.split(".")[-1],
    }
    
    return _process_and_store(document, source_info)
