# Pipeline PDFs - Conexión con API OpenText

> **Estado:** ✅ Implementado (Enero 2026)

## Resumen

El pipeline ahora está configurado para:
1. **Descargar PDFs** desde OpenText Content Server vía API
2. **Generar embeddings** con OpenAI (1536 dimensiones)
3. **Almacenar** en la tabla `documents` de PostgreSQL/pgvector

## Archivos Principales

| Archivo | Descripción |
|---------|-------------|
| `pipeline_main.py` | Script principal - ejecuta el pipeline completo |
| `src/loaders/opentext_loader.py` | Descarga desde OpenText API |
| `src/embeddings/openai_embedder.py` | Embeddings OpenAI (1536 dims) |
| `src/pipeline/ingest_and_embed.py` | Ingesta con soporte API y local |

## Uso del Pipeline

### 1. Preparar archivo JSON de metadatos

```json
[
  {
    "DataID": 12345,
    "Name": "Manual de Usuario.pdf",
    "Description": "public",
    "ModifyDate": "2026-01-15T10:30:00Z"
  },
  {
    "DataID": 12346,
    "Name": "Informe Confidencial.pdf",
    "Description": "private",
    "ModifyDate": "2026-01-15T11:00:00Z"
  }
]
```

**Campos:**
- `DataID`: ID del documento en OpenText (requerido)
- `Name`: Nombre del archivo
- `Description`: `"public"` o `"private"` para control de acceso

### 2. Configurar variables de entorno

```bash
# OpenText Content Server
OTCS_BASE_URL=http://192.168.68.22/OTCS/cs.exe
OTCS_USERNAME=otadmin@otds.admin
OTCS_PASSWORD=inicio1234.
OTCS_TIMEOUT=60

# OpenAI
OPENAI_API_KEY=sk-proj-...

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_DB=rag
POSTGRES_USER=admin
POSTGRES_PASSWORD=1234
POSTGRES_PORT=5432
```

### 3. Ejecutar el pipeline

```bash
# Activar entorno virtual
source .venv/bin/activate  # o .venv\Scripts\activate en Windows

# Ejecutar pipeline
python pipeline_main.py metadata/documentos_pendientes.json
```

### 4. Verificar resultados

```bash
# Ver documentos insertados
docker exec -it platform-db psql -U admin -d rag -c "SELECT id, metadata->>'filename', metadata->>'description' FROM documents LIMIT 10;"

# Contar total de registros
docker exec -it platform-db psql -U admin -d rag -c "SELECT COUNT(*) FROM documents;"

# Ver ejecuciones del pipeline
docker exec -it platform-db psql -U admin -d rag -c "SELECT * FROM pipeline_runs;"
```

## Esquema de Base de Datos

El pipeline usa la tabla `documents` existente:

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Metadata JSON generada:**
```json
{
  "description": "public",
  "source": "opentext://12345",
  "filename": "Manual de Usuario.pdf",
  "data_id": 12345,
  "run_id": "run-20260119-123456-abc123",
  "chunk_index": 0,
  "chunk_type": "fixed_size",
  "num_pages": 5
}
```

## Flujo de Datos

```
┌─────────────────────────────────────────────────────────────┐
│  METADATA PIPELINE (SQL Server)                              │
│  - Extrae metadatos de SQL Server                            │
│  - Genera: documentos_pendientes.json                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  DATA PIPELINE (pipeline_main.py)                            │
│  1. Lee JSON con metadatos                                   │
│  2. Descarga PDFs desde OpenText API                         │
│  3. Extrae texto del PDF                                     │
│  4. Genera chunks (tamaño fijo)                              │
│  5. Crea embeddings OpenAI (1536 dims)                       │
│  6. Inserta en tabla documents (pgvector)                    │
└─────────────────────────────────────────────────────────────┘
```

## Modo Testing (Archivos Locales)

Para pruebas sin conexión a OpenText:

```python
from src.pipeline.ingest_and_embed import ingest_file

# Ingestar archivo local
ingest_file("data/raw/ejemplo.pdf", visibility="private")
```

## Notas Importantes

1. **Visibilidad**: Se mapea desde `Description` en el JSON:
   - `"public"` → documentos públicos (acceso general)
   - cualquier otro valor → `"private"` (acceso restringido)

2. **Embeddings**: Se usan embeddings OpenAI (`text-embedding-3-small`, 1536 dims) para compatibilidad con el esquema existente

3. **Idempotencia**: El pipeline NO verifica duplicados. Si se procesa el mismo documento dos veces, se insertarán registros duplicados

4. **Errores**: El pipeline continúa procesando aunque algún documento falle. Los errores se muestran en consola

## Archivos de Testing (Opcionales)

Estos archivos son para validación local y pueden eliminarse:
- `test_embeddings.py`
- `test_pipeline.py`
- `commands.sh`
- `src/loaders/local_loader.py` (mantener si se necesita modo local)

---

**Última actualización:** 19 de enero de 2026
