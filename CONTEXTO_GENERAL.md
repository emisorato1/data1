# Contexto General: Enterprise AI Platform en GKE

## 🎯 Objetivos

### 1. Airflow RAG Indexing Pipeline
Hacer funcionar el DAG `rag_indexing` de Airflow para indexar documentos en el sistema RAG Enterprise AI Platform. Actualmente el chat responde "No tengo información suficiente" porque la tabla `document_chunks` está vacía (0 embeddings).

### 2. Backend/Frontend Deployment
Mantener actualizados los deployments de Backend (FastAPI) y Frontend (Next.js) en GKE con los últimos cambios del código (Sprint 6: configuraciones centralizadas, tests, mejoras de consistencia).

## 🏗️ Arquitectura

- **Proyecto GCP**: `itmind-macro-ai-dev-0`
- **Cluster GKE**: `macro-ai-dev-gke` (zona: `us-east1-b`)
- **Namespace Airflow**: `airflow`
- **Namespace Enterprise AI**: `enterprise-ai`
- **Framework**: FAST v52 (Terraform + GKE + Cloud SQL)
- **Airflow**: v3.1.7 (Helm chart 1.19.0)
- **Base de datos**: Cloud SQL PostgreSQL (`macro-ai-dev-db`)
  - Database `airflow`: metadatos de Airflow
  - Database `enterprise_ai`: documentos, chunks, embeddings

## 🔴 Problemas Identificados y Resueltos

### 1. Timeout de Celery (RESUELTO)
**Síntoma**: `module 'redis' has no attribute 'client'`  
**Causa**: `AIRFLOW__CELERY__OPERATION_TIMEOUT` default 1 segundo era insuficiente para la primera conexión lazy a Redis/Celery.  
**Solución**: Configurado a `10.0` en template `02-values.yaml.tpl` línea 91-92.

### 2. DATABASE_URL Incorrecto (RESUELTO)
**Síntoma**: Errores de autenticación al conectar DAGs a `enterprise_ai` database.  
**Causa**: Usuario incorrecto (`enterprise_ai` en vez de `enterprise_ai_admin`).  
**Solución**: Corregido en template línea 99-100:
```
postgresql://enterprise_ai_admin:rR%3CXZ4%7DsWDVW9AY5Pr%7BCTV9ef5jk%29K%3Dy@127.0.0.1:5432/enterprise_ai
```
Password real (URL-decoded): `rR<XZ4}sWDVW9AY5Pr{CTV9ef5jk)K=y`

### 3. Tiktoken Download Timeout (RESUELTO)
**Síntoma**: Task `load_and_chunk` fallaba al intentar descargar `cl100k_base.tiktoken` desde Azure Blob Storage (`openaipublic.blob.core.windows.net`).  
**Causa**: GKE pods no tienen acceso a Azure Blob Storage (egress filtrado). `AdaptiveChunker` usa tiktoken para token counting.  
**Solución**: Pre-cachear encoding en imagen Docker custom.

## 🐳 Imágenes Docker Custom

Ubicación de código: `/Users/agustin/Documents/desarrollos/enterprise-ai-platform/airflow/`

### Evolución de Versiones

| Versión | Descripción | Estado |
|---------|-------------|--------|
| `v1.0.0` | Dependencias básicas (psycopg, PyMuPDF, python-docx, langchain-text-splitters) | ❌ Insuficiente |
| `v1.1.1` | + Código fuente enterprise-ai-platform instalado como package | ❌ Falla tiktoken |
| `v1.1.2` | + Pre-cache tiktoken `cl100k_base` | ✅ Construida y pusheada |
| `v1.1.3` | Versión actual en template (con últimos cambios del repo) | ⏳ **PENDIENTE** |

### Build y Push

```bash
cd /Users/agustin/Documents/desarrollos/enterprise-ai-platform/airflow
./scripts/build-and-push.sh
```

