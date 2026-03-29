# T1-S2-02: Deploy Airflow 3 en K8s + configuracion base

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Franco, Agus) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T3-S2-03 (DAG indexacion) |
| Depende de | Infra: A-01 a A-05 aplicados via `terraform apply` en `itmind-infrastructure` |
| Skill | `observability/SKILL.md` |
| Estimacion | XL (8h+) |

## Contexto

Airflow orquesta todos los pipelines batch: indexacion de documentos, sincronizacion CDC, evaluacion RAGAS. Necesita estar operativo en K8s antes de que T3 pueda crear el DAG de indexacion.

El deployment se basa en el spec detallado **D-01** del repo `itmind-infrastructure`, que incorpora 5 correcciones criticas descubiertas en pruebas internas (proyecto `macro-ia-test-tmp`) y features de **paridad con Cloud Composer**.

### Relacion entre repos

| Repo | Contenido | Directorio |
|------|-----------|------------|
| `itmind-infrastructure` | Terraform infra (A-01 a A-05) + deployment scripts + Helm values template | `fast/tenants/macro/workloads-ai-dev/` + `fast/tenants/macro/deploy-dev-airflow/` |
| `itmind-infrastructure` | Spec detallado del deployment | `specs/deploy-dev/D-01_airflow-helm-deploy.md` |
| `enterprise-ai-platform` | DAGs, verificacion, .env config | `dags/` + `infra/airflow/` + `.env.example` |

## Spec

Desplegar Apache Airflow 3.1.7 en el cluster GKE con **multi-executor hybrid** (`CeleryExecutor,KubernetesExecutor`), sincronizacion de DAGs desde GCS bucket, Cloud SQL Auth Proxy, Redis como broker Celery, y paridad con Cloud Composer. El equipo de desarrollo sube DAGs a GCS y opera Airflow via la UI o REST API. Tasks default corren en Celery workers persistentes; tasks que necesitan aislamiento usan `executor="KubernetesExecutor"`.

## Acceptance Criteria

### Core deployment
- [ ] Airflow 3.1.7 desplegado via Helm chart oficial (`apache-airflow/airflow` v1.19.0) en namespace `airflow`
- [ ] Multi-executor: `CeleryExecutor,KubernetesExecutor` configurado
- [ ] Redis in-cluster habilitado como broker para CeleryExecutor (auth + persistence)
- [ ] Celery workers persistentes (StatefulSet, 2 replicas) con gcs-sync + cloud-sql-proxy sidecars
- [ ] DAGs sincronizados desde GCS bucket via sidecar `gsutil rsync` cada 30s en scheduler, dagProcessor, y workers
- [ ] Cloud SQL Auth Proxy como sidecar en **todos** los componentes: scheduler, apiServer, triggerer, dagProcessor, workers, migrateDatabaseJob
- [ ] ServiceAccount `airflow-sa` con annotation de Workload Identity
- [ ] Override de comando para API Server: `command: ["bash", "-c", "exec airflow api-server"]` (fix Airflow 3)
- [ ] K8s Secrets creados desde Secret Manager: `airflow-db-credentials`, `airflow-fernet-key`, `airflow-api-secret`, `airflow-redis-password`
- [ ] Migration job completado sin quedar bloqueado (imagen alpine del proxy)
- [ ] Todos los pods en estado Running (scheduler, api-server, dag-processor, triggerer, 2x worker, redis, statsd)
- [ ] DAGs visibles en UI via port-forward (`kubectl port-forward svc/airflow-api-server 8080:8080 -n airflow`)
- [ ] Tasks default corren en Celery workers (no crean pods nuevos)

### Cloud Composer parity features
- [ ] Secret Manager backend configurado (`AIRFLOW__SECRETS__BACKEND = CloudSecretManagerBackend`)
- [ ] Remote logging a GCS bucket (`macro-ai-dev-airflow-logs`)
- [ ] Fernet key para encriptar connections/variables en metastore
- [ ] API secret key para firmar JWT tokens del API server
- [ ] StatsD exporter habilitado para Managed Prometheus
- [ ] Database cleanup CronJob (2 AM diario)
- [ ] `apache-airflow-providers-google` instalado
- [ ] Network Policy para namespace `airflow` (Dataplane V2)
- [ ] Security contexts configurados (runAsUser: 50000, allowPrivilegeEscalation: false)
- [ ] Resource requests/limits definidos para todos los componentes

