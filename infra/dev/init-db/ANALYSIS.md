# 📊 Análisis Comparativo de Tablas SQL - Enterprise AI Platform

## Estado de la Base de Datos (Post Docker-Compose)

### Tablas Creadas ✅
| Tabla | Estado | Fuente | Propósito |
|-------|--------|--------|-----------|
| `tenants` | ✅ Existe | 01-init-extensions.sql | Multi-tenancy |
| `roles` | ✅ Existe | 01-init-extensions.sql | Gestión de roles |
| `users` | ✅ Existe | 01-init-extensions.sql | Autenticación |
| `refresh_tokens` | ✅ Existe | 01-init-extensions.sql | JWT tokens |
| `messages` | ✅ Existe | 01-init-extensions.sql | Chat/conversaciones |
| `message_sources` | ✅ Existe | 01-init-extensions.sql | Citas en respuestas |
| `documents` | ✅ Existe | 01-init-extensions.sql | Vector store RAG |
| `pipeline_runs` | ✅ Existe | init.sql (pipeline) | Tracking indexación |
| `document_pipeline_metadata` | ✅ Existe | init.sql (pipeline) | Metadata medallion |

### Extensiones Instaladas ✅
- `uuid-ossp` - Generación de UUIDs
- `vector` - Soporte para embeddings y búsqueda vectorial
- `plpgsql` - Lenguaje procedural (built-in)

## Comparación de Archivos Originales

### Archivo 1: `01-init-extensions.sql`
**Ubicación**: `infra/dev/init-db/01-init-extensions.sql`

**Contenido**:
- ✅ Extensiones (uuid-ossp, vector)
- ✅ Esquema de autenticación (tenants, roles, users, refresh_tokens)
- ✅ Esquema de mensajes (messages, message_sources)
- ✅ Vector store (documents)
- ✅ Todos los índices necesarios
- ✅ Datos iniciales (default tenant, roles básicos)

### Archivo 2: `init.sql` (Pipeline)
**Ubicación**: `services/rag-indexation/data-pipelines/index-base/pipeline-pdfs/init.sql`

**Contenido**:
- ✅ Tabla `pipeline_runs` - tracking de ejecuciones
- ✅ Tabla `document_pipeline_metadata` - metadata medallion (bronze/silver/gold)
- ✅ Índices específicos del pipeline
- ✅ Comentarios y documentación

## Análisis de Diferencias

### Complementariedad
| Aspecto | 01-init-extensions.sql | init.sql (pipeline) | Unificado |
|---------|------------------------|-------------------|-----------|
| Extensiones | ✅ Define | ❌ Asume | ✅ Define |
| Auth/Users | ✅ Define | ❌ No incluye | ✅ Define |
| Vector Store | ✅ Define | ❌ Asume | ✅ Define |
| Pipeline Tables | ❌ No incluye | ✅ Define | ✅ Define |
| Índices Auth | ✅ Define | ❌ No incluye | ✅ Define |
| Índices Pipeline | ❌ No incluye | ✅ Define | ✅ Define |
| Datos Iniciales | ✅ Define | ❌ No incluye | ✅ Define |

**Conclusión**: Los archivos son **complementarios**. El archivo 1 es base, el archivo 2 es extensión.

## 📄 Archivos Generados

### 1. `02-init-pipeline.sql` (NUEVO)
Archivo intermedio con solo las tablas del pipeline.
- Se ejecuta DESPUÉS de `01-init-extensions.sql`
- Independiente y modular
- Usado para inicialización incremental

### 2. `init-unified.sql` (NUEVO - RECOMENDADO)
Archivo único consolidado que contiene TODO.

**Ventajas**:
✅ Punto único de verdad para inicialización BD  
✅ Garantiza orden correcto de creación  
✅ Facilita mantenimiento  
✅ Documentación completa integrada  
✅ Compatible con ambos servicios (API + Pipeline)

## 📋 Recomendaciones

### Opción A: Mantener Separado (Actual)
```
infra/dev/init-db/
  ├── 01-init-extensions.sql      (Auth + Chat + Vector Store)
  └── 02-init-pipeline.sql        (Pipeline Tables)
```
**Usado**: Docker Compose ejecuta `init-db.d/*.sql` en orden alfabético

### Opción B: Usar Unificado (Recomendado)
```
infra/dev/init-db/
  ├── init-unified.sql            (TODO en un solo archivo)
  └── (opcional) versiones anteriores como referencia
```

**Cambio en docker-compose.yaml**:
```yaml
volumes:
  - ./init-db/init-unified.sql:/docker-entrypoint-initdb.d/01-init.sql:ro
```

## 🔄 Estructura Medallion (Bronze/Silver/Gold)

El pipeline implementa el patrón medallion en `document_pipeline_metadata`:

- **Bronze**: Ingesta raw (checksum, timestamp)
- **Silver**: Procesamiento de texto (char count, word count, tool usado)
- **Gold**: Chunking y embeddings (count, status)

Cada etapa es rastreable e independiente.

## ✅ Verificación en Base de Datos

### Tablas actuales (9 total):
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

Resultado:
- document_pipeline_metadata
- documents
- message_sources
- messages
- pipeline_runs
- refresh_tokens
- roles
- tenants
- users

## 🚀 Próximos Pasos

1. **Revisar** si necesitas mantener modularidad o unificar
2. **Elegir** entre Opción A (actual) u Opción B (recomendada)
3. **Aplicar** la estructura elegida
4. **Documentar** en README.md del equipo
