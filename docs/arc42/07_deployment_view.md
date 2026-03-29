# 7. Deployment View

> **arc42 Section 7**: Describe la infraestructura técnica sobre la que se ejecuta el sistema, el mapeo de artefactos de software a elementos de infraestructura, y los aspectos de deployment.
>
> **Referencia**: [arc42 Section 7 — Deployment View](https://docs.arc42.org/section-7/)

---

## 7.1 Imágenes Docker

El proyecto produce **2 imágenes Docker**. No más.

```
┌─────────────────────────────────────────────────────────┐
│                      MONOREPO                            │
│                                                          │
│   pyproject.toml ──────────► Imagen 1: BACKEND           │
│   src/                       (Python 3.12 + FastAPI +    │
│   alembic/                    LangGraph + todo src/)     │
│                                                          │
│   frontend/package.json ───► Imagen 2: FRONTEND          │
│   frontend/app/              (Node.js + Next.js)         │
│   frontend/components/                                   │
│                                                          │
│   dags/ ──────────────────► NO necesita imagen propia    │
│                              (Airflow los sincroniza     │
│                               via GCS bucket)            │
│                                                          │
│   helm/ ─────────────────► NO es código ejecutable       │
│                              (templates YAML)             │
└─────────────────────────────────────────────────────────┘
```

### ¿Por qué no una imagen por "servicio"?

Porque no hay microservicios. El backend es **un proceso** que sirve la API REST (FastAPI), el pipeline RAG (LangGraph), los guardrails, y la auth. Todo en la misma imagen. Es un monolito modular: una imagen, múltiples módulos internos.

Ver [Section 4 — Solution Strategy](04_solution_strategy.md) para la justificación del monolito modular.

### Imagen Backend (Python)

| Aspecto | Valor |
|---------|-------|
| Base | `python:3.12-slim` |
| Build | Multi-stage (builder + runtime) |
| Usuario | non-root (`appuser`, UID 1000) |
| Target | < 200MB |
| Contiene | `src/`, `alembic/`, dependencias Python |
| NO contiene | `tests/`, `docs/`, `dags/`, `frontend/`, `.git` |

### Imagen Frontend (Node.js)

| Aspecto | Valor |
|---------|-------|
| Base | `node:20-alpine` |
| Build | Multi-stage (deps + build + runtime) |
| Target | < 150MB |
| Contiene | Build output de Next.js (`.next/`) |
| NO contiene | `node_modules/` de desarrollo, source maps |

### DAGs de Airflow: sin imagen propia

Los DAGs de Airflow llegan al cluster via **GCS bucket** (`gsutil rsync`), un sidecar que sincroniza `dags/` desde un bucket de Cloud Storage:

```
┌─────────────────────── Airflow Pod ─────────────────────┐
│                                                          │
│  ┌──────────────┐    ┌──────────────┐                    │
│  │  Airflow      │    │  gcs-sync    │                    │
│  │  Scheduler    │◄───│  sidecar     │◄── GCS bucket     │
│  │              │    │              │    (gs://…/dags/)  │
│  │  lee dags/   │    │  sincroniza  │                    │
│  └──────────────┘    │  dags/       │                    │
│                       └──────────────┘                    │
│                                                          │
│  Cuando un DAG ejecuta, KubernetesExecutor lanza un      │
│  Pod separado con la imagen custom de Airflow + src/     │
└──────────────────────────────────────────────────────────┘
```

Los DAGs importan código de `src/` (por ejemplo, el `IndexingService`). Para que esto funcione en K8s, los worker pods de Airflow usan una **imagen custom** que incluye `src/` instalado como paquete Python. Los DAGs se sincronizan via **GCS bucket** (`gsutil rsync` desde CI/CD al bucket).

| Estrategia | Complejidad | Cuándo usarla |
|------------|-------------|---------------|
| **GCS bucket sync para `dags/`** | Baja | DAGs se suben al bucket desde CI/CD, el sidecar los sincroniza al pod |
| **Imagen custom de Airflow** | Media | Worker pods incluyen `src/` instalado como paquete Python para importar `IndexingService` |

**Nota**: No se usa git-sync porque el entorno bancario restringe acceso a repositorios Git externos desde el cluster.

---

## 7.2 Topología Kubernetes

Un solo Helm chart (`enterprise-ai-platform`) despliega los componentes de aplicación en el cluster GKE. La base de datos PostgreSQL se gestiona externamente como Cloud SQL (ver [ADR-012](decisions/ADR-012-cloud-sql-managed.md)):

```
helm install enterprise-ai-platform ./helm/enterprise-ai-platform
                    │
                    ▼
┌────────────────── Kubernetes Cluster (GKE) ──────────────────────┐
│                                                                  │
│  Namespace: enterprise-ai                                        │
│                                                                  │
│  ┌─── Deployment: backend ──────────────────────────────────────┐│
│  │  Replicas: 2                                                 ││
│  │  Image: gcr.io/tu-proyecto/backend:v1.0                      ││
│  │  ┌─────────────────────────────────────────────────────────┐ ││
│  │  │  Pod 1                                                  │ ││
│  │  │  ┌──────────────┐  ┌────────────────────────────────┐   │ ││
│  │  │  │  backend     │  │  cloud-sql-proxy (sidecar)     │   │ ││
│  │  │  │  FastAPI +   │  │  Workload Identity auth        │   │ ││
│  │  │  │  LangGraph   │──│  → localhost:5432              │   │ ││
│  │  │  └──────────────┘  └────────────┬───────────────────┘   │ ││
│  │  │                                 │ Private IP (PSA)      │ ││
│  │  └─────────────────────────────────┼───────────────────────┘ ││
│  └────────────────────────────────────┼─────────────────────────┘│
│                         │             │                          │
│  ┌─── Service: backend-svc ──┐     ┌──┼── Ingress ──────────────┐│
│  │  ClusterIP :8000          │◄────│  │api.tudominio.com → :8000││
│  └───────────────────────────┘     │  │app.tudominio.com → :3000││
│                                    └──┼─────────────────────────┘│
│  ┌─── Deployment: frontend ───────────┼─────────────────────────┐│
│  │  Replicas: 1                       │                         ││
│  │  Image: gcr.io/tu-proyecto/frontend:v1.0                     ││
│  │  ┌─────────┐                       │                         ││
│  │  │  Pod    │  ← Next.js (SSR)      │                         ││
│  │  │ frontend│                       │                         ││
│  │  └─────────┘                       │                         ││
│  └────────────────────────────────────┼─────────────────────────┘│
│                                       │                          │
│  ┌─── Deployment: redis ───┐          │                          │
│  │  bitnami/redis          │          │                          │
│  │  (cache de sesión)      │          │                          │
│  │  Sin persistencia       │          │                          │
│  └─────────────────────────┘          │                          │
│                                       │─|                        │
│  ┌─── ConfigMap ─────────┐  ┌─── Secret ┼────────────────────┐   │
│  │  REDIS_URL            │  │  JWT_SECRET                    │   │
│  │  LANGFUSE_HOST        │  │  DB_PASSWORD (from Secret Mgr) │   │
│  │  AIRFLOW_API_URL      │  │  GEMINI_API_KEY                │   │
│  │  INSTANCE_CONN_NAME   │  │  LANGFUSE_SECRET_KEY           │   │
│  └───────────────────────┘  └────────────────────────────────┘   │
│                                         │                        │
│  ── Otros namespaces (desplegados por separado) ──               │
│  │  Airflow  (namespace: airflow)  — Helm chart oficial          │
│  │  Langfuse (namespace: langfuse) — Helm chart oficial          │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             │ Private IP via PSA (10.2.224.0/20)
                             ▼
┌───────────────────────────────────────────────────────────┐
│  Cloud SQL for PostgreSQL 16 (ADR-012)                    │
│  Instancia: macro-ai-dev-db                               │
│  CMEK: macro-data-key | TLS: ENCRYPTED_ONLY               │
│                                                           │
│  ├── Database: enterprise_ai (ADR-004)                    │
│  │   Datos: relacional + pgvector + BM25 + LangGraph      │
│  │   User: enterprise_ai_admin                            │
│  │                                                        │
│  ├── Database: langfuse (ADR-010)                         │
│  │   Datos: metadata de traces LLM/RAG                    │
│  │   User: langfuse_admin                                 │
│  │                                                        │
│  └── Database: airflow (ADR-005)                          │
│      Datos: DAG runs, task instances, XCom, connections    │
│      User: airflow_admin                                  │
└───────────────────────────────────────────────────────────┘
```

### Infraestructura base (repo `itmind-infrastructure`)

La infraestructura GCP sobre la que se despliega este sistema se gestiona en un repositorio separado (`itmind-infrastructure`) usando Terraform con el framework FAST de Google Cloud. El equipo de infraestructura provisiona:

| Recurso | Ubicacion en itmind-infrastructure | Consumido por |
|---------|-----------------------------------|---------------|
| GKE cluster | `fast/tenants/macro/` | Todos los namespaces (enterprise-ai, airflow, langfuse) |
| Cloud SQL (PostgreSQL 16) | `specs/workloads-dev/A-03_ai-cloudsql-secrets.md` | enterprise_ai, langfuse, airflow databases |
| Shared VPC + PSA | `fast/tenants/macro/networking/` | Conectividad privada Cloud SQL |
| KMS (CMEK) | `fast/tenants/macro/security/` | Cifrado de datos en reposo |
| Workload Identity | `fast/tenants/macro/security/` | Auth sin service account keys |
| Secret Manager | `fast/tenants/macro/security/` | Credenciales DB, API keys |

**Importante**: Este repositorio (`enterprise-ai-platform`) contiene la aplicacion y sus Helm charts. No contiene la infraestructura GCP base. Cualquier cambio en GKE, Cloud SQL, VPC o IAM se gestiona en `itmind-infrastructure`.

### ¿Por qué un solo Helm chart para la aplicación?

Los componentes del chart son **acoplados operacionalmente**: el backend necesita que Redis esté arriba. El frontend necesita al backend. Se despliegan juntos, se versionan juntos, se configuran juntos.

PostgreSQL (Cloud SQL), Airflow y Langfuse son **externos al chart** porque:

| Componente | Gestión | Razón |
|------------|---------|-------|
| Backend + Frontend + Redis | `enterprise-ai-platform` (Helm chart propio) | Acoplados, ciclo de vida compartido |
| PostgreSQL | Cloud SQL (Terraform, ADR-012) | Managed service: backups, CMEK, HA, compliance bancaria |
| Airflow | `apache-airflow/airflow` (Helm chart oficial) | Producto tercero, ciclo de vida independiente |
| Langfuse | Chart oficial o manifests | Producto tercero, compartido por todo el equipo |

### Recursos Kubernetes por componente

| Componente | Tipo K8s | Probes | Notas |
|------------|----------|--------|-------|
| Backend | Deployment | liveness: `/health`, readiness: `/health/ready` | 2 réplicas staging, HPA en prod. Incluye cloud-sql-proxy sidecar |
| Frontend | Deployment | liveness: `/` | 1 réplica staging |
| Redis | Deployment (sub-chart) | TCP :6379 | Sin persistencia (cache de sesión) |
| Ingress | Ingress | N/A | TLS via cert-manager |
| Config | ConfigMap + Secret | N/A | Separación config pública vs secreta |

### Cloud SQL Auth Proxy como sidecar

Cada pod del backend incluye un container sidecar `cloud-sql-proxy` que:
1. Se autentica contra Cloud SQL via **Workload Identity** (sin service account keys)
2. Negocia **TLS automáticamente** entre el pod y Cloud SQL
3. Expone PostgreSQL en `localhost:5432` para la aplicación
4. La aplicación conecta como si fuera PostgreSQL local

Los pods de Airflow que necesiten acceder a Cloud SQL (workers de indexación) también incluyen el sidecar.

---

## 7.3 Flujo de un request

Cómo viaja una petición del usuario a través de la infraestructura:

```
Usuario (browser)
  │
  │ HTTPS
  ▼
Ingress Controller (GKE)
  │
  ├── app.tudominio.com ──────► Frontend Pod (Next.js SSR)
  │                                  │
  │                                  │ fetch interno (server-side)
  │                                  │ o fetch desde browser (client-side)
  │                                  ▼
  └── api.tudominio.com ──────► Backend Pod (FastAPI + cloud-sql-proxy)
                                     │
                            ┌────────┼────────┐
                            ▼        ▼        ▼
                        Cloud SQL   Redis   Vertex AI
                        (PG 16)    (cache)  (Gemini)
```

### Flujo detallado: query RAG

```
Browser ──► Next.js ──► POST /api/v1/conversations/{id}/messages
                              │
                              ▼
                         FastAPI (backend Pod)
                              │
                    ┌─────────┴─────────────────────┐
                    ▼                                 │
              JWT validation                          │
                    │                                 │
                    ▼                                 │
              LangGraph pipeline                      │
              (todo en el mismo proceso)              │
                    │                                 │
          ┌────────┼────────┬────────────┐           │
          ▼        ▼        ▼            ▼           │
      guardrail  retrieve  rerank    generate        │
      (input)    (pgvector) (Vertex)  (Gemini)       │
          │        │        │            │           │
          └────────┴────────┴────────────┘           │
                    │                                 │
                    ▼                                 │
              SSE stream ────────────────────────────┘
                    │
                    ▼
              Browser (tokens aparecen incrementalmente)

Conexión a PostgreSQL:
  backend container → localhost:5432 → cloud-sql-proxy sidecar
                                          → Private IP (PSA)
                                          → Cloud SQL (enterprise_ai)
```

### Flujo detallado: indexación batch

```
Operador ──► Airflow UI ──► Trigger DAG "rag_indexing"
                                   │
                                   ▼
                            Airflow Scheduler
                            (namespace: airflow)
                                   │
                                   ▼
                         KubernetesExecutor lanza
                         Worker Pod por cada task
                         (con cloud-sql-proxy sidecar)
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
              validate_file   generate_embeddings  store_in_pgvector
              (FileValidator)  (Gemini API)        (pgvector)
                    │              │              │
                    └──────────────┴──────────────┘
                                   │
                                   ▼
                            Cloud SQL (enterprise_ai)
                            via cloud-sql-proxy sidecar
```

---

## 7.4 Networking entre namespaces

Los componentes en diferentes namespaces se comunican via DNS interno de Kubernetes. Cloud SQL es externo al cluster y se accede via Private Service Access (PSA):

```
┌─── namespace: enterprise-ai ────┐     ┌─── namespace: airflow ──────┐
│                                  │     │                              │
│  backend ─────────────────────────────► airflow-webserver             │
│  (trigger DAGs via REST API)     │     │  :8080                      │
│                                  │     │                              │
│  redis ◄─── backend             │     │                              │
│  (session cache, ClusterIP)      │     │                              │
└──────────────────────────────────┘     └──────────────────────────────┘

                                         ┌─── namespace: langfuse ─────┐
┌─── namespace: enterprise-ai ────┐     │                              │
│                                  │     │                              │
│  backend ─────────────────────────────► langfuse-web                  │
│  (envía trazas via SDK)         │     │  :3000                      │
│                                  │     │                              │
└──────────────────────────────────┘     └──────────────────────────────┘

DNS interno: <service>.<namespace>.svc.cluster.local
Ejemplo:     redis.enterprise-ai.svc.cluster.local:6379

Conexiones a Cloud SQL (externas al cluster):
  backend pods           ──► cloud-sql-proxy sidecar ──► Cloud SQL (enterprise_ai)
  airflow scheduler/web  ──► cloud-sql-proxy sidecar ──► Cloud SQL (airflow)       [metadata]
  airflow worker pods    ──► cloud-sql-proxy sidecar ──► Cloud SQL (enterprise_ai) [indexing]
  langfuse pods          ──► cloud-sql-proxy sidecar ──► Cloud SQL (langfuse)
```

---

## 7.5 Entornos

| Entorno | Infraestructura | Propósito |
|---------|----------------|-----------|
| **Local (dev)** | Docker Compose: PG + Redis. Langfuse y Airflow del cluster compartido. | Desarrollo diario |
| **Staging** | GKE: Helm chart completo + Cloud SQL. Todo el stack. | Demo, QA, validación pre-prod |
| **Producción** | GKE: Helm chart con valores de prod + Cloud SQL HA. HPA, más réplicas. | Usuarios reales |

### Local vs Staging

```
LOCAL (cada desarrollador)              STAGING (cluster GKE)

┌────────────────────────┐       ┌──────────────────────────────┐
│  docker compose up     │       │  helm install enterprise-ai  │
│                        │       │                              │
│  ┌──────┐ ┌──────┐    │       │  ┌────────┐ ┌────────┐      │
│  │  PG  │ │Redis │    │       │  │Backend │ │Frontend│      │
│  └──────┘ └──────┘    │       │  │(2 pods)│ │(1 pod) │      │
│                        │       │  │+proxy  │ │        │      │
│  uvicorn src/ (local)  │       │  └────────┘ └────────┘      │
│  next dev (local)      │       │  ┌──────┐                   │
│                        │       │  │Redis │ (in-cluster)      │
│  Langfuse ──► cluster  │       │  └──────┘                   │
│  Airflow ──► cluster   │       │                              │
└────────────────────────┘       │  Cloud SQL ◄── via PSA       │
                                  │  Langfuse ──► cluster        │
                                  │  Airflow ──► cluster         │
                                  └──────────────────────────────┘
```

**Nota**: En local, PostgreSQL se ejecuta via Docker Compose (sin Cloud SQL Auth Proxy). La aplicación conecta directamente a `localhost:5432`. El flag `DATABASE_URL` en el entorno local apunta al container Docker, mientras que en staging/prod apunta a `localhost:5432` (via cloud-sql-proxy sidecar).