Imagen resultante: `gcr.io/itmind-macro-ai-dev-0/airflow-custom:3.1.7-v1.1.3`

## 📁 Estructura de Archivos Relevantes

### Enterprise AI Platform Repo
```
/Users/agustin/Documents/desarrollos/enterprise-ai-platform/
├── airflow/
│   ├── Dockerfile                    # Imagen custom con tiktoken pre-cache
│   ├── requirements.txt              # Dependencias Python
│   ├── .dockerignore                 # Optimización de build context
│   └── scripts/build-and-push.sh     # Script de automatización
├── dags/indexing/rag_indexing.py     # DAG principal (5 tasks)
├── src/infrastructure/rag/
│   ├── chunking/adaptive_chunker.py  # Usa tiktoken.get_encoding('cl100k_base')
│   ├── embeddings/gemini_embeddings.py
│   └── loaders/                      # PDF/DOCX loaders
└── tests/data/demo/
    └── 001 RRHH - Administración.pdf # Documento de prueba (128KB, 18 páginas)
```

### Infrastructure Repo
```
/Users/agustin/Documents/desarrollos/itmind-infrastructure/
└── fast/tenants/macro/deploy-dev-airflow/
    ├── 00-namespace.yaml
    ├── 01-secrets.sh
    ├── 02-values.yaml.tpl            # ⚠️ TEMPLATE (editar SOLO este)
    ├── 03-deploy.sh                  # Regenera airflow-values.yaml
    ├── 04-network-policy.yaml
    └── airflow-values.yaml           # ❌ NO EDITAR (generado por 03-deploy.sh)
```

**⚠️ IMPORTANTE**: `airflow-values.yaml` se regenera automáticamente desde `02-values.yaml.tpl`. Cualquier edición manual se perderá. Para cambios permanentes, editar el template.

## 🚀 Estado Actual del Deployment

### Helm Release
- **Release**: `airflow`
- **Revisión**: 12
- **Estado**: `deployed`
- **Chart**: `apache-airflow/airflow:1.19.0`

### Pods Actuales (namespace: airflow)
```
airflow-api-server-*       2/2  Running  (v1.1.1 o anterior)
airflow-dag-processor-*    4/4  Running  (v1.1.1 o anterior)
airflow-scheduler-*        4/4  Running  (v1.1.1 o anterior)
airflow-worker-0           4/4  Running  (v1.1.1 o anterior)
airflow-redis-0            1/1  Running
airflow-triggerer-0        3/3  Running
airflow-statsd-*           1/1  Running
```

### Database Estado
- `documents` tabla: ✅ Tiene documento de prueba ID=1 (`test_document.pdf`)
- `document_chunks` tabla: ❌ VACÍA (0 embeddings) ← **ESTO ES LO QUE HAY QUE SOLUCIONAR**
- `pipeline_runs` tabla: Tiene 1 run fallido (limpiarlo antes de re-ejecutar)

## 🎯 Plan de Integración - Helm Upgrade v1.1.3

### Restricción Importante: CPU Quota Limitada
El cluster GKE no tiene CPU suficiente para rolling updates tradicionales. Solución: usar `--force --no-hooks` y borrar pods viejos manualmente para liberar recursos.

### Paso 1: Construir y Pushear Imagen v1.1.3

```bash
cd /Users/agustin/Documents/desarrollos/enterprise-ai-platform/airflow
./scripts/build-and-push.sh
```

**Verificar en GCR**:
```bash
gcloud container images list-tags gcr.io/itmind-macro-ai-dev-0/airflow-custom --limit=3
```

### Paso 2: Regenerar airflow-values.yaml desde Template

El script `03-deploy.sh` hace la sustitución de variables. Extraemos solo la parte de generación de valores:

```bash
cd /Users/agustin/Documents/desarrollos/itmind-infrastructure/fast/tenants/macro/deploy-dev-airflow

# Obtener variables de Terraform
export PROJECT_ID="itmind-macro-ai-dev-0"
export AIRFLOW_WI_SA=$(terraform -chdir=../workloads-ai-dev output -json service_accounts | jq -r '.airflow_wi')
export CONN_NAME=$(terraform -chdir=../workloads-ai-dev output -json cloud_sql | jq -r '.instance.connection_name')
export DAGS_BUCKET="macro-ai-dev-airflow"
export LOGS_BUCKET=$(terraform -chdir=../workloads-ai-dev output -json airflow_infra | jq -r '.logs_bucket')
export JWT_SECRET=$(gcloud secrets versions access latest --secret=macro-ai-dev-airflow-jwt-secret --project=$PROJECT_ID)

# Generar airflow-values.yaml
sed -e "s|\${AIRFLOW_WI_SA_EMAIL}|${AIRFLOW_WI_SA}|g" \
    -e "s|\${CLOUD_SQL_CONNECTION_NAME}|${CONN_NAME}|g" \
    -e "s|\${DAGS_BUCKET}|${DAGS_BUCKET}|g" \
    -e "s|\${LOGS_BUCKET}|${LOGS_BUCKET}|g" \
    -e "s|\${PROJECT_ID}|${PROJECT_ID}|g" \
    -e "s|\${JWT_SECRET}|${JWT_SECRET}|g" \
    -e "s|\${OAUTH_CLIENT_ID}|not-configured|g" \
    -e "s|\${OAUTH_CLIENT_SECRET}|not-configured|g" \
    02-values.yaml.tpl > airflow-values.yaml
```

### Paso 3: Helm Upgrade con Force

```bash
helm upgrade airflow apache-airflow/airflow \
  --version 1.19.0 \
  -n airflow \
  -f airflow-values.yaml \
  --force --no-hooks
```

**Nota**: `--force` recrea los recursos. `--no-hooks` evita que el migration job se cuelgue.

### Paso 4: Purgar Pods Viejos (Liberar CPU)

Inmediatamente después del upgrade, borrar pods para liberar CPU:

```bash
kubectl delete pod -n airflow -l component=worker --force --grace-period=0
kubectl delete pod -n airflow -l component=scheduler --force --grace-period=0
kubectl delete pod -n airflow -l component=dag-processor --force --grace-period=0
kubectl delete pod -n airflow -l component=api-server --force --grace-period=0
```

### Paso 5: Esperar Nuevos Pods

```bash
kubectl wait --for=condition=Ready pod -n airflow -l component=worker --timeout=300s
kubectl wait --for=condition=Ready pod -n airflow -l component=scheduler --timeout=300s
kubectl wait --for=condition=Ready pod -n airflow -l component=dag-processor --timeout=300s
kubectl wait --for=condition=Ready pod -n airflow -l component=api-server --timeout=300s
```

### Paso 6: Verificar Imagen v1.1.3

```bash
kubectl get pods -n airflow -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}' | grep airflow-custom
```

Debe mostrar: `gcr.io/itmind-macro-ai-dev-0/airflow-custom:3.1.7-v1.1.3`

### Paso 7: Verificar Tiktoken Cache

```bash
kubectl exec -n airflow airflow-worker-0 -c worker -- python3 -c "import tiktoken; enc = tiktoken.get_encoding('cl100k_base'); print('✓ Encoding loaded from cache, no download needed')"
```

## 🧪 Testing del Pipeline RAG

Una vez deployado v1.1.3:

### Paso 1: Copiar Documento de Prueba al Worker

```bash
kubectl cp tests/data/demo/001\ RRHH\ -\ Administración.pdf \
  airflow/airflow-worker-0:/tmp/test_document.pdf -c worker
```

### Paso 2: Limpiar Pipeline Run Fallido Anterior

```bash
kubectl exec -n airflow airflow-worker-0 -c worker -- python3 -c "
import os, psycopg
conn = psycopg.connect(os.environ['DATABASE_URL'])
conn.execute('DELETE FROM pipeline_runs WHERE document_id = 1')
conn.commit()
print('✓ Pipeline run limpiado')
"
```

