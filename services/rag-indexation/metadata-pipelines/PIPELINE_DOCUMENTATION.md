# Metadata Pipeline - Documentación Técnica

> **Versión**: 1.0.0  
> **Última Actualización**: 2026-01-16  
> **Autor**: Data Engineering Team  
> **Sistema Origen**: OpenText Content Server (EFS)

---

## Índice

1. [Visión General](#visión-general)
2. [Arquitectura Medallion](#arquitectura-medallion)
3. [Transformaciones por Capa](#transformaciones-por-capa)
4. [Contratos de Datos](#contratos-de-datos)
5. [Sistema de Checkpoint](#sistema-de-checkpoint)
6. [Flujo de Ejecución](#flujo-de-ejecución)

---

## Visión General

Este pipeline implementa una arquitectura **Medallion (Bronze → Silver → Gold)** para la extracción, transformación y preparación de metadatos desde OpenText Content Server hacia un sistema RAG (Retrieval-Augmented Generation).

### Objetivos del Pipeline

| Objetivo | Descripción |
|----------|-------------|
| **Extracción Incremental** | Solo procesa documentos modificados desde el último checkpoint |
| **Seguridad Híbrida** | Preserva tokens de acceso para filtrado en runtime |
| **Trazabilidad** | Cada registro mantiene lineage completo entre capas |
| **Idempotencia** | Re-ejecuciones producen resultados consistentes |

---

## Arquitectura Medallion

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         METADATA PIPELINE - MEDALLION                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │              │    │              │    │              │                  │
│  │   🥉 BRONZE  │───▶│   🥈 SILVER  │───▶│   🥇 GOLD    │                  │
│  │              │    │              │    │              │                  │
│  │  Raw Data    │    │  Normalized  │    │  Contracted  │                  │
│  │  562 rows    │    │  60 docs     │    │  60 docs     │                  │
│  │              │    │              │    │              │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│        │                   │                   │                           │
│        ▼                   ▼                   ▼                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │ BRZ_*.json   │    │ SLV_*.json   │    │ GLD_*.json   │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Ratio de Transformación

| Métrica | Bronze | Silver | Gold |
|---------|--------|--------|------|
| **Registros** | 562 | 60 | 60 |
| **Granularidad** | Fila por permiso | Documento único | Documento contratado |
| **Ratio** | 1:1 (raw) | 9.4:1 (agregación) | 1:1 (contrato) |

---

## Transformaciones por Capa

### 🥉 Capa Bronze - Extracción Cruda

**Propósito**: Espejo fiel del sistema origen sin transformaciones.

**Query de Extracción** (`extract_metadata.sql`):
```sql
SELECT 
    d.DataID, 
    d.VersionNum AS VersionNumber,
    d.Name, 
    v.DataSize AS FileSize,
    d.ModifyDate,
    p.providerData + '.dat' AS EFSRelativePath,
    v.MimeType,
    acl.RightID,
    acl.See AS AccessLevel,
    -- Clasificación derivada
    CASE WHEN acl.RightID = -1 THEN 'Public' ELSE 'Private' END AS PrivacyStatus,
    CASE 
        WHEN k.Type = 0 THEN 'User'
        WHEN k.Type = 1 THEN 'Group'
        WHEN acl.RightID = -1 THEN 'Public'
        WHEN acl.RightID = -2 THEN 'Admin'
        ELSE 'Special/System'
    END AS SubjectType
FROM DTreeCore d
INNER JOIN DVersData v ON d.DataID = v.DocID AND d.VersionNum = v.Version
INNER JOIN ProviderData p ON v.ProviderId = p.providerID
LEFT JOIN DTreeACL acl ON d.DataID = acl.DataID AND acl.See >= 1
LEFT JOIN KUAF k ON acl.RightID = k.ID
WHERE d.SubType = 144 
AND d.ModifyDate > :start_date
```

**Transformaciones**: Ninguna (raw data)

**Output Schema**:
```json
{
    "DataID": 7896,
    "VersionNumber": 1,
    "Name": "documento.pdf",
    "FileSize": 90165,
    "ModifyDate": "2025-01-20T17:15:15",
    "EFSRelativePath": "7897.dat",
    "MimeType": "application/pdf",
    "RightID": 1000,
    "AccessLevel": 4,
    "PrivacyStatus": "Private",
    "SubjectType": "User"
}
```

> ⚠️ **Multiplicidad**: Un documento con 5 permisos genera 5 filas en Bronze.

---

### 🥈 Capa Silver - Normalización y Seguridad

**Propósito**: Estandarización, filtrado y consolidación de permisos.

**Transformaciones Aplicadas**:

| # | Transformación | Descripción |
|---|----------------|-------------|
| 1 | **Filtrado por MimeType** | Solo `application/pdf` y `.docx` |
| 2 | **Agrupación por DataID** | Colapsa N filas → 1 documento |
| 3 | **Tokenización de Permisos** | ACLs → formato `T:ID:N` |
| 4 | **Normalización de Fechas** | DateTime → ISO 8601 |
| 5 | **Agregación de Lineage** | Trazabilidad a Bronze |

**Lógica de Tokenización de Seguridad**:
```python
# Formato: "{SubjectType[0]}:{RightID}:{AccessLevel}"
# Ejemplos:
#   U:1000:4  → User ID 1000, nivel acceso 4
#   G:2001:4  → Group ID 2001, nivel acceso 4
#   P:-1:2    → Public, nivel acceso 2
#   A:-2:4    → Admin, nivel acceso 4
```

**Diagrama de Transformación**:
```
BRONZE (562 rows)                    SILVER (60 docs)
┌─────────────────────┐              ┌─────────────────────────────┐
│ DataID: 7896        │              │ source_id: "CS-7896"        │
│ RightID: 1000       │──┐           │ name: "documento.pdf"       │
│ SubjectType: "User" │  │           │ security_tokens: [          │
├─────────────────────┤  │           │   "U:1000:4",               │
│ DataID: 7896        │  ├──────────▶│   "P:-1:2",                 │
│ RightID: -1         │  │           │   "A:-2:4",                 │
│ SubjectType:"Public"│  │           │   "G:2001:4"                │
├─────────────────────┤  │           │ ]                           │
│ DataID: 7896        │  │           │ lineage: {                  │
│ RightID: -2         │──┘           │   run_id: "...",            │
│ SubjectType:"Admin" │              │   previous_stage: "BRZ_..." │
└─────────────────────┘              │ }                           │
                                     └─────────────────────────────┘
```

**Output Schema**:
```json
{
    "source_id": "CS-7896",
    "source_version": 1,
    "name": "eSignDefaultTemplate.pdf",
    "file_size_bytes": 90165,
    "modify_date_iso": "2025-01-20T17:15:15",
    "efs_relative_path": "7897.dat",
    "mime_type": "application/pdf",
    "security_tokens": ["U:1000:4", "S:999:2", "P:-1:2", "A:-2:4", "G:2001:4"],
    "lineage": {
        "run_id": "RUN-20260116-130555-2723",
        "stage": "silver",
        "previous_stage_id": "BRZ_RUN-20260116-130555-2723"
    }
}
```

---

### 🥇 Capa Gold - Contrato de Datos Final

**Propósito**: Estructura lista para consumo por el sistema RAG.

**Transformaciones Aplicadas**:

| # | Transformación | Descripción |
|---|----------------|-------------|
| 1 | **Generación de Document ID** | Formato: `DOC-CS-{id}-v{version}` |
| 2 | **Renombrado de Campos** | Alineación a contrato RAG |
| 3 | **Clasificación Default** | `"Unclassified"` (extensible) |
| 4 | **Hash de Integridad** | SHA-256 por registro |
| 5 | **Encapsulación de Metadata** | Origen en `source_metadata` |

**Mapeo Silver → Gold**:

| Campo Silver | Campo Gold | Transformación |
|--------------|------------|----------------|
| `source_id` | `document_id` | `"DOC-CS-{id}-v{version}"` |
| `name` | `title` | Directo |
| - | `classification` | `"Unclassified"` (default) |
| `security_tokens` | `access_groups` | Directo |
| `source_version` | `version` | Cast a string |
| `modify_date_iso` | `effective_date` | Directo |
| `efs_relative_path` | `source_metadata.efs_path` | Encapsulado |
| `file_size_bytes` | `source_metadata.file_size` | Encapsulado |
| `mime_type` | `source_metadata.mime_type` | Encapsulado |
| - | `integrity_hash` | SHA-256 del doc |

**Output Schema (Contrato RAG)**:
```json
{
    "document_id": "DOC-CS-7896-v1",
    "title": "eSignDefaultTemplate.pdf",
    "classification": "Unclassified",
    "access_groups": ["U:1000:4", "S:999:2", "P:-1:2", "A:-2:4", "G:2001:4"],
    "version": "1",
    "effective_date": "2025-01-20T17:15:15",
    "source_metadata": {
        "system": "Content Server",
        "efs_path": "7897.dat",
        "file_size": 90165,
        "mime_type": "application/pdf"
    },
    "integrity_hash": "a1b2c3d4e5..."
}
```

---

## Contratos de Datos

### Metadata de Ejecución (Por Capa)

Cada archivo de salida incluye un header `metadata_run`:

```json
{
    "metadata_run": {
        "run_id": "RUN-20260116-130555-2723",
        "stage": "bronze|silver|gold",
        "timestamp_*": "2026-01-16T13:05:57",
        "record_count|input_records|output_documents": 60,
        "checksum_*": "sha256..."
    },
    "raw_data|data": [...]
}
```

### Checksums de Integridad

| Capa | Campo | Calcula Sobre |
|------|-------|---------------|
| Bronze | `checksum_data` | Array completo de `raw_data` |
| Silver | `checksum_silver` | Array de documentos procesados |
| Gold | `integrity_hash_total` | Array de documentos finales |
| Gold | `integrity_hash` (por doc) | Cada documento individual |

---

## Sistema de Checkpoint

El pipeline utiliza un archivo de estado persistente para control de ejecución incremental.

### Archivo `data/checkpoint.json`

```json
{
    "last_successful_run": "RUN-20260116-130555-2723",
    "last_checkpoint_date": "2026-01-16T11:49:44",
    "documents_processed": 60,
    "timestamp_saved": "2026-01-16T13:05:57"
}
```

### Flujo de Decisión

```
                    ┌─────────────────────┐
                    │ Pipeline Iniciado   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ ¿Existe checkpoint? │
                    └──────────┬──────────┘
                      No ──────┼────── Sí
                               │       │
               ┌───────────────▼───┐   │
               │ Usar default_date │   │
               │ (2024-01-01)      │   │
               └───────────────────┘   │
                               │       │
                    ┌──────────▼───────▼──┐
                    │ Query: COUNT cambios│
                    │ desde checkpoint    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ ¿Hay cambios > 0?   │
                    └──────────┬──────────┘
                      No ──────┼────── Sí
                       │       │
            ┌──────────▼───┐   │
            │ [SKIP]       │   │
            │ Pipeline     │   │
            │ omitido      │   │
            └──────────────┘   │
                               │
                    ┌──────────▼──────────┐
                    │ Ejecutar B→S→G      │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Guardar checkpoint  │
                    │ con max(ModifyDate) │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ [DONE] Pipeline     │
                    │ completado          │
                    └─────────────────────┘
```

---

## Flujo de Ejecución

### Logs de Ejemplo

```
[CHECKPOINT] Estado cargado | Último run: RUN-20260116-130555-2723
[INIT] Pipeline incremental iniciado | RunID: RUN-20260116-130616-3E0A
[INIT] Checkpoint de extracción: 2026-01-16T11:49:44
[DETECT] 60 documento(s) pendiente(s) de procesamiento
[BRONZE] Iniciando extracción | Desde: 2026-01-16T11:49:44
[BRONZE] Completado | Records: 562 | Output: data\1_bronze\BRZ_*.json
[SILVER] Iniciando transformación y agrupamiento
[SILVER] Completado | Input: 562 rows -> Output: 60 docs
[GOLD] Iniciando validación de contrato final
[GOLD] Completado | Documentos finales: 60 | Output: data\3_gold\GLD_*.json
[CHECKPOINT] Estado guardado | RunID: RUN-20260116-* | Docs: 60
[DONE] Pipeline completado exitosamente | RunID: RUN-20260116-*
```

### Estructura de Directorios

```
metadata-pipelines/
├── data/
│   ├── checkpoint.json           # Estado del pipeline
│   ├── 1_bronze/
│   │   └── BRZ_RUN-*.json       # Raw data
│   ├── 2_silver/
│   │   └── SLV_RUN-*.json       # Normalized data
│   └── 3_gold/
│       └── GLD_RUN-*.json       # Contracted data
├── src/
│   ├── main.py                   # Orquestador principal
│   ├── common/
│   │   ├── checkpoint_manager.py # Gestión de estado
│   │   ├── database_manager.py   # Conexión SQL Server
│   │   ├── logger.py             # Logging centralizado
│   │   └── utils.py              # Utilidades (checksum, etc)
│   └── pipeline/
│       ├── metadata_pipeline.py  # Lógica B→S→G
│       └── queries/
│           ├── extract_metadata.sql
│           └── count_changes.sql
└── config/
    └── config.py                 # Configuración DB y pipeline
```

---

## Consideraciones de Performance

| Aspecto | Implementación |
|---------|----------------|
| **Extracción** | Query parametrizada con índice en `ModifyDate` |
| **Memoria** | Procesamiento en streaming por lotes |
| **I/O** | Persistencia JSON con indentación mínima en producción |
| **Idempotencia** | Checkpoint basado en `max(ModifyDate)` procesado |

---

## Extensibilidad

### Agregar Nuevo MimeType
```python
# metadata_pipeline.py - run_silver()
allowed_mimetypes = [
    'application/pdf', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain'  # ← Agregar aquí
]
```

### Reset Manual
```powershell
# Eliminar checkpoint para reprocesar desde fecha default
Remove-Item "data\checkpoint.json"
```

### Forzar Fecha Específica
```json
// Editar data/checkpoint.json
{
    "last_checkpoint_date": "2025-01-01T00:00:00"
}
```

---

> **Nota**: Esta documentación corresponde a la versión actual del pipeline. Para cambios en contratos de datos, actualizar este documento en conjunto con el código.
