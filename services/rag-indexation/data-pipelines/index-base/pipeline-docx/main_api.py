#!/usr/bin/env python3
"""
Ingesta de DOCX desde OpenText Content Server.

Uso:
    # Un documento
    python main_api.py 103830
    
    # Múltiples documentos
    python main_api.py 103830 103831 103832
    
    # Desde archivo JSON con metadata
    python main_api.py --from-json metadata.json
"""

import sys
import json
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
sys.path.append(str(SRC_DIR))

from loaders.opentext_loader import load_from_opentext, test_connection
from chunking.chunker import chunk_document
from embeddings.minilm_embedder import embed_texts
from db.postgres import get_connection
from psycopg2.extras import Json
from utils.text import clean_text


def ingest_from_opentext(data_id: int, extra_metadata: dict = None):
    """Ingesta un documento desde Content Server."""
    print(f"\n📥 Descargando DataID={data_id}...")
    
    # 1. Descargar y parsear
    document = load_from_opentext(data_id, extra_metadata)
    print(f"   ✓ {len(document.content)} caracteres, {document.metadata.get('num_paragraphs', '?')} párrafos")
    
    # 2. Chunking
    chunks = chunk_document(document)
    if not chunks:
        print("   ⚠ No se generaron chunks")
        return 0
    
    # 3. Limpiar y filtrar
    texts = []
    cleaned_chunks = []
    for chunk in chunks:
        text = clean_text(chunk.get("content", ""))
        if text.strip():
            texts.append(text)
            cleaned_chunks.append(chunk)
    
    if not texts:
        print("   ⚠ Chunks vacíos después de limpiar")
        return 0
    
    # 4. Embeddings
    print(f"   🔢 Generando {len(texts)} embeddings...")
    embeddings = embed_texts(texts)
    
    # 5. Insertar en pgvector
    conn = get_connection()
    cur = conn.cursor()
    
    for i, (chunk, chunk_text, embedding) in enumerate(
        zip(cleaned_chunks, texts, embeddings)
    ):
        metadata = {
            **chunk.get("metadata", {}),
            **document.metadata,
            "chunk_id": i,
        }
        
        cur.execute(
            """
            INSERT INTO documents (content, embedding, metadata)
            VALUES (%s, %s, %s)
            """,
            (chunk_text, embedding, Json(metadata))
        )
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"   ✅ {len(texts)} chunks insertados")
    return len(texts)


def main():
    parser = argparse.ArgumentParser(
        description="Ingesta DOCX desde OpenText Content Server"
    )
    parser.add_argument(
        "data_ids",
        nargs="*",
        type=int,
        help="DataIDs de documentos a ingestar"
    )
    parser.add_argument(
        "--from-json",
        type=str,
        help="Archivo JSON con metadata (debe tener campo 'DataID')"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Solo probar conexión"
    )
    
    args = parser.parse_args()
    
    # Test de conexión
    if args.test:
        print("Probando conexión a Content Server...")
        if test_connection():
            print("✅ Conexión OK")
            return 0
        else:
            print("❌ Conexión fallida")
            return 1
    
    # Cargar desde JSON
    if args.from_json:
        with open(args.from_json) as f:
            data = json.load(f)
        
        # Soporta objeto único o array
        items = data if isinstance(data, list) else [data]
        
        total = 0
        for item in items:
            data_id = item.get("DataID")
            if not data_id:
                print(f"⚠ Saltando item sin DataID: {item}")
                continue
            total += ingest_from_opentext(data_id, item)
        
        print(f"\n{'='*40}")
        print(f"Total: {total} chunks de {len(items)} documentos")
        return 0
    
    # Ingestar por DataIDs
    if args.data_ids:
        total = 0
        for data_id in args.data_ids:
            total += ingest_from_opentext(data_id)
        
        print(f"\n{'='*40}")
        print(f"Total: {total} chunks de {len(args.data_ids)} documentos")
        return 0
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