### Paso 3: Disparar DAG via API

```bash
# Port-forward al API server
kubectl port-forward svc/airflow-api-server 8080:8080 -n airflow &

# Obtener token JWT (Airflow 3 usa /auth/token, no Basic Auth)
TOKEN=$(curl -s -X POST http://localhost:8080/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Disparar DAG (endpoint /api/v2 en Airflow 3)
curl -X POST http://localhost:8080/api/v2/dags/rag_indexing/dagRuns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "logical_date": "2026-03-05T15:00:00Z",
    "conf": {
      "document_id": 1,
      "file_path": "/tmp/test_document.pdf"
    }
  }'
```

### Paso 4: Monitorear Ejecución

```bash
# Ver logs del worker en tiempo real
kubectl logs -n airflow -f airflow-worker-0 -c worker

# Ver estado de tasks en UI
# Abrir http://localhost:8080 (port-forward debe estar activo)
```

### Paso 5: Verificar Resultados

```bash
kubectl exec -n airflow airflow-worker-0 -c worker -- python3 -c "
import os, psycopg
conn = psycopg.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Verificar chunks creados
cur.execute('SELECT COUNT(*) FROM document_chunks WHERE document_id = 1')
chunk_count = cur.fetchone()[0]
print(f'✓ Chunks indexados: {chunk_count}')

# Verificar embeddings generados (embeddings es bytea, verificamos que no sea NULL)
cur.execute('SELECT COUNT(*) FROM document_chunks WHERE document_id = 1 AND embeddings IS NOT NULL')
embedding_count = cur.fetchone()[0]
print(f'✓ Embeddings generados: {embedding_count}')

# Verificar status del pipeline
cur.execute('SELECT status, error FROM pipeline_runs WHERE document_id = 1 ORDER BY id DESC LIMIT 1')
row = cur.fetchone()
if row:
    status, error = row
    print(f'✓ Pipeline status: {status}')
    if error:
        print(f'  Error: {error}')
else:
    print('⚠️  No pipeline run encontrado')
"
```

**Resultado esperado**:
- Chunks indexados: ~40-60 (depende del tamaño de documento)
- Embeddings generados: mismo número que chunks
- Pipeline status: `completed`

## 📝 Estructura del DAG `rag_indexing`

El DAG tiene 5 tasks secuenciales:

1. **validate_file**: Verifica que el archivo existe y es accesible
2. **load_and_chunk**: Carga documento y hace chunking adaptativo (usa tiktoken)
3. **generate_embeddings**: Genera embeddings con Vertex AI Gemini (768 dimensiones)
4. **store_in_pgvector**: Almacena chunks y embeddings en `document_chunks` (halfvec)
5. **update_status**: Actualiza `pipeline_runs.status = 'completed'`

## ⚠️ Troubleshooting Común

### Pod Worker Stuck en Init
**Síntoma**: Worker pod queda en `Init:0/4` después de force-delete.  
**Causa**: Interface veth huérfana en nodo GKE.  
**Solución**:
```bash
kubectl scale statefulset airflow-worker -n airflow --replicas=0
# Esperar 2 minutos para cleanup de interfaces
sleep 120
kubectl scale statefulset airflow-worker -n airflow --replicas=1
```

### Tiktoken Download Timeout
**Síntoma**: Task `load_and_chunk` falla con timeout a `openaipublic.blob.core.windows.net`.  
**Causa**: Imagen no tiene tiktoken pre-cacheado.  
**Solución**: Verificar que se está usando imagen v1.1.2+ (debe tener el cache).

### Database Authentication Failed
**Síntoma**: `password authentication failed for user "enterprise_ai"`.  
**Causa**: DATABASE_URL usa usuario incorrecto.  
**Solución**: Verificar template línea 100 tiene `enterprise_ai_admin`.

