# Enterprise AI Platform — RAG System

Sistema RAG (Retrieval-Augmented Generation) enterprise para un banco. Indexa documentos internos, genera embeddings con Gemini, y permite consultas conversacionales con control de acceso granular.

---

## Requisitos previos

- [uv](https://docs.astral.sh/uv/) (gestor de paquetes Python)
- [Docker](https://docs.docker.com/get-docker/) y Docker Compose v2+
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) (para autenticacion ADC con Vertex AI)
- `GEMINI_API_KEY` en `.env` para embeddings y generacion con Gemini

---

## Configuración de Docker nativo en WSL (Recomendado)

Si tienes problemas con Docker Desktop (errores de DNS, lentitud o conflictos con VPN), se recomienda instalar Docker directamente dentro de Ubuntu.

### 1. Activar Systemd en WSL (Paso Crítico)
Para que Docker arranque automáticamente y los servicios funcionen como en un servidor real, activa `systemd`. En la terminal de Ubuntu:

```bash
sudo bash -c 'cat <<EOF > /etc/wsl.conf
[boot]
systemd=true
[network]
generateResolvConf = false
EOF'
```

**Reinicia WSL desde una PowerShell de Windows (como Administrador) para aplicar cambios:**
```powershell
wsl --shutdown
```

### 2. Instalar el motor de Docker
Vuelve a entrar a la terminal de Ubuntu y ejecuta:

```bash
# Instalar repositorio oficial de Docker
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker Engine y Docker Compose V2
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Dar permisos a tu usuario (para no usar sudo siempre)
sudo usermod -aG docker $USER
```
*Nota: Cierra y abre la terminal de Ubuntu después de este paso para que los permisos se activen.*

### 3. Arreglar DNS (Opcional)
Si Docker no puede descargar imágenes tras el cambio de `wsl.conf`:
```bash
sudo rm /etc/resolv.conf
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf > /dev/null
```

---

## Interfaz Web y Gestión (Portainer)

Si extrañas la interfaz visual de Docker Desktop, instala Portainer. Se gestiona vía web y corre como un contenedor más.

### Levantar Portainer
```bash
docker run -d -p 9000:9000 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock portainer/portainer-ce
```
- **Acceso**: [http://localhost:9000](http://localhost:9000)

### Guía de recuperación (Si reiniciaste la PC)
1. Abre tu terminal de Ubuntu (**Docker arrancará solo** gracias a `systemd`).
2. Verifica el estado: `docker ps`.
3. Si los contenedores no subieron solos, inicia Portainer: `docker start portainer`.
4. Entra al proyecto y levanta los servicios:
   ```bash
   cd ~/projects/enterprise-ai-platform
   docker compose up -d
   ```

---

## Setup inicial

### 1. Clonar repositorio

```bash
git clone https://github.com/data-oilers/enterprise-ai-platform.git
cd enterprise-ai-platform
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env y completar los valores marcados con CHANGE_ME
```

Valores minimos requeridos en `.env`:

| Variable | Descripcion |
|----------|------------|
| `DB_PASSWORD` | Password de PostgreSQL |
| `REDIS_PASSWORD` | Password de Redis |
| `JWT_SECRET` | Secret para tokens JWT (min 32 chars) |
| `GEMINI_API_KEY` | API key de Google Gemini (necesaria para embeddings) |

### 3. Autenticacion con Google Cloud (ADC)

El proyecto usa **Vertex AI Discovery Engine** para reranking semantico. Este servicio requiere credenciales de Google Cloud (no basta con la `GEMINI_API_KEY`).

> **Politica de seguridad**: No se permite exportar service account keys (org policy: *Deny SA key creation*). Usamos **Application Default Credentials (ADC)** con OAuth del usuario.

**Paso unico por desarrollador** (el token se refresca automaticamente):

```bash
# Instalar gcloud CLI si no lo tienes: https://cloud.google.com/sdk/docs/install
gcloud auth application-default login --project=itmind-macro-ai-dev-0
```

Esto abre el navegador para autenticarse con tu cuenta Google y genera:

```
~/.config/gcloud/application_default_credentials.json
```

**Como funciona en cada entorno:**

| Entorno | Mecanismo | Detalle |
|---------|-----------|---------|
| Backend en host (`uvicorn`) | ADC automatico | `gcloud` ADC se detecta sin config adicional |
| Airflow en Docker (`--profile airflow`) | Volume mount | `docker-compose.yml` monta el archivo ADC en `/tmp/gcloud/adc.json` |
| GKE (produccion) | Workload Identity | K8s SA vinculado a GCP SA, sin keys |

**Verificar que funciona:**

```bash
# En el host — deberia mostrar tu cuenta y el proyecto
gcloud auth application-default print-access-token > /dev/null && echo "ADC OK"

# En el contenedor de Airflow — verificar que el archivo existe
docker compose exec airflow cat /tmp/gcloud/adc.json | head -3
```

> **Si no configuras ADC**: el reranker de Vertex AI falla y el sistema hace fallback automatico a RRF (Reciprocal Rank Fusion). La app funciona pero con calidad de reranking degradada.

### 4. Crear el entorno virtual

```bash
uv sync
```

### 5. Levantar servicios base

```bash
docker compose up -d
```

Esto levanta PostgreSQL 16 (con pgvector), Redis 7, el Backend FastAPI y el Frontend Next.js.

### 6. Correr migraciones

```bash
uv run alembic upgrade head
```

### 7. Cargar datos semilla

```bash
uv run python -m scripts.seed_data
```

El seed crea:
- **5 usuarios** (admin, analista, operador, auditor, tesorero) con IDs 1000-1004
- **5 documentos mock** (IDs 2000-2004) — registros en `documents` con paths ficticios (sin archivo fisico)
- **3 documentos de prueba** (IDs a partir de 3000) — el seed escanea `tests/fixtures/` automaticamente, registra cada `.pdf` y `.docx` valido en `documents`, y les asigna el path del container de Airflow. Si agregás nuevos archivos a la carpeta, el proximo `seed_data` los incluye
- **Permisos OpenText mock** (kuaf, dtreeacl, etc.) para el sistema de control de acceso

---

## Servicios Docker

El proyecto usa **Docker Compose profiles** para separar servicios base de herramientas opcionales. Esto permite que `docker compose up -d` levante lo esencial (PG + Redis + Backend + Frontend), sin consumir recursos extra en herramientas de desarrollo.

### Comandos por escenario

| Que necesitas | Comando |
|--------------|---------|
| Base (PG + Redis + Backend + Frontend) | `docker compose up -d` |
| Base + Airflow | `docker compose --profile airflow up -d` |
| Base + pgAdmin | `docker compose --profile pgadmin up -d` |
| Todo junto | `docker compose --profile airflow --profile pgadmin up -d` |

### Reconstruir con cambios

```bash
docker compose --profile airflow --profile pgadmin up -d --build
```

### Detener todo

```bash
docker compose --profile airflow --profile pgadmin down
```

### Detener solo un servicio opcional (sin tocar PG/Redis)

```bash
docker compose --profile airflow stop airflow
docker compose --profile pgadmin stop pgadmin
```

### Interfaz Visual (Portainer)

Si extrañas la interfaz de Docker Desktop, puedes levantar Portainer para gestionar todo vía web:

```bash
docker run -d -p 9000:9000 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock portainer/portainer-ce
```

- **Acceso**: http://localhost:9000
- **Uso**: Crea una contraseña inicial y selecciona "Get Started" para ver el entorno local.

---

## Comprobar el pipeline de indexacion con Airflow

Esta seccion explica paso a paso como ejecutar y verificar el DAG `rag_indexing`, que es el pipeline principal para indexar documentos en el sistema RAG.

### Contexto: como funcionan los documentos

El sistema tiene dos conceptos separados:

1. **Registro en la tabla `documents`** — metadatos del documento (nombre, area, quien lo subio). Se crean via el seed script. Los documentos mock (IDs 2000-2004) tienen paths ficticios. Los documentos de prueba (IDs 3000-3002) estan alineados con archivos reales.

2. **Archivo fisico** — el PDF/DOCX real que el pipeline necesita leer para extraer texto, generar chunks y embeddings. Los archivos de prueba estan en `tests/fixtures/` y se montan automaticamente dentro del container de Airflow en `/opt/airflow/test-data/`.

El seed crea 3 documentos listos para probar el pipeline de punta a punta:

### Paso 1: Levantar los servicios

```bash
docker compose --profile airflow up -d
```

La primera vez tarda ~90 segundos (instala dependencias pip + inicializa la DB de Airflow). Verificar que Airflow este healthy:

```bash
docker compose ps
```

Esperar a que `rag-airflow` muestre `healthy` en la columna STATUS.

### Paso 2: Correr migraciones y seed (si no lo hiciste antes)

```bash
uv run alembic upgrade head
uv run python -m scripts.seed_data
```

### Paso 3: Trigger del DAG

**Opcion A — Desde la UI de Airflow:**

1. Abrir http://localhost:8080
2. Login: `admin` / `admin`
3. Buscar el DAG `rag_indexing` en la lista
4. Click en el boton Play (triangulo) → **"Trigger DAG w/ config"**
5. En el campo JSON pegar:

```json
{"document_id": 3000, "file_path": "/opt/airflow/test-data/sample.pdf"}
```

6. Click en **"Trigger"**

**Opcion B — Desde la terminal:**

```bash
docker compose exec airflow airflow dags trigger rag_indexing \
  --conf '{"document_id": 3000, "file_path": "/opt/airflow/test-data/sample.pdf"}'
```

### Documentos de prueba disponibles

El seed escanea `tests/fixtures/` y registra automaticamente cada `.pdf` y `.docx` valido. Para ver los IDs asignados, correr el seed y buscar las lineas de output:

```bash
uv run python -m scripts.seed_data
# Output:
#   ID 3000: normas_higiene.pdf (671223 bytes) -> /opt/airflow/test-data/normas_higiene.pdf
#   ID 3001: sample.docx (1006 bytes) -> /opt/airflow/test-data/sample.docx
#   ID 3002: sample.pdf (548 bytes) -> /opt/airflow/test-data/sample.pdf
```

Para agregar nuevos documentos de prueba, simplemente copiar el archivo a `tests/fixtures/`:

```bash
cp /ruta/a/mi/documento.pdf tests/fixtures/
uv run python -m scripts.seed_data   # registra el nuevo archivo automaticamente
```

> Para re-ejecutar el pipeline sobre el mismo documento, primero limpiar los datos anteriores:
> ```sql
> DELETE FROM document_chunks WHERE document_id = 3000;
> DELETE FROM pipeline_runs WHERE document_id = 3000;
> ```

### Paso 4: Verificar la ejecucion

**Desde la UI**: en la vista del DAG `rag_indexing`, los 5 tasks deberian ponerse verdes uno a uno:

```
validate_file → load_and_chunk → generate_embeddings → store_in_pgvector → update_status
```

**Desde la terminal:**

```bash
docker compose exec airflow airflow dags list-runs rag_indexing
```

Esperar a ver `state: success`.

### Paso 5: Verificar los datos en la base de datos

Via psql:

```bash
# Pipeline runs — deberia tener status='completed'
docker compose exec db psql -U raguser -d rag_db -c \
  "SELECT id, document_id, status, started_at, finished_at FROM pipeline_runs ORDER BY started_at DESC LIMIT 5;"

# Chunks con embeddings
docker compose exec db psql -U raguser -d rag_db -c \
  "SELECT id, document_id, chunk_index, area, token_count, embedding IS NOT NULL AS has_embedding FROM document_chunks WHERE document_id = 3000;"
```

### Que significa cada task del DAG

| Task | Que hace | Criterio de exito |
|------|----------|-------------------|
| `validate_file` | Valida que el archivo exista y sea de tipo permitido (magic bytes). Crea registro en `pipeline_runs`. | Log: `validate_file_done` con mime_type y hash |
| `load_and_chunk` | Carga el documento (PDF/DOCX) y lo divide en chunks de ~1000 tokens. | Log: `document_chunked` con count de chunks |
| `generate_embeddings` | Genera embeddings 768-d con Gemini. Requiere `GEMINI_API_KEY` valida. | Log: `embeddings_generated` con dims=768 |
| `store_in_pgvector` | Almacena chunks + embeddings en `document_chunks` con halfvec(768). | Chunks en DB con `has_embedding = true` |
| `update_status` | Marca `pipeline_runs.status = 'completed'`. | `finished_at` tiene timestamp |

### Si algo falla

```bash
# Ver el estado del run
docker compose exec airflow airflow dags list-runs rag_indexing

# Ver logs del container (errores de arranque, pip install, etc.)
docker compose logs airflow --tail=100

# Verificar que GEMINI_API_KEY llego al container
docker compose exec airflow env | grep GEMINI
```

Si `generate_embeddings` falla con `API_KEY_INVALID`, verificar que `GEMINI_API_KEY` este definida en `.env` con una key valida.

---

## pgAdmin (consultas SQL via web)

### Levantar

```bash
docker compose --profile pgadmin up -d
```

### Credenciales

- **URL**: http://localhost:5050
- **Email**: `admin@rag.local`
- **Password**: `admin`

El servidor PostgreSQL (`RAG DB (local)`) aparece pre-registrado en el panel izquierdo. La primera vez pide la password de PostgreSQL (el valor de `DB_PASSWORD` en `.env`).

### Queries utiles para validar indexacion

```sql
-- Estado de las ejecuciones del pipeline
SELECT id, document_id, status, started_at, finished_at, error_message
FROM pipeline_runs ORDER BY started_at DESC;

-- Chunks almacenados con embeddings
SELECT id, document_id, chunk_index, area, token_count,
       length(content) AS content_len, embedding IS NOT NULL AS has_embedding
FROM document_chunks ORDER BY document_id, chunk_index;

-- Documentos con metadata de indexacion
SELECT id, filename, file_hash, metadata
FROM documents WHERE file_hash IS NOT NULL;

-- Verificar dimensiones del embedding (deberia ser 768)
SELECT id, document_id, array_length(embedding::real[], 1) AS dims
FROM document_chunks LIMIT 5;
```

---

## Tests

```bash
# Instalar dependencias de test
uv sync --extra test

# Ejecutar todos los tests
uv run pytest

# Solo tests unitarios
uv run pytest tests/unit/ -q
```

> Los tests de Airflow (`test_airflow_smoke.py`, `test_dag_indexing.py`) se skipean automaticamente si `apache-airflow` no esta instalado en el venv.



> Cómo ejecutar los tests de Helm
# Instalar helm-unittest
helm plugin install https://github.com/helm-unittest/helm-unittest
# Ejecutar tests
helm unittest helm/enterprise-ai-platform
# O usar el script completo (lint + template + unittest + kubeconform)
./scripts/validate-helm-chart.sh

---

## API

### Levantar (desarrollo local)

```bash
docker compose up -d                                    # PG + Redis + Backend + Frontend
uv run alembic upgrade head                             # migraciones
uv run python -m scripts.seed_data                      # datos semilla
uv run uvicorn src.infrastructure.api.main:app --reload # API en :8000 (alt: dev sin Docker)
```

### Imagen Docker de produccion

```bash
# Build
docker build -f docker/Dockerfile -t rag-api:latest .

# Run (requiere PG y Redis accesibles)
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host/db" \
  -e REDIS_URL="redis://:pass@host:6379" \
  -e JWT_SECRET="your-secret" \
  rag-api:latest
```

Caracteristicas de la imagen:
- Multi-stage build (builder + runtime)
- Base `python:3.12-slim`
- Usuario non-root `appuser` (UID 1000)
- Healthcheck integrado (`/health`)
- Sin secrets embebidos (todo via env vars)

### Despliegue en Kubernetes (Helm)

El proyecto incluye un Helm chart completo en `helm/enterprise-ai-platform/`.

```bash
# Instalar dependencias del chart (PostgreSQL + Redis de Bitnami)
cd helm/enterprise-ai-platform
helm dependency update

# Dry-run para validar
helm install --dry-run --debug rag-staging . -n rag-staging

# Deploy en staging
helm upgrade --install rag-staging . \
  -f values-staging.yaml \
  --set secrets.jwtSecret="$(openssl rand -base64 32)" \
  --set secrets.geminiApiKey="your-api-key" \
  --set postgresql.auth.password="$(openssl rand -base64 16)" \
  --set redis.auth.password="$(openssl rand -base64 16)" \
  -n rag-staging --create-namespace
```

Caracteristicas del chart:
- Deployment con liveness/readiness/startup probes
- HPA (autoscaling) y PDB (disruption budget)
- Security hardening: non-root, read-only fs, seccomp
- Sub-charts bitnami para PostgreSQL (pgvector) y Redis
- Ingress con TLS via cert-manager
- ServiceAccount con Workload Identity (GKE)

Ver `helm/enterprise-ai-platform/values.yaml` para todas las opciones configurables.

### Endpoints

| URL | Descripcion |
|-----|------------|
| http://localhost:8000/health | Health check |
| http://localhost:8000/docs | Documentacion Swagger |
| http://localhost:8000/redoc | Documentacion ReDoc |
