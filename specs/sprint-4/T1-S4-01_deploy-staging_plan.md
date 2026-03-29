# T1-S4-01: Deploy completo a K8s Staging — Análisis de Factibilidad y Plan

## Veredicto: ✅ SE PUEDE HACER

Las dos dependencias directas están **done**:
- `T1-S3-01` (Dockerfile multi-stage) → `done` — `docker/Dockerfile` existe ✓
- `T1-S3-02` (Helm chart base) → `done` — `helm/enterprise-ai-platform/` completo (10 templates + `values-staging.yaml`) ✓

---

## Estado actual del proyecto (lo que ya existe)

| Componente | Archivo/Estado | OK para staging? |
|---|---|---|
| **Dockerfile** | `docker/Dockerfile` multi-stage, non-root, slim | ✅ Listo |
| **Helm chart** | `helm/enterprise-ai-platform/` con 10 templates | ✅ Listo |
| **values-staging.yaml** | Existe con config GKE, replicas=2, cert-manager | ✅ Listo (falta personalizar) |
| **PostgreSQL + pgvector** | Sub-chart Bitnami en `Chart.yaml`, initdb con `CREATE EXTENSION vector` | ✅ Listo |
| **Redis** | Sub-chart Bitnami en `Chart.yaml` | ✅ Listo |
| **Airflow** | Ya desplegado en GKE (namespace `airflow`), DAGs via GCS sync | ✅ Operativo (externo al chart) |
| **Langfuse** | `infra/langfuse/values.yaml` existe | ✅ Ya desplegado en GKE |
| **Frontend** | `frontend/` Next.js inicializado, login + chat UI con SSE | ✅ Listo (Vercel o Nginx) |

### Specs previas relevantes — todas `done` excepto una

| Spec | Estado | Relevancia para S4-01 |
|---|---|---|
| T1-S1-06 Langfuse K8s | done | Langfuse ya en el cluster |
| T1-S2-01 SQL Schema / Alembic | done | Schema listo para PG |
| T1-S2-02 Airflow K8s | done | Airflow ya operativo |
| T1-S3-01 Dockerfile | done | Imagen de producción lista |
| T1-S3-02 Helm chart | done | Chart base completo |
| T1-S3-03 GCP Monitoring | **pending** | No bloquea (es post-deploy) |
| T2-S2-01 Auth JWT | done | Backend auth listo |
| T2-S3-01 Chat SSE endpoint | done | Endpoint streaming listo |
| T5-S3-01/02 Frontend | done | Login + Chat UI implementados |

> **T1-S3-03 (GCP Monitoring)** está `pending` pero **no es dependencia de T1-S4-01**. No bloquea.

---

## Gaps identificados (lo que falta hacer para cumplir los AC)

### Gap 1 — Imagen Docker no está publicada en registry 🔴
El `values-staging.yaml` referencia `gcr.io/your-gcp-project-id/enterprise-ai-platform:0.1.0` pero la imagen no existe en GCR/Artifact Registry aún. Hay que buildear y pushear.

### Gap 2 — Secrets reales no configurados 🔴  
El `values-staging.yaml` tiene placeholders (`your-gcp-project-id`, JWT secret, Gemini API key, etc.). Hay que setear los valores reales vía `--set` o External Secrets.

### Gap 3 — Airflow: DAGs en el chart vs. GCS 🟡  
Airflow ya está desplegado externamente (namespace `airflow`, DAGs via GCS). El chart no incluye Airflow — los DAGs del proyecto (`dags/`) deben sincronizarse al GCS bucket del cluster staging.

### Gap 4 — cert-manager en el cluster 🟡  
El `values-staging.yaml` usa `cert-manager.io/cluster-issuer: letsencrypt-staging`. Hay que verificar que cert-manager esté instalado y el ClusterIssuer creado.

### Gap 5 — `helm dependency update` no ejecutado 🟡  
Los sub-charts Bitnami (PostgreSQL 16.4.3, Redis 20.6.3) requieren `helm dependency update` para descargar los `.tgz`. No hay `charts/` directory en el repo.

### Gap 6 — Dominio DNS para staging 🟡  
`api.staging.rag.dataoilers.com` debe apuntar al IP del ingress del cluster.

### Gap 7 — Alembic migrations en startup 🟡  
Hay que asegurarse de que el backend corre `alembic upgrade head` antes de levantar (o usar un init container en el Deployment).

### Gap 8 — Frontend: decisión Vercel vs. Nginx 🟢  
La spec dice "puede ser Vercel preview". Si se elige Vercel: solo configurar `NEXT_PUBLIC_API_URL`. Si se elige in-cluster: agregar Deployment/Service al chart.

---

## Plan de integración (pasos ordenados)

### Fase 1 — Prerrequisitos de cluster (Franco, ~1h)
1. Verificar que cert-manager está instalado: `kubectl get pods -n cert-manager`
2. Si no: `helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set installCRDs=true`
3. Crear ClusterIssuer Let's Encrypt staging:
```yaml
# infra/cluster/cluster-issuer-staging.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: team@dataoilers.com
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
      - http01:
          ingress:
            class: nginx
```
4. Verificar nginx ingress controller: `kubectl get pods -n ingress-nginx`

### Fase 2 — Build y Push de imagen Docker (Franco, ~30min)
```bash
# Desde raíz del proyecto
export PROJECT_ID=<your-gcp-project-id>
export TAG=0.1.0

docker build -f docker/Dockerfile -t gcr.io/$PROJECT_ID/enterprise-ai-platform:$TAG .
docker push gcr.io/$PROJECT_ID/enterprise-ai-platform:$TAG
```
> Asegurarse que GKE tiene permisos para pull de GCR (Workload Identity o imagePullSecrets).