## 🔐 Secretos en Secret Manager

- `macro-ai-dev-airflow-connection`: Connection string de Cloud SQL (airflow database)
- `macro-ai-dev-airflow-fernet-key`: Fernet key para cifrado de connections/variables
- `macro-ai-dev-airflow-api-secret`: Secret key para JWT API tokens
- `macro-ai-dev-airflow-jwt-secret`: JWT secret compartido con enterprise-ai-platform backend
- `macro-ai-dev-enterprise-ai-password`: Password de `enterprise_ai_admin` (usado en DATABASE_URL)

## 🎓 Lecciones Aprendidas

1. **Airflow 3 API Changes**: Usa `/api/v2` endpoints y JWT authentication (`/auth/token`), no Basic Auth.
2. **GKE Resource Constraints**: En clusters con CPU limitada, usar `--force --no-hooks` y borrado manual de pods.
3. **Template Regeneration**: NUNCA editar `airflow-values.yaml` directamente, siempre el template `.tpl`.
4. **Egress Filtering**: Pre-cachear assets externos (tiktoken) en imagen Docker, no asumir internet abierto.
5. **Cloud SQL Auth Proxy**: Siempre usar versión `-alpine` en jobs (para que el sidecar termine con el main container).
6. **Multi-executor Stability**: Multi-executor (`CeleryExecutor,KubernetesExecutor`) es estable desde Airflow 3.1.1+.

---

# 🚢 Plan de Integración: Backend/Frontend (Enterprise AI Platform)

## 📊 Estado Actual del Release `rag`

### Helm Release Info
- **Namespace**: `enterprise-ai`
- **Release**: `rag` (Revisión 11, última actualización: 3 de Marzo 2026)
- **Chart**: `./helm/enterprise-ai-platform` versión `0.1.0`
- **Estado**: `deployed`

### Imágenes Actuales en Producción
- **Backend**: `us-east1-docker.pkg.dev/itmind-macro-ai-dev-0/ai-platform-test/backend:0.1.0`
- **Frontend**: `us-east1-docker.pkg.dev/itmind-macro-ai-dev-0/ai-platform-test/frontend:0.1.1-localhost`

### Pods Running
```
rag-enterprise-ai-platform-api-*        3/3  Running  (backend:0.1.0)
rag-enterprise-ai-platform-frontend-*   2/2  Running  (frontend:0.1.1-localhost)
rag-redis-master-0                      1/1  Running
```

### Configuración Actual (desde `helm get values`)
- **Autoscaling Backend**: Habilitado (min: 2, max: 5 réplicas, target CPU: 70%)
- **Réplicas Frontend**: 2 (sin autoscaling)
- **Vertex AI**: Habilitado (`useVertexAi: "true"`)
- **Workload Identity**: Configurada (`macro-ai-dev-backend-wi@itmind-macro-ai-dev-0.iam.gserviceaccount.com`)
- **Ingress**: Configurado para `api.staging.rag.dataoilers.com` y `staging.rag.dataoilers.com`
- **Redis**: In-cluster Bitnami (mirroreada en Artifact Registry)

## 🎯 Cambios a Deployar

### Último Commit (a69dee3 - 4 Marzo 2026)
**Auditoría Sprint 6: Consolidación y Mejoras**
- ✅ Mover valores hardcodeados a `settings.py` (chunk_size, chunk_overlap, thresholds)
- ✅ AdaptiveChunker y MemoryService leen de configuración centralizada
- ✅ Tests adicionales de GroupResolver (jerarquía, ciclos, errores DB)
- ✅ Error handling mejorado con logging
- ✅ Unificar response key del nodo retrieve a "context_text"
- ✅ Transiciones suaves en dark mode (frontend)

### Tag de Imagen Objetivo
Usar el hash del commit como tag: `a69dee3` (o crear un tag semántico como `0.1.2`)

## 📋 Plan de Integración Paso a Paso

