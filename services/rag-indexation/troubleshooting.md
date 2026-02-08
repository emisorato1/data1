# Troubleshooting - RAG Indexation Pipelines

> **Fecha:** 2026-01-20  
> **Proyecto:** Enterprise AI Platform - RAG Indexation

---

## Resumen de la sesión

Se configuraron y solucionaron problemas de los dos pipelines de indexación RAG:
1. **metadata-pipelines**: Extrae metadata de SQL Server (OpenText Content Server)
2. **pipeline-pdfs**: Procesa PDFs, genera embeddings y guarda en pgvector

---

## 1. Consolidación de archivos SQL

### Problema
Múltiples archivos `.sql` para inicializar la base de datos PostgreSQL.

### Archivos encontrados
| Archivo | Propósito |
|---------|-----------|
| `01-init-extensions.sql` | Extensiones + tablas auth/usuarios/mensajes/documentos |
| `02-init-pipeline.sql` | Tablas del pipeline de indexación |
| `init-unified.sql` | **Archivo unificado** (ya existente) |

### Solución
El archivo `init-unified.sql` ya contenía todo. Para ejecutarlo manualmente:

```bash
# Desde dentro del contenedor PostgreSQL
psql -U eai_user -d eai_platform -f /docker-entrypoint-initdb.d/init-unified.sql

# Desde PowerShell (fuera del contenedor)
docker exec -i eai-postgres psql -U eai_user -d eai_platform -f /docker-entrypoint-initdb.d/init-unified.sql
```

---

## 2. Configuración de metadata-pipelines

### Problema
Error `ModuleNotFoundError: No module named 'config'` al ejecutar con uv.

### Causa
Faltaban archivos `__init__.py` en los directorios de paquetes.

### Solución
Creados los siguientes `__init__.py`:
- `config/__init__.py`
- `src/__init__.py`
- `src/common/__init__.py`
- `src/pipeline/__init__.py`

Actualizado `pyproject.toml`:
```toml
[tool.uv]
package = false
```

### Comando correcto
```powershell
cd services/rag-indexation/metadata-pipelines
uv run python -m src.main
```

---

## 3. Conexión a SQL Server (ODBC)

### Problema
Error `[IM002] No se encuentra el nombre del origen de datos y no se especificó ningún controlador predeterminado`

### Causa
Faltaba el archivo `.env` con credenciales de conexión.

### Solución
Crear archivo `config/.env` con:
```env
SERVER=tu_servidor
DATABASE=tu_base_datos
USER=tu_usuario
PASSWORD=tu_contraseña
DB_DRIVER=ODBC Driver 17 for SQL Server
```

> **Nota:** El archivo debe estar en `config/.env`, no en la raíz del proyecto.

### Verificar drivers ODBC instalados
```powershell
Get-OdbcDriver | Where-Object {$_.Name -like "*SQL Server*"} | Select-Object Name
```

---

## 4. Configuración de pipeline-pdfs

### Problema
Error `ModuleNotFoundError: No module named 'openai'`

### Solución
Usar uv para instalar dependencias automáticamente:
```powershell
cd services/rag-indexation/data-pipelines/index-base/pipeline-pdfs
uv sync  # Instala dependencias
uv run python pipeline_main.py <archivo.json>
```

---

## 5. Integración entre pipelines

### Problema
Los dos pipelines usaban formatos JSON diferentes:
- **metadata-pipelines** genera formato Gold: `{metadata_run, data: [{document_id, title, access_groups, ...}]}`
- **pipeline-pdfs** esperaba formato simple: `[{DataID, Name, Description}]`

### Soluciones implementadas

#### 5.1 Filtro de carpeta PRUEBA-DATA-OILERS
Modificados los archivos SQL para filtrar solo documentos de esa carpeta:

**`count_changes.sql`** y **`extract_metadata.sql`**:
```sql
-- Filtro: Solo documentos dentro de la carpeta PRUEBA-DATA-OILERS
AND EXISTS (
    SELECT 1 FROM DTreeAncestors anc
    INNER JOIN DTreeCore folder ON anc.AncestorID = folder.DataID
    WHERE anc.DataID = d.DataID
    AND folder.Name = 'PRUEBA-DATA-OILERS'
)
```

#### 5.2 Soporte automático de formato Gold
Agregadas funciones a `pipeline_main.py`:
- `parse_metadata_file()`: Detecta automáticamente el formato
- `transform_gold_to_pipeline_format()`: Transforma Gold → formato pipeline

Los chunks ahora incluyen metadata enriquecida:
- `gold_document_id`
- `classification`
- `access_groups`
- `effective_date`
- `integrity_hash`

---

## 6. Flujo de ejecución completo

```powershell
# 1. Levantar servicios Docker
cd infra/dev
docker compose up -d

# 2. Ejecutar metadata-pipelines (extrae metadata de SQL Server)
cd services/rag-indexation/metadata-pipelines
uv run python -m src.main

# 3. Ejecutar pipeline-pdfs con el archivo Gold generado
cd ../data-pipelines/index-base/pipeline-pdfs
uv run python pipeline_main.py ../../../metadata-pipelines/data/3_gold/GLD_RUN-<timestamp>.json
```

---

## 7. Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `metadata-pipelines/pyproject.toml` | Configuración para uv |
| `metadata-pipelines/config/__init__.py` | Nuevo archivo |
| `metadata-pipelines/src/__init__.py` | Nuevo archivo |
| `metadata-pipelines/src/common/__init__.py` | Nuevo archivo |
| `metadata-pipelines/src/pipeline/__init__.py` | Nuevo archivo |
| `metadata-pipelines/src/pipeline/queries/count_changes.sql` | Filtro PRUEBA-DATA-OILERS |
| `metadata-pipelines/src/pipeline/queries/extract_metadata.sql` | Filtro PRUEBA-DATA-OILERS |
| `pipeline-pdfs/pipeline_main.py` | Soporte formato Gold automático |

---

## 8. Filtrado de documentos eliminados y huérfanos

### Problema
El pipeline traía documentos eliminados y archivos con nombres GUID (ej: `@[9EF13C49-3AAB-47B6-AE3C-ED5EA1A22A1B]`) que son huérfanos o temporales en OpenText.

### Solución
Agregados nuevos filtros a las queries SQL:

```sql
-- Filtro: Solo documentos NO eliminados
AND (d.Deleted IS NULL OR d.Deleted = 0)
-- Filtro: Excluir archivos con nombres GUID (huérfanos/temporales)
AND d.Name NOT LIKE '@[%'
```

### Resultado
Antes: 13 documentos (incluyendo eliminados)
Después: 1 documento (solo el vigente en PRUEBA-DATA-OILERS)

### Para reiniciar el checkpoint
```powershell
Remove-Item data/checkpoint.json
uv run python -m src.main
```

---

## 9. Notas adicionales

- El contenedor PostgreSQL se llama `eai-postgres` (no `postgres`)
- La base de datos es `eai_platform` (no `rag_db`)
- Usuario por defecto: `eai_user`
- Los archivos Gold se generan en: `metadata-pipelines/data/3_gold/`
- El checkpoint se guarda en: `metadata-pipelines/data/checkpoint.json`
- **Importante**: Al ejecutar `pipeline_main.py`, incluir la extensión `.json` en el nombre del archivo
