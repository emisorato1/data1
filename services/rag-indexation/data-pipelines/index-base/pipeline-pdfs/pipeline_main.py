#!/usr/bin/env python3
"""
Pipeline principal para procesar documentos PDF desde OpenText Content Server.

Lee un archivo JSON con metadatos de documentos y procesa cada uno:
1. Descarga desde OpenText API
2. Extrae texto del PDF
3. Genera chunks
4. Crea embeddings con OpenAI (1536 dims)
5. Guarda en PostgreSQL/pgvector

Soporta dos formatos de entrada:
- Formato Gold (de metadata-pipelines): {"metadata_run": {...}, "data": [...]}
- Formato simple: [{"DataID": ..., "Name": ..., "Description": ...}]

Uso:
    python pipeline_main.py metadata/documentos_pendientes.json
    python pipeline_main.py ../../../metadata-pipelines/data/3_gold/GLD_RUN-xxx.json
"""

import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Cargar variables de entorno desde .env.general (en la raíz del proyecto)
from dotenv import load_dotenv
# Imprime la ruta para depuración y confirmación
env_path = Path(__file__).parents[5] / ".env.general"
print(f"🔧 Cargando configuración desde: {env_path}")
load_dotenv(env_path)

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loaders.opentext_loader import load_from_opentext
from chunking.chunker import chunk_document
from embeddings.openai_embedder import get_embeddings
from db.postgres import get_connection
from utils.text import clean_text