### PASO 1: Build y Push de Nuevas Imágenes

**1.1 Backend**
```bash
# Opción A: Build manual (si no hay script de build)
cd /Users/agustin/Documents/desarrollos/enterprise-ai-platform
docker build -t us-east1-docker.pkg.dev/itmind-macro-ai-dev-0/ai-platform-test/backend:a69dee3 -f docker/Dockerfile.backend .
docker push us-east1-docker.pkg.dev/itmind-macro-ai-dev-0/ai-platform-test/backend:a69dee3

# Opción B: Si existe script de build
./scripts/build-backend.sh a69dee3
```

**1.2 Frontend**
```bash
# Opción A: Build manual
docker build -t us-east1-docker.pkg.dev/itmind-macro-ai-dev-0/ai-platform-test/frontend:a69dee3 -f docker/Dockerfile.frontend .
docker push us-east1-docker.pkg.dev/itmind-macro-ai-dev-0/ai-platform-test/frontend:a69dee3

# Opción B: Si existe script de build
./scripts/build-frontend.sh a69dee3
```

**1.3 Verificar Imágenes en Artifact Registry**
```bash
gcloud container images list-tags us-east1-docker.pkg.dev/itmind-macro-ai-dev-0/ai-platform-test/backend --limit=3
gcloud container images list-tags us-east1-docker.pkg.dev/itmind-macro-ai-dev-0/ai-platform-test/frontend --limit=3
```

### PASO 2: Helm Upgrade

**2.1 Preparar el Comando**

Hay dos estrategias posibles:

**Opción A: Upgrade con --reuse-values (Recomendado para cambios solo de imagen)**
```bash
helm upgrade rag ./helm/enterprise-ai-platform \
  -n enterprise-ai \
  --set backend.image.tag=a69dee3 \
  --set frontend.image.tag=a69dee3 \
  --reuse-values \
  --wait
```
**Ventaja**: Mantiene todos los secretos y configuraciones actuales (JWT, Gemini API key, DB password, etc.)
**Desventaja**: No recoge cambios en `values-staging.yaml` si los hay

**Opción B: Upgrade con -f values-staging.yaml (Recomendado si hay cambios en config)**
```bash
helm upgrade rag ./helm/enterprise-ai-platform \
  -n enterprise-ai \
  -f ./helm/enterprise-ai-platform/values-staging.yaml \
  --set backend.image.tag=a69dee3 \
  --set frontend.image.tag=a69dee3 \
  --set secrets.jwtSecret="7875a14755fc5d64a76b125e0119e1fa2bf75317814525714277b89c0e2be86d" \
  --set secrets.geminiApiKey="AQ.Ab8RN6IcBlE1NJ5goCLTibjrOZgRKvj8dqQ8BIIsPtCvP1G-Ig" \
  --set secrets.databaseUrl="postgresql+asyncpg://enterprise_ai_admin:rR%3CXZ4%7DsWDVW9AY5Pr%7BCTV9ef5jk%29K%3Dy@127.0.0.1:5432/enterprise_ai" \
  --set secrets.langfusePublicKey="pk-lf-9e93b81c-7e78-4de9-a82d-d4fd580bfff6" \
  --set secrets.langfuseSecretKey="sk-lf-21aa7e7c-5313-4745-9382-489c864adc11" \
  --set redis.auth.password="<REDIS_PASSWORD_FROM_SECRET>" \
  --wait
```
**Ventaja**: Aplica cambios completos del values-staging.yaml
**Desventaja**: Requiere reinyectar todos los secrets

**2.2 Consideraciones para Cluster con CPU Limitada**

Si el upgrade se queda colgado por falta de recursos (similar al problema de Airflow):