### Fase 3 — Helm dependency update (Agus, ~10min)
```bash
cd helm/enterprise-ai-platform
helm dependency update
# Verifica que charts/ contiene postgresql-16.4.3.tgz y redis-20.6.3.tgz
```

### Fase 4 — Personalizar values-staging.yaml (Agus, ~30min)

Editar `helm/enterprise-ai-platform/values-staging.yaml`:
```yaml
global:
  gcpProjectId: "itmind-macro-ai-dev-0"  # Completar con el real
  domain: staging.rag.dataoilers.com

backend:
  image:
    repository: gcr.io/itmind-macro-ai-dev-0/enterprise-ai-platform
    tag: "0.1.0"
```

### Fase 5 — Instalar en staging namespace (Agus, ~30min)
```bash
kubectl create namespace rag-staging

# Setear secrets via --set (NO commitear)
helm upgrade --install rag-staging ./helm/enterprise-ai-platform \
  -f ./helm/enterprise-ai-platform/values-staging.yaml \
  -n rag-staging \
  --set secrets.jwtSecret="$(openssl rand -base64 32)" \
  --set secrets.geminiApiKey="$GEMINI_API_KEY" \
  --set secrets.databaseUrl="postgresql+asyncpg://raguser:$PG_PASS@rag-staging-postgresql:5432/rag_db" \
  --set secrets.redisUrl="redis://:$REDIS_PASS@rag-staging-redis-master:6379/0" \
  --set postgresql.auth.password="$PG_PASS" \
  --set redis.auth.password="$REDIS_PASS" \
  --set secrets.langfusePublicKey="$LANGFUSE_PK" \
  --set secrets.langfuseSecretKey="$LANGFUSE_SK"
```

### Fase 6 — Alembic migrations (Agus, ~15min)

Verificar si el Deployment ya tiene initContainer para migraciones. Si no, correr manualmente en el primer deploy:
```bash
kubectl run alembic-migrate --rm -it \
  --image=gcr.io/<PROJECT_ID>/enterprise-ai-platform:0.1.0 \
  --env="DATABASE_URL=postgresql+asyncpg://raguser:$PG_PASS@rag-staging-postgresql.rag-staging.svc.cluster.local:5432/rag_db" \
  --restart=Never \
  --namespace=rag-staging \
  -- alembic upgrade head
```

### Fase 7 — Sync DAGs a GCS staging (Franco, ~15min)
```bash
gsutil -m rsync -r ./dags gs://macro-ai-dev-airflow/dags/staging/
```
> Confirmar que el bucket es el correcto para el entorno staging (puede ser el mismo bucket de dev o uno separado).

### Fase 8 — Frontend (Ema/Agus, ~30min)

**Opción A — Vercel (recomendada para rapidez):**
- Push del frontend a rama `staging`
- Configurar env en Vercel: `NEXT_PUBLIC_API_URL=https://api.staging.rag.dataoilers.com`
- El AC dice "puede ser via Vercel preview" ✅

**Opción B — In-cluster:** Agregar Deployment/Service/Ingress para el frontend al chart (agrega ~2h de trabajo).

### Fase 9 — DNS y verificacion TLS (Franco, ~20min)
1. Obtener IP del ingress: `kubectl get ingress -n rag-staging`
2. Crear registro A en DNS: `api.staging.rag.dataoilers.com → <INGRESS_IP>`
3. Esperar que cert-manager emita el certificado: `kubectl describe certificate -n rag-staging`

### Fase 10 — Smoke test (Agus + Ema, ~30min)
```bash
# 1. Health check
curl https://api.staging.rag.dataoilers.com/health

# 2. Login
curl -X POST https://api.staging.rag.dataoilers.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "test1234"}'

# 3. Chat con streaming
curl -N https://api.staging.rag.dataoilers.com/api/v1/chat/stream \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué es el ratio de capital?"}'
```
4. Abrir frontend en staging y verificar login → chat → respuesta con streaming.

---

## Resumen de estimación

| Fase | Responsable | Tiempo estimado |
|---|---|---|
| Prerrequisitos cluster | Franco | 1h |
| Build + push imagen | Franco | 30min |
| Helm dep update + values | Agus | 40min |
| Deploy helm | Agus | 30min |
| Alembic migrations | Agus | 15min |
| DAGs sync | Franco | 15min |
| Frontend (Vercel) | Ema | 30min |
| DNS + TLS | Franco | 20min |
| Smoke test | Todos | 30min |
| **Total** | | **~4.5h** |

> La estimación de la spec era 8h+ asumiendo que el chart había que construirlo desde cero. Como ya existe y `values-staging.yaml` ya está, el esfuerzo real es ~4-5h.

---

## Decisiones a confirmar antes de arrancar

1. **¿GCP Project ID real para staging?** (actualmente `your-gcp-project-id` en values-staging.yaml) — parece ser `itmind-macro-ai-dev-0` según la doc de Airflow.
2. **¿Frontend vía Vercel o in-cluster?** — Vercel es más rápido para la demo.
3. **¿Mismo cluster GKE que Airflow/Langfuse?** — Asumo que sí, pero confirmar namespace strategy.
4. **¿Usar letsencrypt-staging (cert sin CA trust) o prod cert para la demo?** — Para la demo con stakeholders, usar letsencrypt-prod.