### Configuracion de acceso
- [ ] Google OAuth configurado via ConfigMap `airflow-webserver-config` (opcional, requiere OAuth Client ID)
- [ ] Variable `AIRFLOW_API_URL` documentada en `.env.example` para que FastAPI dispare DAGs via REST API
- [ ] Connection a Vertex AI (Gemini) creada en Secret Manager (`airflow-connections-google_cloud_default`)

### Verificacion
- [ ] DAG de prueba (`hello_world.py`) subido a GCS y ejecutado correctamente
- [ ] Logs del DAG visibles en la UI (remote logging a GCS funcionando)

## Arquitectura

```
┌──────────────────────────────────────────────────────────────┐
│ GKE Cluster (macro-ai-dev-gke)                               │
│                                                              │
│  ┌─ namespace: airflow ────────────────────────────────────┐ │
│  │                                                         │ │
│  │  K8s SA: airflow-sa                                     │ │
│  │    ↕ Workload Identity (A-04)                           │ │
│  │  GCP SA: macro-ai-dev-airflow-wi                        │ │
│  │                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐    │ │
│  │  │ Scheduler   │  │ API Server  │  │ DAG Processor│    │ │
│  │  │ + sql-proxy │  │ + sql-proxy │  │ + sql-proxy  │    │ │
│  │  │ + gcs-sync  │  │             │  │ + gcs-sync   │    │ │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘    │ │
│  │         │                │                │             │ │
│  │  ┌──────┴──────┐  ┌─────┴──────┐                       │ │
│  │  │ Triggerer   │  │  StatsD    │                       │ │
│  │  │ + sql-proxy │  │ → Prometheus│                       │ │
│  │  └─────────────┘  └────────────┘                       │ │
│  │                                                         │ │
│  │  ┌──────────────────────────────────────────┐           │ │
│  │  │ Celery Workers (StatefulSet, 2 replicas) │           │ │
│  │  │ + sql-proxy + gcs-sync sidecars          │           │ │
│  │  │ → procesan tasks default via Redis       │           │ │
│  │  └──────────────────┬───────────────────────┘           │ │
│  │                     │                                   │ │
│  │  ┌──────────────────┴───────────────────────┐           │ │
│  │  │ Redis (broker Celery, persistence 1Gi)   │           │ │
│  │  └──────────────────────────────────────────┘           │ │
│  │                                                         │ │
│  │  ┌──────────────────────────────────────────┐           │ │
│  │  │ K8s Workers (pods efimeros, on-demand)   │           │ │
│  │  │ + sql-proxy sidecar                      │           │ │
│  │  │ → tasks con executor="KubernetesExecutor"│           │ │
│  │  └──────────────────────────────────────────┘           │ │
│  └─────────────────────────────────────────────────────────┘ │
│          │                                                   │
│  GCS Buckets:             Secret Manager:                    │
│  - macro-ai-dev-dags      - airflow-connection               │
│  - macro-ai-dev-airflow-  - airflow-fernet-key               │
│    logs                   - airflow-api-secret               │
│                           - airflow-connections-*            │
│          │ PSA (10.2.224.0/20)                               │
└──────────┼───────────────────────────────────────────────────┘
           ▼
  ┌────────────────────────┐
  │ Cloud SQL (A-03)       │
  │ macro-ai-dev-db        │
  │ ├── enterprise_ai      │
  │ ├── airflow (metadata) │
  │ └── langfuse           │
  └────────────────────────┘
```

## Archivos a crear/modificar

### enterprise-ai-platform (este repo)

| Archivo | Accion | Descripcion |
|---------|--------|-------------|
| `dags/hello_world.py` | Crear | DAG de verificacion (TaskFlow API) |
| `infra/airflow/README.md` | Crear | Instrucciones para el equipo de dev (UI, DAGs, connections, executor routing) |
| `.env.example` | Modificar | Actualizar `AIRFLOW_API_URL` con instrucciones correctas (api-server, no webserver) |

### itmind-infrastructure (repo de infra, ya creados)

