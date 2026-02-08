#!/usr/bin/env python3
"""
Test de descarga y chunking DOCX (SIN embeddings ni BD).

Uso:
    # Probar conexión
    python test_pipeline.py --test-connection
    
    # Descargar y chunkear un documento
    python test_pipeline.py 103830
    
    # Desde archivo JSON con metadata
    python test_pipeline.py --from-json metadata.json
    
    # Guardar chunks en JSON
    python test_pipeline.py 103830 --save
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


def test_document(data_id: int, extra_metadata: dict = None, save: bool = False):
    """Descarga y chunkea un documento, mostrando resultados."""
    print(f"\n{'='*60}")
    print(f"📥 DOCUMENTO DataID={data_id}")
    print(f"{'='*60}")
    
    # 1. Descargar y parsear
    try:
        document = load_from_opentext(data_id, extra_metadata)
        print(f"✅ Descargado: {len(document.content)} caracteres")
        print(f"   Párrafos: {document.metadata.get('num_paragraphs', 'N/A')}")
    except Exception as e:
        print(f"❌ Error descargando: {e}")
        return None
    
    # 2. Preview del contenido
    print(f"\n📄 PREVIEW (primeros 500 chars):")
    print("-" * 40)
    print(document.content[:500])
    print("-" * 40)
    
    # 3. Chunking
    print(f"\n🔪 CHUNKING...")
    try:
        chunks = chunk_document(document)
        print(f"✅ {len(chunks)} chunks generados")
    except Exception as e:
        print(f"❌ Error en chunking: {e}")
        return None
    
    # 4. Mostrar chunks
    print(f"\n📦 CHUNKS:")
    for i, chunk in enumerate(chunks[:5]):  # Solo primeros 5
        content = chunk.get("content", "")
        preview = content[:100] + "..." if len(content) > 100 else content
        print(f"\n  [{i}] ({len(content)} chars)")
        print(f"      {preview}")
    
    if len(chunks) > 5:
        print(f"\n  ... y {len(chunks) - 5} chunks más")
    
    # 5. Stats
    sizes = [len(c.get("content", "")) for c in chunks]
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"   Total chunks: {len(chunks)}")
    print(f"   Tamaño mínimo: {min(sizes)} chars")
    print(f"   Tamaño máximo: {max(sizes)} chars")
    print(f"   Tamaño promedio: {sum(sizes)//len(sizes)} chars")
    
    # 6. Guardar si se pide
    if save:
        output_dir = BASE_DIR / "output"
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"{data_id}_chunks.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "data_id": data_id,
                "metadata": document.metadata,
                "total_chars": len(document.content),
                "total_chunks": len(chunks),
                "chunks": chunks
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Guardado en: {output_file}")
    
    return chunks


def main():
    parser = argparse.ArgumentParser(
        description="Test de descarga y chunking DOCX (sin embeddings)"
    )
    parser.add_argument(
        "data_ids",
        nargs="*",
        type=int,
        help="DataIDs de documentos a probar"
    )
    parser.add_argument(
        "--from-json",
        type=str,
        help="Archivo JSON con metadata"
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Solo probar conexión a Content Server"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Guardar chunks en output/{data_id}_chunks.json"
    )
    
    args = parser.parse_args()
    
    # Test de conexión
    if args.test_connection:
        print("🔌 Probando conexión a Content Server...")
        if test_connection():
            print("✅ Conexión OK")
            return 0
        else:
            print("❌ Conexión fallida")
            return 1
    
    # Desde JSON
    if args.from_json:
        with open(args.from_json) as f:
            data = json.load(f)
        
        items = data if isinstance(data, list) else [data]
        
        for item in items:
            data_id = item.get("DataID")
            if data_id:
                test_document(data_id, item, args.save)
        return 0
    
    # Por DataIDs
    if args.data_ids:
        for data_id in args.data_ids:
            test_document(data_id, save=args.save)
        return 0
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