def parse_metadata_file(metadata_file: Path) -> list[dict]:
    """
    Parsea el archivo de metadatos, soportando tanto formato simple como Gold.
    
    Args:
        metadata_file: Ruta al archivo JSON
    
    Returns:
        Lista de documentos en formato normalizado para process_document()
    """
    with open(metadata_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    # Detectar formato Gold (tiene "metadata_run" y "data")
    if isinstance(raw_data, dict) and "data" in raw_data and "metadata_run" in raw_data:
        print(f"📋 Formato detectado: Gold (metadata-pipelines)")
        print(f"   Run ID origen: {raw_data['metadata_run'].get('run_id', 'N/A')}")
        return transform_gold_to_pipeline_format(raw_data["data"])
    else:
        # Formato simple legacy
        print(f"📋 Formato detectado: Simple (legacy)")
        return raw_data


def transform_gold_to_pipeline_format(gold_data: list[dict]) -> list[dict]:
    """
    Transforma documentos Gold al formato esperado por process_document().
    
    Args:
        gold_data: Lista de documentos en formato Gold
    
    Returns:
        Lista de documentos en formato pipeline
    """
    result = []
    for doc in gold_data:
        # Extraer DataID del document_id (formato: "DOC-CS-{DataID}-v{version}")
        doc_id_parts = doc["document_id"].split("-")
        data_id = int(doc_id_parts[2]) if len(doc_id_parts) >= 3 else None
        
        # Determinar visibilidad basada en access_groups
        # P:-1 significa Public (con cualquier nivel de acceso)
        is_public = any(g.startswith("P:-1") for g in doc.get("access_groups", []))
        
        result.append({
            "DataID": data_id,
            "Name": doc["title"],
            "Description": "public" if is_public else "private",
            # Metadata extendida del Gold para enriquecer los chunks
            "_gold_metadata": {
                "document_id": doc["document_id"],
                "version": doc["version"],
                "classification": doc.get("classification", "Unclassified"),
                "access_groups": doc.get("access_groups", []),
                "effective_date": doc.get("effective_date"),
                "efs_path": doc.get("source_metadata", {}).get("efs_path"),
                "file_size": doc.get("source_metadata", {}).get("file_size"),
                "mime_type": doc.get("source_metadata", {}).get("mime_type"),
                "integrity_hash": doc.get("integrity_hash"),
            }
        })
    return result


def process_document(doc_metadata: dict, run_id: str) -> dict:
    """
    Procesa un documento individual: descarga, extrae, chunking, embeddings y guarda.
    
    Args:
        doc_metadata: Diccionario con metadatos del documento desde JSON
        run_id: ID de la ejecución del pipeline
    
    Returns:
        dict con estadísticas del procesamiento
    """
    data_id = doc_metadata.get("DataID")
    name = doc_metadata.get("Name", f"documento_{data_id}.pdf")
    visibility = "public" if doc_metadata.get("Description", "").lower() == "public" else "private"
    
    print(f"\n📄 Procesando documento DataID: {data_id} - {name}")
    
    stats = {
        "data_id": data_id,
        "name": name,
        "status": "pending",
        "chunks_count": 0,
        "chars_count": 0,
    }
    
    try:
        # 1. Descargar desde OpenText (Bronze)
        document = load_from_opentext(data_id, metadata={
            "name": name,
            "visibility": visibility,
            "description": visibility,
        })
        print(f"  ✓ Descargado: {len(document.content)} caracteres, {document.metadata.get('num_pages', '?')} páginas")
        
        if not document.content.strip():
            print(f"  ⚠️  PDF vacío o sin texto extraíble")
            stats["status"] = "empty"
            return stats
        
        # 2. Chunking (Silver → Gold)
        chunks = chunk_document(document)
        print(f"  ✓ Generados {len(chunks)} chunks")
        
        if not chunks:
            print(f"  ⚠️  No se generaron chunks")
            stats["status"] = "no_chunks"
            return stats
        
        # 3. Limpiar y preparar textos
        cleaned_chunks = []
        texts = []
        
        for chunk in chunks:
            raw_text = chunk.get("content", "")
            text = clean_text(raw_text)
            
            if text.strip():
                texts.append(text)
                cleaned_chunks.append(chunk)
        
        if not texts:
            print(f"  ⚠️  Todos los chunks estaban vacíos después de limpiar")
            stats["status"] = "empty_after_clean"
            return stats
        
        # 4. Generar embeddings con OpenAI (1536 dims)
        embeddings = get_embeddings(texts)
        print(f"  ✓ Embeddings generados: {len(embeddings)} x {len(embeddings[0])} dims")
        
        # 5. Insertar en PostgreSQL (tabla documents existente)
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            inserted_ids = []
            
            for i, (chunk, chunk_text, embedding) in enumerate(zip(cleaned_chunks, texts, embeddings)):
                # Construir metadata compatible con esquema existente
                metadata = {
                    "description": visibility,  # Campo clave para RAG: 'public' o 'private'
                    "source": f"opentext://{data_id}",
                    "filename": name,
                    "data_id": data_id,
                    "run_id": run_id,
                    "chunk_index": i,
                    "chunk_type": "fixed_size",
                    "num_pages": document.metadata.get("num_pages"),
                    **chunk.get("metadata", {})
                }
                
                # Incluir metadata Gold si está disponible (enriquece los chunks)
                gold_meta = doc_metadata.get("_gold_metadata")
                if gold_meta:
                    metadata["gold_document_id"] = gold_meta.get("document_id")
                    metadata["gold_version"] = gold_meta.get("version")
                    metadata["classification"] = gold_meta.get("classification")
                    metadata["access_groups"] = gold_meta.get("access_groups")
                    metadata["effective_date"] = gold_meta.get("effective_date")
                    metadata["integrity_hash"] = gold_meta.get("integrity_hash")
                
                cur.execute("""
                    INSERT INTO documents (content, embedding, metadata)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (
                    chunk_text,
                    embedding,
                    json.dumps(metadata),
                ))
                
                doc_id = cur.fetchone()[0]
                inserted_ids.append(doc_id)
            
            conn.commit()
            
            stats["status"] = "success"
            stats["chunks_count"] = len(inserted_ids)
            stats["chars_count"] = sum(len(t) for t in texts)
            stats["document_ids"] = inserted_ids
            
            print(f"  ✓ Guardados {len(inserted_ids)} registros en BD (IDs: {inserted_ids[0]}...{inserted_ids[-1]})")
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
            
    except Exception as e:
        stats["status"] = "error"
        stats["error"] = str(e)
        print(f"  ❌ Error: {e}")
    
    return stats


def run_pipeline(metadata_file: Path):
    """
    Ejecuta el pipeline completo leyendo metadatos desde un archivo JSON.
    
    Args:
        metadata_file: Ruta al archivo JSON con metadatos de documentos
    """
    print("=" * 60)
    print("🚀 Pipeline de Indexación PDF → OpenText → pgvector")
    print("=" * 60)
    print(f"📋 Archivo de metadatos: {metadata_file}")
    
    # Generar run_id único
    run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    # Registrar ejecución del pipeline
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO pipeline_runs (run_id, started_at, status)
            VALUES (%s, %s, %s)
        """, (run_id, datetime.now(timezone.utc), "running"))
        conn.commit()
        print(f"📝 Run ID: {run_id}")
    except Exception as e:
        print(f"⚠️  No se pudo registrar pipeline_run (tabla puede no existir): {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
    
    # Leer metadatos (soporta formato Gold y formato simple)
    metadata_list = parse_metadata_file(metadata_file)
    
    print(f"📊 Total de documentos a procesar: {len(metadata_list)}")
    
    # Procesar cada documento
    results = []
    success_count = 0
    error_count = 0
    total_chunks = 0
    
    for doc_metadata in metadata_list:
        stats = process_document(doc_metadata, run_id)
        results.append(stats)
        
        if stats["status"] == "success":
            success_count += 1
            total_chunks += stats.get("chunks_count", 0)
        else:
            error_count += 1
    
    # Actualizar estado final del pipeline
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        status = "completed" if error_count == 0 else "completed_with_errors"
        cur.execute("""
            UPDATE pipeline_runs
            SET status = %s,
                finished_at = %s,
                documents_count = %s,
                chunks_count = %s
            WHERE run_id = %s
        """, (status, datetime.now(timezone.utc), success_count, total_chunks, run_id))
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("✅ Pipeline completado")
    print("=" * 60)
    print(f"   - Exitosos:     {success_count}")
    print(f"   - Errores:      {error_count}")
    print(f"   - Total chunks: {total_chunks}")
    print(f"   - Run ID:       {run_id}")
    
    # Flush final de Langfuse
    try:
        flush_langfuse()
    except Exception as e:
        print(f"⚠️ Error flushing Langfuse: {e}")
    
    return {
        "run_id": run_id,
        "success_count": success_count,
        "error_count": error_count,
        "total_chunks": total_chunks,
        "results": results,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python pipeline_main.py <archivo_metadatos.json>")
        print("\nEjemplo:")
        print("  python pipeline_main.py metadata/documentos_pendientes.json")
        print("\nFormato del JSON:")
        print('  [{"DataID": 12345, "Name": "doc.pdf", "Description": "public"}, ...]')
        sys.exit(1)
    
    metadata_file = Path(sys.argv[1])
    
    if not metadata_file.exists():
        print(f"❌ Error: No se encuentra el archivo {metadata_file}")
        sys.exit(1)
    
    run_pipeline(metadata_file)