| Archivo | Descripcion |
|---------|-------------|
| `fast/tenants/macro/deploy-dev-airflow/00-namespace.yaml` | Namespace `airflow` con labels |
| `fast/tenants/macro/deploy-dev-airflow/01-secrets.sh` | Crea 3 K8s Secrets + ConfigMap OAuth desde Secret Manager |
| `fast/tenants/macro/deploy-dev-airflow/02-values.yaml.tpl` | Helm values template (7 variables a sustituir) |
| `fast/tenants/macro/deploy-dev-airflow/03-deploy.sh` | Script de deployment completo (6 fases) |
| `fast/tenants/macro/deploy-dev-airflow/04-network-policy.yaml` | NetworkPolicy para Dataplane V2 |
| `fast/tenants/macro/deploy-dev-airflow/README.md` | Quick start y troubleshooting |

## Dependencia de infraestructura

Esta task requiere que el equipo de infraestructura haya desplegado previamente desde el repo `itmind-infrastructure`:

| Recurso | Spec | Terraform | Necesario para | Estado |
|---------|------|-----------|----------------|--------|
| GKE cluster + node pools | A-02 | `gke.tf` | Cluster donde corren los pods | Done |
| Cloud SQL + database `airflow` | A-03 | `cloudsql.tf` | Metastore de Airflow | Done |
| Workload Identity SA | A-04 | `iam.tf` | Auth keyless para Cloud SQL, GCS, Secret Manager | Done |
| GCS buckets (DAGs + logs) | A-05 | `airflow.tf` | Sync DAGs + remote task logging | Done |
| Secrets (connection, Fernet, API) | A-05 | `airflow.tf` | Credenciales encriptadas | Done |

Para el deployment completo con Helm values, Cloud SQL Auth Proxy sidecars, y troubleshooting:
> `itmind-infrastructure/specs/deploy-dev/D-01_airflow-helm-deploy.md`

## Correcciones criticas incorporadas (de pruebas internas)

Estas 5 lecciones fueron descubiertas en el proyecto `macro-ia-test-tmp` y estan incorporadas en los deployment scripts:

| # | Problema | Solucion |
|---|----------|----------|
| 1 | 403 en Cloud SQL Proxy -- migration job sin WI | Todos los componentes usan `serviceAccountName: airflow-sa` |
| 2 | Helm bloqueado -- sidecar proxy no muere en Jobs | Imagen alpine del proxy (`2.14.3-alpine`) |
| 3 | Airflow 3 API Server CrashLoop | Override: `command: ["bash", "-c", "exec airflow api-server"]` |
| 4 | GCS Sync permisos -- no puede escribir en `/.config/gcloud` | `HOME=/tmp` en env del sidecar |
| 5 | DAGs invisibles -- dagProcessor sin SA | SA explicito en scheduler, triggerer, workers y dagProcessor |

## Runbook de deployment

El deployment se ejecuta desde `itmind-infrastructure`:

```bash
cd itmind-infrastructure/fast/tenants/macro/deploy-dev-airflow/
chmod +x 03-deploy.sh 01-secrets.sh

# Sin OAuth (basico):
./03-deploy.sh

# Con Google OAuth:
export OAUTH_CLIENT_ID="tu-client-id.apps.googleusercontent.com"
export OAUTH_CLIENT_SECRET="tu-client-secret"
./03-deploy.sh
```

El script `03-deploy.sh` ejecuta 6 fases automaticamente:
1. **Verificacion de prerequisitos** (cluster, DB, secrets, GCS bucket, Terraform outputs)
2. **Crear namespace** (`00-namespace.yaml`)
3. **Crear K8s Secrets** desde Secret Manager (`01-secrets.sh`)
4. **Generar Helm values** desde template (`02-values.yaml.tpl` → `airflow-values.yaml`)
5. **Helm install** con dry-run previo de validacion
6. **Verificacion post-deploy** + Network Policy (`04-network-policy.yaml`)

### Post-deploy (desde enterprise-ai-platform)

```bash
# 1. Subir DAG de prueba
gsutil cp dags/hello_world.py gs://macro-ai-dev-dags/dags/

# 2. Acceder a la UI (Airflow 3 usa api-server)
kubectl port-forward svc/airflow-api-server 8080:8080 -n airflow

# 3. Crear usuario admin
kubectl exec -it -n airflow -c api-server \
  $(kubectl get pod -n airflow -l component=api-server -o name | head -1) \
  -- airflow users create \
  --username admin --firstname Admin --lastname User \
  --role Admin --email admin@example.com --password admin

# 4. Crear connection para Vertex AI en Secret Manager
gcloud secrets create airflow-connections-google_cloud_default \
  --project=itmind-macro-ai-dev-0 \
  --data-file=/dev/stdin <<< '{"conn_type": "google_cloud_platform", "extra": {"project": "itmind-macro-ai-dev-0"}}'

# 5. Verificar DAG ejecuta
# Abrir http://localhost:8080 → hello_world → Trigger
```

