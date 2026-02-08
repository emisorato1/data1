#!/usr/bin/env python3
"""Test de embeddings con archivos locales y guardado en PostgreSQL."""
import sys
import hashlib
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "src"))

from loaders.local_loader import load_local_document
from chunking.chunker import chunk_document
from embeddings.openai_embedder import get_embeddings
from db.postgres import get_connection

# Archivos de prueba
DATA_TEST_DIR = Path("/Users/agustin/Documents/desarrollos/enterprise-ai-platform/services/rag-indexation/data-test")


def generate_run_id():
    """Genera un ID único para esta ejecución."""
    return f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def save_to_postgres(run_id, filename, doc, chunks, embeddings):
    """Guarda documento y chunks en PostgreSQL."""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # 1. Crear pipeline_run
        cur.execute("""
            INSERT INTO pipeline_runs (run_id, started_at, status)
            VALUES (%s, %s, 'running')
            ON CONFLICT (run_id) DO NOTHING
        """, (run_id, datetime.now()))
        
        # 2. Crear documento con metadata de stages
        file_hash = hashlib.sha256(doc.content.encode()).hexdigest()
        cur.execute("""
            INSERT INTO documents (
                run_id, data_id, name, mime_type, file_size, visibility,
                bronze_timestamp, bronze_checksum, bronze_status,
                silver_timestamp, silver_chars, silver_words, silver_tool, silver_status,
                gold_timestamp, gold_chunks_count, gold_status
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s
            ) RETURNING id
        """, (
            run_id,
            0,  # data_id (local test)
            filename,
            'application/pdf',
            len(doc.content),
            'public',
            # Bronze
            datetime.now(), file_hash, 'success',
            # Silver
            datetime.now(), len(doc.content), len(doc.content.split()), 'pdfplumber', 'success',
            # Gold
            datetime.now(), len(chunks), 'success'
        ))
        
        document_id = cur.fetchone()[0]
        
        # 3. Guardar chunks con embeddings
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_hash = hashlib.sha256(chunk['content'].encode()).hexdigest()
            cur.execute("""
                INSERT INTO chunks (document_id, chunk_index, content, content_hash, char_count, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                document_id,
                i,
                chunk['content'],
                chunk_hash,
                len(chunk['content']),
                embedding
            ))
        
        # 4. Actualizar pipeline_run
        cur.execute("""
            UPDATE pipeline_runs 
            SET status = 'success', finished_at = %s, documents_count = 1, chunks_count = %s
            WHERE run_id = %s
        """, (datetime.now(), len(chunks), run_id))
        
        conn.commit()
        print(f"   ✅ Guardado en PostgreSQL (document_id: {document_id})")
        
    except Exception as e:
        conn.rollback()
        print(f"   ❌ Error guardando: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def test_file(filepath, run_id):
    """Procesa un archivo: carga, chunkea, embeddings, guarda."""
    filename = Path(filepath).name
    print(f"\n{'='*50}")
    print(f"Archivo: {filename}")
    print('='*50)
    
    # 1. Cargar (Bronze)
    print("\n1. [BRONZE] Cargando documento...")
    doc = load_local_document(filepath)
    print(f"   Contenido: {len(doc.content)} caracteres")
    
    # 2. Extraer y chunkear (Silver + Gold)
    print("\n2. [SILVER] Extrayendo texto...")
    print(f"   Palabras: {len(doc.content.split())}")
    
    print("\n3. [GOLD] Chunkeando...")
    chunks = chunk_document(doc)
    print(f"   Chunks generados: {len(chunks)}")
    
    # 3. Embeddings
    print("\n4. Generando embeddings...")
    texts = [c["content"] for c in chunks]
    embeddings = get_embeddings(texts)
    print(f"   Embeddings: {len(embeddings)} vectores de {len(embeddings[0])} dimensiones")
    
    # 4. Guardar en PostgreSQL
    print("\n5. Guardando en PostgreSQL...")
    save_to_postgres(run_id, filename, doc, chunks, embeddings)
    
    return len(chunks)


def main():
    print("🚀 Test de Pipeline: Carga → Chunks → Embeddings → PostgreSQL")
    
    run_id = generate_run_id()
    print(f"\nRun ID: {run_id}")
    
    # Buscar PDFs en data-test
    pdf_files = list(DATA_TEST_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No hay PDFs en {DATA_TEST_DIR}")
        return
    
    total_chunks = 0
    for pdf_path in pdf_files:
        try:
            total_chunks += test_file(str(pdf_path), run_id)
        except Exception as e:
            print(f"❌ Error procesando {pdf_path.name}: {e}")
    
    print(f"\n{'='*50}")
    print(f"✅ Completado! Total chunks: {total_chunks}")
    print(f"   Run ID: {run_id}")
    print(f"\nVerificar en PostgreSQL:")
    print(f"   docker exec -it rag-postgres psql -U admin -d rag -c 'SELECT * FROM documents;'")


if __name__ == "__main__":
    main()