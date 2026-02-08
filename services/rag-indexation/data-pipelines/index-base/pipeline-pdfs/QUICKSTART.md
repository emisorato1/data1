# 🚀 Quickstart - Pipeline PDFs

## Setup rápido

```bash
# 1. Ir al directorio
cd services/rag-indexation/data-pipelines/index-base/pipeline-pdfs

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -e .

# 4. Descargar datos NLTK (solo primera vez)
python -c "import nltk; nltk.download('punkt')"

# 5. Configurar credenciales
cp .env.example .env
# Editar .env si es necesario
```

## Test sin embeddings

```bash
# Probar conexión (requiere VPN)
python test_pipeline.py --test-connection

# Descargar y chunkear un documento
python test_pipeline.py 103830

# Guardar chunks en JSON
python test_pipeline.py 103830 --save
# → output/103830_chunks.json
```

## Estructura de salida

```json
{
  "data_id": 103830,
  "metadata": {"source": "opentext://103830", "num_pages": 5},
  "total_chars": 15000,
  "total_chunks": 25,
  "chunks": [
    {"content": "...", "metadata": {...}},
    ...
  ]
}

## Probar pipeline con un archivo de metadatos
python pipeline_main.py C:\ProyectosIT\DataOilers\enterprise-ai-platform\services\rag-indexation\metadata-pipelines\data\3_gold\GLD_RUN-20260120-101540-4E3B.json