```bash
# Upgrade con force (recrea recursos)
helm upgrade rag ./helm/enterprise-ai-platform \
  -n enterprise-ai \
  -f ./helm/enterprise-ai-platform/values-staging.yaml \
  --set backend.image.tag=a69dee3 \
  --set frontend.image.tag=a69dee3 \
  --force --no-hooks

# Inmediatamente forzar borrado de pods viejos
kubectl delete pod -n enterprise-ai -l app.kubernetes.io/component=api --force --grace-period=0
kubectl delete pod -n enterprise-ai -l app.kubernetes.io/component=frontend --force --grace-period=0
```

### PASO 3: Verificación Post-Deployment

**3.1 Verificar Nuevos Pods Levantando**
```bash
# Ver pods en tiempo real
kubectl get pods -n enterprise-ai -w

# Esperar a que estén Ready
kubectl wait --for=condition=Ready pod -n enterprise-ai -l app.kubernetes.io/component=api --timeout=300s
kubectl wait --for=condition=Ready pod -n enterprise-ai -l app.kubernetes.io/component=frontend --timeout=300s
```

**3.2 Verificar Imágenes Actualizadas**
```bash
kubectl describe deployment rag-enterprise-ai-platform-api -n enterprise-ai | grep Image
kubectl describe deployment rag-enterprise-ai-platform-frontend -n enterprise-ai | grep Image
```

Debe mostrar:
```
Image: us-east1-docker.pkg.dev/itmind-macro-ai-dev-0/ai-platform-test/backend:a69dee3
Image: us-east1-docker.pkg.dev/itmind-macro-ai-dev-0/ai-platform-test/frontend:a69dee3
```

**3.3 Verificar Health Checks**
```bash
# Port-forward para probar endpoints localmente
kubectl port-forward svc/rag-enterprise-ai-platform 8000:80 -n enterprise-ai &
kubectl port-forward svc/rag-enterprise-ai-platform-frontend 3000:80 -n enterprise-ai &

# Verificar health endpoints
curl -s http://localhost:8000/health | jq
curl -s http://localhost:8000/health/ready | jq

# Verificar frontend responde
curl -s -o /dev/null -w "Frontend: %{http_code}\n" http://localhost:3000/
```

**3.4 Verificar Logs (Sin Errores)**
```bash
# Backend logs
kubectl logs -n enterprise-ai -l app.kubernetes.io/component=api --tail=50

# Frontend logs
kubectl logs -n enterprise-ai -l app.kubernetes.io/component=frontend --tail=50
```

**3.5 Smoke Test del RAG Chat**
```bash
# Probar endpoint de chat (si la indexación ya se hizo)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{
    "query": "¿Qué beneficios tiene el banco?",
    "conversation_id": "test-001"
  }' | jq
```

### PASO 4: Rollback Plan (Si algo falla)

**Si el deployment nuevo presenta problemas:**

```bash
# Ver historial de releases
helm history rag -n enterprise-ai

# Rollback a la revisión anterior (11)
helm rollback rag 11 -n enterprise-ai

# Verificar que volvió a la versión anterior
kubectl describe deployment rag-enterprise-ai-platform-api -n enterprise-ai | grep Image
```

## 🔄 Flujo Completo de CI/CD (Futuro)

Basado en el `plan_integracion_cicd.md`, el flujo automatizado sería:

```yaml
# .github/workflows/deploy-backend-frontend.yml
name: Deploy Backend/Frontend to GKE

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'frontend/**'
      - 'helm/enterprise-ai-platform/**'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Authenticate to GCP via Workload Identity
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}
      
      - name: Build and Push Backend
        run: |
          docker build -t us-east1-docker.pkg.dev/.../backend:${{ github.sha }} -f docker/Dockerfile.backend .
          docker push us-east1-docker.pkg.dev/.../backend:${{ github.sha }}
      
      - name: Build and Push Frontend
        run: |
          docker build -t us-east1-docker.pkg.dev/.../frontend:${{ github.sha }} -f docker/Dockerfile.frontend .
          docker push us-east1-docker.pkg.dev/.../frontend:${{ github.sha }}
      
      - name: Helm Upgrade
        run: |
          gcloud container clusters get-credentials macro-ai-dev-gke --zone us-east1-b
          helm upgrade rag ./helm/enterprise-ai-platform \
            -n enterprise-ai \
            --set backend.image.tag=${{ github.sha }} \
            --set frontend.image.tag=${{ github.sha }} \
            --reuse-values \
            --wait --timeout 5m
```

