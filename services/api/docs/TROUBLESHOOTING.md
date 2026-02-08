# 🔧 Troubleshooting Guide - Enterprise AI Platform

> **Última actualización:** 2026-01-22  
> **Proyecto:** Enterprise AI Platform  
> **Versión:** 1.0

---

## 📋 Índice

1. [Errores de Docker y Contenedores](#1-errores-de-docker-y-contenedores)
2. [Errores de Base de Datos (PostgreSQL)](#2-errores-de-base-de-datos-postgresql)
3. [Errores de API Gateway (FastAPI)](#3-errores-de-api-gateway-fastapi)
4. [Errores de RAG Generation (LangGraph)](#4-errores-de-rag-generation-langgraph)
5. [Errores de RAG Indexation (Pipelines)](#5-errores-de-rag-indexation-pipelines)
6. [Errores de Frontend (Next.js)](#6-errores-de-frontend-nextjs)
7. [Errores de Autenticación](#7-errores-de-autenticación)
8. [Errores de Conectividad entre Servicios](#8-errores-de-conectividad-entre-servicios)
9. [Comandos de Diagnóstico Útiles](#9-comandos-de-diagnóstico-útiles)

---

## 1. Errores de Docker y Contenedores

### 1.1 Error: "could not translate host name 'db' to address"

**Síntoma:**
```
psycopg2.OperationalError: could not translate host name "db" to address: Name or service not known
```

**Causa:** El nombre del host en la configuración no coincide con el nombre del servicio en Docker Compose.

**Solución:**
1. Verificar el nombre del servicio en `docker-compose.yaml`:
   ```yaml
   services:
     postgres:  # Este es el nombre que debe usarse
       image: pgvector/pgvector:pg16
   ```
2. Actualizar variables de entorno para usar el nombre correcto:
   ```env
   DB_HOST=postgres  # No usar "db" o "localhost"
   ```
3. Reiniciar el servicio:
   ```bash
   docker-compose restart api-gateway
   ```

---

### 1.2 Error: Contenedor se reinicia continuamente

**Síntoma:** `docker ps` muestra estado `Restarting` repetidamente.

**Diagnóstico:**
```bash
docker logs <container_name> --tail 50
```

**Causas comunes:**
- Falta de variables de entorno requeridas
- Puerto ya en uso
- Dependencia no disponible

**Solución:**
```bash
# Verificar que el .env está completo
cat infra/dev/.env | grep -E "OPENAI|POSTGRES"

# Verificar puertos en uso
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Reiniciar limpio
docker-compose down
docker-compose up -d
```

---

### 1.3 Error: "image not found" al hacer build

**Síntoma:**
```
ERROR: Service 'api-gateway' failed to build
```

**Solución:**
```bash
# Reconstruir con --no-cache
docker-compose build --no-cache api-gateway
docker-compose up -d
```

---

## 2. Errores de Base de Datos (PostgreSQL)

### 2.1 Error: "column xxx does not exist"

**Síntoma:**
```
sqlalchemy.exc.ProgrammingError: column "status" does not exist
```

**Causa:** Desincronización entre el esquema SQL y los modelos ORM.

**Solución:**
```bash
# Opción 1: Eliminar volumen y recrear
docker-compose down -v
docker-compose up -d

# Opción 2: Ejecutar migración manualmente
docker exec -it eai-api-gateway uv run alembic upgrade head
```

---

### 2.2 Error: "relation xxx already exists"

**Síntoma:**
```
psycopg2.errors.DuplicateTable: relation "tenants" already exists
```

**Causa:** Se ejecutó el script de inicialización en una BD que ya tenía las tablas.

**Solución:**
```bash
# Si es desarrollo, limpiar y recrear
docker-compose down -v
docker-compose up -d

# Si necesitas preservar datos, ignorar y verificar
docker exec eai-postgres psql -U eai_user -d eai_platform -c "\dt"
```

---

### 2.3 Error: "password authentication failed"

**Síntoma:**
```
FATAL: password authentication failed for user "eai_user"
```

**Causa:** Credenciales incorrectas o volumen con datos de contraseña anterior.

**Solución:**
```bash
# Verificar credenciales en .env
cat infra/dev/.env | grep POSTGRES

# Si cambiaste credenciales, eliminar volumen
docker volume rm eai-postgres-data
docker-compose up -d
```

---

### 2.4 Error: Extensión pgvector no existe

**Síntoma:**
```
ERROR: extension "vector" is not available
```

**Solución:** Asegurarse de usar la imagen correcta:
```yaml
# docker-compose.yaml
postgres:
  image: pgvector/pgvector:pg16  # NO usar postgres:16
```

---

## 3. Errores de API Gateway (FastAPI)

### 3.1 Error: CORS "405 Method Not Allowed" en OPTIONS

**Síntoma:** El frontend recibe error 405 al hacer requests.

**Causa:** Middleware CORS no configurado correctamente.

**Solución:** Verificar `main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 3.2 Error: "502 Bad Gateway" al enviar mensajes

**Síntoma:** El chat devuelve error 502.

**Causa:** API Gateway no puede comunicarse con el servicio RAG.

**Solución:**
```bash
# 1. Verificar que agentic-rag está corriendo
docker-compose ps

# 2. Ver logs del RAG
docker-compose logs agentic-rag --tail=50

# 3. Probar conectividad desde API Gateway
docker-compose exec api-gateway python -c "import httpx; print(httpx.get('http://agentic-rag:2024/info').text)"
```

---

### 3.3 Error: "No module named 'app'"

**Síntoma:** Error al iniciar el contenedor del API.

**Solución:** Verificar el Dockerfile:
```dockerfile
WORKDIR /app
COPY . .
# El comando debe ser relativo a /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

---

## 4. Errores de RAG Generation (LangGraph)

### 4.1 Error: "OPENAI_API_KEY no configurada"

**Síntoma:**
```
openai.AuthenticationError: No API key provided
```

**Solución:**
```bash
# Verificar .env
cat infra/dev/.env | grep OPENAI

# Debe tener:
OPENAI_API_KEY=sk-proj-xxx...

# Reiniciar servicio
docker-compose restart agentic-rag
```

---

### 4.2 Error: "No se pudo obtener respuesta del agente"

**Síntoma:** El chat siempre devuelve este mensaje.

**Diagnóstico:**
```bash
# Ver logs del RAG
docker-compose logs agentic-rag --tail=100

# Probar endpoint directamente
curl -X POST http://localhost:2024/runs \
  -H "Content-Type: application/json" \
  -d '{"assistant_id": "rag_generation", "input": {"message": "test"}}'
```

**Causas posibles:**
1. API Key de OpenAI inválida o expirada
2. Límite de rate de OpenAI alcanzado
3. Error en la búsqueda vectorial (BD vacía)

**Solución:**
```bash
# Verificar documentos en BD
docker exec eai-postgres psql -U eai_user -d eai_platform -c "SELECT count(*) FROM documents;"

# Si está vacío, ejecutar seed
python infra/dev/scripts/seed_test_data.py
```

---

### 4.3 Error: Conexión a PostgreSQL desde RAG

**Síntoma:**
```
Connection refused to postgres:5432
```

**Solución:**
1. Verificar nombre del host en variables:
   ```env
   PGVECTOR_HOST=postgres  # Nombre del servicio en Docker
   ```
2. Si ejecutas localmente (fuera de Docker):
   ```env
   PGVECTOR_HOST=localhost
   PGVECTOR_PORT=55432  # Puerto mapeado
   ```

---

### 4.4 Error: Docker "host.docker.internal" no resuelve

**Síntoma:** Contenedor no puede conectar al host.

**Solución:** Agregar flag al ejecutar:
```bash
docker run -d \
  --add-host=host.docker.internal:host-gateway \
  --name rag-generation \
  rag-generation:latest
```

---

## 5. Errores de RAG Indexation (Pipelines)

### 5.1 Error: "ModuleNotFoundError: No module named 'config'"

**Síntoma:** Error al ejecutar el pipeline con uv.

**Causa:** Faltan archivos `__init__.py` en los directorios.

**Solución:**
```bash
# Crear archivos __init__.py necesarios
touch config/__init__.py
touch src/__init__.py
touch src/common/__init__.py
touch src/pipeline/__init__.py

# Actualizar pyproject.toml
[tool.uv]
package = false
```

**Comando correcto:**
```powershell
cd services/rag-indexation/metadata-pipelines
uv run python -m src.main
```

---

### 5.2 Error: "No se encuentra el nombre del origen de datos" (ODBC)

**Síntoma:**
```
[IM002] No se encuentra el nombre del origen de datos y no se especificó ningún controlador predeterminado
```

**Causa:** Falta archivo `.env` con credenciales de SQL Server.

**Solución:**
1. Crear `config/.env`:
   ```env
   SERVER=tu_servidor
   DATABASE=tu_base_datos
   USER=tu_usuario
   PASSWORD=tu_contraseña
   DB_DRIVER=ODBC Driver 17 for SQL Server
   ```

2. Verificar drivers ODBC instalados:
   ```powershell
   Get-OdbcDriver | Where-Object {$_.Name -like "*SQL Server*"} | Select-Object Name
   ```

---

### 5.3 Error: Formatos JSON incompatibles entre pipelines

**Síntoma:** El pipeline de PDFs no acepta el JSON del metadata-pipeline.

**Causa:** Formatos diferentes:
- metadata-pipelines genera: `{metadata_run, data: [{document_id, ...}]}`
- pipeline-pdfs esperaba: `[{DataID, Name, ...}]`

**Solución:** El `pipeline_main.py` ya incluye detección automática de formato Gold y transformación. Usar:
```powershell
cd services/rag-indexation/data-pipelines/index-base/pipeline-pdfs
uv run python pipeline_main.py ../../../metadata-pipelines/data/3_gold/GLD_RUN-<timestamp>.json
```

---

### 5.4 Error: Documentos eliminados o huérfanos aparecen

**Síntoma:** El pipeline trae documentos que no deberían estar.

**Solución:** Verificar filtros en las queries SQL:
```sql
-- En count_changes.sql y extract_metadata.sql
AND (d.Deleted IS NULL OR d.Deleted = 0)
AND d.Name NOT LIKE '@[%'
AND EXISTS (
    SELECT 1 FROM DTreeAncestors anc
    INNER JOIN DTreeCore folder ON anc.AncestorID = folder.DataID
    WHERE anc.DataID = d.DataID
    AND folder.Name = 'PRUEBA-DATA-OILERS'
)
```

Para reiniciar checkpoint:
```powershell
Remove-Item data/checkpoint.json
uv run python -m src.main
```

---

## 6. Errores de Frontend (Next.js)

### 6.1 Error: Frontend no carga

**Diagnóstico:**
```bash
docker-compose logs frontend
```

**Solución:**
```bash
docker-compose up -d --build frontend
```

---

### 6.2 Error: TypeScript "reader is possibly undefined"

**Síntoma:**
```
error TS2532: Object is possibly 'undefined'.
```

**Ubicación:** `lib/chatApi.ts` línea ~236

**Solución:** Agregar verificación null:
```typescript
const reader = response.body?.getReader();
if (!reader) {
  throw new Error('Response body is null');
}
```

---

### 6.3 Error: "Parsing ecmascript source code failed"

**Síntoma:** Error de build en Docker.

**Causa:** Error de sintaxis en TypeScript.

**Solución:** Revisar líneas indicadas en el error, usualmente paréntesis o llaves faltantes.

---

## 7. Errores de Autenticación

### 7.1 Error: "No se encontraron usuarios"

**Síntoma:** Login falla indicando que no existen usuarios.

**Solución:**
```bash
# Verificar usuarios en BD
docker exec eai-postgres psql -U eai_user -d eai_platform -c "SELECT email, role_id FROM users;"

# Si no hay usuarios, ejecutar script
python infra/dev/scripts/create_test_users.py
```

**Usuarios por defecto:**
| Email | Password | Rol |
|-------|----------|-----|
| public@demo.local | password123 | public |
| private@demo.local | password123 | private |
| admin@demo.local | password123 | admin |

---

### 7.2 Error: Token JWT expirado

**Síntoma:** Requests autenticados devuelven 401 después de un tiempo.

**Solución:**
1. Hacer logout/login nuevamente
2. O aumentar `JWT_EXPIRES_MINUTES` en `.env`

---

## 8. Errores de Conectividad entre Servicios

### 8.1 Mapeo de nombres de host

| Desde | Hacia | Host a usar |
|-------|-------|-------------|
| Host (Windows) | Contenedor | `localhost` |
| Contenedor | Contenedor | Nombre del servicio (`postgres`, `agentic-rag`) |
| Contenedor | Host | `host.docker.internal` |

### 8.2 Mapeo de puertos

| Servicio | Puerto interno | Puerto externo (host) |
|----------|----------------|----------------------|
| PostgreSQL | 5432 | 55432 |
| API Gateway | 8000 | 8000 |
| RAG Generation | 2024 | 2024 |
| Frontend | 3000 | 3000 |
| pgAdmin | 80 | 5050 |

---

## 9. Comandos de Diagnóstico Útiles

### Estado de servicios
```bash
docker-compose ps
docker-compose logs -f  # Logs en tiempo real
```

### Verificar conectividad
```bash
# API Gateway
curl http://localhost:8000/api/v1/health

# RAG Generation  
curl http://localhost:2024/info

# PostgreSQL
docker exec eai-postgres psql -U eai_user -d eai_platform -c "SELECT 1;"
```

### Verificar datos
```bash
# Documentos
docker exec eai-postgres psql -U eai_user -d eai_platform -c "SELECT count(*) FROM documents;"

# Usuarios
docker exec eai-postgres psql -U eai_user -d eai_platform -c "SELECT email, role_id FROM users;"

# Tenants
docker exec eai-postgres psql -U eai_user -d eai_platform -c "SELECT * FROM tenants;"
```

### Reset completo
```bash
cd infra/dev
docker-compose down -v  # Elimina volúmenes
docker-compose up -d    # Recrea todo
python scripts/create_test_users.py
python scripts/seed_test_data.py
```

### Reconstruir servicio específico
```bash
docker-compose up -d --build api-gateway
docker-compose up -d --build agentic-rag
docker-compose up -d --build frontend
```

### Acceso a shell de contenedor
```bash
docker exec -it eai-api-gateway /bin/sh
docker exec -it eai-postgres psql -U eai_user -d eai_platform
```

---

## 📝 Notas Importantes

1. **Nombre del contenedor PostgreSQL:** `eai-postgres` (no `postgres`)
2. **Base de datos:** `eai_platform` (no `rag_db` ni `enterpriseaigatewaydev`)
3. **Usuario por defecto:** `eai_user`
4. **Puerto PostgreSQL externo:** `55432` (no `5432`)
5. **DEFAULT_TENANT_ID:** `00000000-0000-0000-0000-000000000001`
6. **Archivos Gold se generan en:** `metadata-pipelines/data/3_gold/`
7. **Incluir extensión `.json`** al pasar archivos a `pipeline_main.py`

---

*Documentación de troubleshooting - Enterprise AI Platform © 2026*