## Decisiones de diseno

- **Multi-executor hybrid (`CeleryExecutor,KubernetesExecutor`)**: Celery para tasks normales (baja latencia, sin overhead de pod creation), KubernetesExecutor para tasks que necesitan aislamiento. Redis in-cluster como broker (suficiente para dev). Routing por task: `executor="KubernetesExecutor"`
- **GCS bucket sync (no GitSync)**: red bancaria sin acceso a repos Git externos. GCS accesible via Workload Identity
- **Cloud SQL Auth Proxy sidecar**: conexion a Cloud SQL via sidecar (127.0.0.1:5432). TLS automatico + auth via Workload Identity sin passwords en pods
- **Airflow 3**: soporte nativo de TaskFlow API mejorado, API Server (reemplaza webserver), DAG Processor separado
- **Cloud Composer parity**: Secret Manager backend, remote GCS logging, Fernet key, StatsD metrics, database cleanup, Google OAuth -- todo replicando lo que Cloud Composer ofrece out-of-the-box
- **Google OAuth directo** (no IAP): Cloud Composer usa IAP para proteger la UI. Nosotros usamos OAuth directamente (mas simple en dev, equivalente en seguridad)
- **Network Policy**: restringe trafico del namespace `airflow` a: intra-namespace, Cloud SQL (PSA range), y APIs de Google (`restricted.googleapis.com`)

## Cloud Composer parity checklist

| Feature | Cloud Composer | Nuestro setup | Status |
|---------|---------------|---------------|--------|
| GCS DAG sync | Nativo | gsutil rsync sidecar (30s) | Ready |
| GCS task logs | Nativo | remote_logging a GCS | Ready |
| Secret Manager backend | Nativo | `AIRFLOW__SECRETS__BACKEND` | Ready |
| Fernet key | Auto-generated | `random_id` → Secret Manager | Ready |
| API secret key | Auto-generated | `random_password` → Secret Manager | Ready |
| Cloud Monitoring | composer.googleapis.com | StatsD → Managed Prometheus | Ready |
| Google Auth | IAP + IAM | Google OAuth directo | Ready |
| DB maintenance | Auto | cleanup CronJob (2 AM) | Ready |
| Workload Identity | Required (Autopilot) | WI config (A-04) | Ready |
| DAG Processor separado | Nativo (Composer 3) | Nativo (Airflow 3.1.7) | Ready |
| Network isolation | Tenant project | NetworkPolicy (Dataplane V2) | Ready |
| Multi-executor | CeleryExecutor | CeleryExecutor,KubernetesExecutor | Ready |
| Redis broker | Interno | In-cluster (auth + persistence) | Ready |
| Persistent workers | StatefulSet | Celery workers (2 replicas) | Ready |

## Out of scope

- DAG de indexacion real (spec T3-S2-03)
- DAG de CDC OpenText (post-MVP)
- DAG de evaluacion RAGAS (post-MVP)
- Monitoring de Airflow en GCP (spec T1-S4-02)
- CI/CD pipeline para subir DAGs automaticamente al bucket
- Ingress/TLS para Airflow UI (post-MVP, usar port-forward en dev)
- Custom Docker image con providers pre-installed (usar `_PIP_ADDITIONAL_REQUIREMENTS` en dev)

---
> **Nota de Auditoría / Actualización:** A pesar de lo indicado inicialmente en los puntos fuera de alcance, **SÍ se construyó y utilizó una imagen custom de Airflow** (`airflow/Dockerfile`) que se integró con Artifact Registry. Esto fue fundamental para resolver de antemano dependencias a nivel de sistema (`libmupdf-dev`), asegurar el pre-caching de `tiktoken` (para no tener fallas de Cloud NAT en GKE) y dejar empaquetado el código fuente interno (`src/`). **La tarea se encuentra finalizada y validada.**