## 📁 Ubicación de Helm Chart

```
/Users/agustin/Documents/desarrollos/enterprise-ai-platform/
└── helm/enterprise-ai-platform/
    ├── Chart.yaml                      # Metadata del chart
    ├── values.yaml                     # Valores por defecto
    ├── values-staging.yaml             # Valores para staging (GKE dev)
    ├── templates/
    │   ├── deployment.yaml             # Backend deployment
    │   ├── deployment-frontend.yaml    # Frontend deployment
    │   ├── service.yaml                # Backend service
    │   ├── service-frontend.yaml       # Frontend service
    │   ├── ingress.yaml                # Ingress para backend
    │   ├── ingress-frontend.yaml       # Ingress para frontend
    │   ├── configmap.yaml              # ConfigMap con env vars
    │   ├── secret.yaml                 # Secret con credenciales
    │   ├── serviceaccount.yaml         # ServiceAccount para Workload Identity
    │   ├── hpa.yaml                    # HorizontalPodAutoscaler (backend)
    │   └── pdb.yaml                    # PodDisruptionBudget
    └── charts/                         # Sub-charts (redis, postgresql)
```

## 🔐 Secretos Requeridos para Helm Upgrade

Los siguientes secretos están actualmente en el cluster (extraídos de `helm get values`):

| Secret | Valor Actual | Fuente |
|--------|--------------|--------|
| `secrets.jwtSecret` | `7875a14755...` | Generado con `openssl rand -hex 32` |
| `secrets.geminiApiKey` | `AQ.Ab8RN6...` | Google AI Studio / Vertex AI |
| `secrets.databaseUrl` | `postgresql+asyncpg://enterprise_ai_admin:rR<...>@127.0.0.1:5432/enterprise_ai` | Cloud SQL (URL-encoded) |
| `secrets.langfusePublicKey` | `pk-lf-9e93b81c...` | Langfuse dashboard |
| `secrets.langfuseSecretKey` | `sk-lf-21aa7e7c...` | Langfuse dashboard |
| `redis.auth.password` | (extraer del secret) | `kubectl get secret rag-redis -n enterprise-ai -o jsonpath='{.data.redis-password}' \| base64 -d` |

## 📞 Próximos Pasos

### Airflow Pipeline
1. ✅ Ejecutar plan de integración Airflow (build + helm upgrade v1.1.3)
2. ✅ Verificar DAG execution exitosa
3. ✅ Probar chat RAG con documento indexado
4. ⏳ Indexar documentación completa de RRHH
5. ⏳ Configurar indexación automática (trigger on upload)

### Backend/Frontend
1. ⏳ Build y push de imágenes con tag `a69dee3` (Sprint 6 changes)
2. ⏳ Helm upgrade del release `rag` en namespace `enterprise-ai`
3. ⏳ Verificación smoke tests post-deployment
4. ⏳ Monitoreo con Langfuse + métricas Prometheus

### CI/CD
1. ⏳ Configurar Workload Identity Federation (GitHub OIDC → GCP)
2. ⏳ Crear workflow `.github/workflows/deploy-backend-frontend.yml`
3. ⏳ Implementar Helm Hook para migraciones Alembic pre-upgrade
4. ⏳ Documentar proceso de rollback

---

**Última actualización**: 2026-03-05  
**Versión Airflow objetivo**: `3.1.7-v1.1.3`  
**Versión Backend/Frontend objetivo**: `a69dee3` (Sprint 6)
**Estado**: Ready para helm upgrade de ambos componentes
