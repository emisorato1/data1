# T1-S1-06: Deploy Langfuse en K8s

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Agus) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T1-S2-03 (instrumentacion), todo el equipo (tracing) |
| Depende de | Infra: GKE cluster + Cloud SQL desplegados por equipo de infra (`itmind-infrastructure`) |
| Skill | `observability/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

Langfuse es la plataforma de observabilidad agentica del proyecto. Necesita estar disponible en K8s desde el dia 1 para que todo el equipo pueda trazar sus componentes. Sin observabilidad, debuggear el pipeline RAG es casi imposible.

## Spec

Desplegar Langfuse en el cluster K8s compartido. El equipo debe poder acceder a la UI y enviar trazas desde su entorno local de desarrollo.

## Acceptance Criteria

- [x] Langfuse desplegado via Helm chart oficial (`langfuse/langfuse`) en namespace dedicado (`langfuse`)
- [x] Base de datos Langfuse en PostgreSQL (instancia Cloud SQL compartida `macro-ai-dev-db`, database `langfuse`)
- [x] Cloud SQL Auth Proxy como sidecar para conexion segura (127.0.0.1:5432, Workload Identity)
- [x] ClickHouse desplegado in-cluster como sub-chart (analytics/traces)
- [x] Redis desplegado in-cluster como sub-chart (cache/queue)
- [x] GCS bucket para blob storage (`macro-ai-dev-langfuse-blob`) en vez de MinIO
- [x] Secrets gestionados via Secret Manager + KMS (salt, encryption-key, nextauth-secret, db-password)
- [x] Langfuse UI accesible para el equipo (via port-forward en esta etapa)
- [x] Proyecto creado con API keys generadas
- [x] Variables documentadas en `.env.example`:
  - `LANGFUSE_PUBLIC_KEY`
  - `LANGFUSE_SECRET_KEY`
  - `LANGFUSE_HOST`
- [x] Verificacion: un script de test envia un trace y aparece en la UI

## Archivos creados/modificados

### enterprise-ai-platform (este repo)

| Archivo | Descripcion |
|---------|-------------|
| `infra/langfuse/namespace.yaml` | Namespace `langfuse` con labels |
| `infra/langfuse/values.yaml` | Helm values override (Cloud SQL Auth Proxy, ClickHouse, Redis, compliance) |
| `infra/langfuse/secret.template.yaml` | Template de K8s Secret con instrucciones de generacion |
| `infra/langfuse/README.md` | Instrucciones completas de deployment, verificacion y troubleshooting |
| `.env.example` | Variables Langfuse agregadas |
| `scripts/test-langfuse.py` | Script de verificacion de tracing |

### itmind-infrastructure (repo de infra)

| Archivo | Descripcion |
|---------|-------------|
| `fast/tenants/macro/workloads-ai-dev/langfuse.tf` | Secrets (nextauth, salt, encryption-key, db-connection) + GCS blob bucket |
| `fast/tenants/macro/workloads-ai-dev/iam.tf` | Workload Identity SA para Langfuse |
| `fast/tenants/macro/workloads-ai-dev/cloudsql.tf` | Database `langfuse` + user `langfuse_admin` en Cloud SQL compartido |
| `specs/deploy-dev/D-02_langfuse-helm-deploy.md` | Spec detallado del deployment Helm con sidecars, tolerations y troubleshooting |

## Dependencia de infraestructura

Esta task requiere que el equipo de infraestructura haya desplegado previamente desde el repo `itmind-infrastructure`:

| Recurso | Spec en itmind-infrastructure | Necesario para | Estado |
|---------|-------------------------------|----------------|--------|
| GKE cluster + node pools | A-02 | Namespace donde se despliega Langfuse | Done |
| Cloud SQL instancia + database `langfuse` | A-03 | Metastore PostgreSQL | Done |
| Workload Identity SA | A-04 | Autenticacion keyless Cloud SQL + GCS + Secret Manager | Done |
| Application secrets (salt, encryption-key, nextauth) | A-06 (`langfuse.tf`) | Credenciales de aplicacion | Done |
| GCS blob bucket | A-06 (`langfuse.tf`) | Event uploads y media uploads | Done |
| VPC + PSA | Networking | Conectividad Cloud SQL via Private IP | Done |

Para el deployment completo con Helm values, Cloud SQL Auth Proxy sidecars, y troubleshooting:
> `itmind-infrastructure/specs/deploy-dev/D-02_langfuse-helm-deploy.md`

## Arquitectura

```
┌─────────────────────────────────────────────────────┐
│ GKE Cluster (macro-ai-dev-gke)                      │
│                                                     │
│  ┌─ namespace: langfuse ───────────────────────────┐│
│  │                                                 ││
│  │  K8s SA: langfuse-sa                            ││
│  │    ↕ Workload Identity (A-04)                   ││
│  │  GCP SA: macro-ai-dev-langfuse-wi               ││
│  │                                                 ││
│  │  ┌───────────────┐  ┌───────────────┐           ││
│  │  │ langfuse-web  │  │ langfuse-     │           ││
│  │  │ + sql-proxy   │  │ worker        │           ││
│  │  │ (NextAuth UI) │  │ + sql-proxy   │           ││
│  │  └───────┬───────┘  └───────┬───────┘           ││
│  │          │                  │                    ││
│  │  ┌───────┴──────────────────┴───────┐            ││
│  │  │   cloud-sql-proxy sidecar        │            ││
│  │  │   → 127.0.0.1:5432              │            ││
│  │  └──────────────┬──────────────────┘            ││
│  │                 │                               ││
│  │  ┌──────────────┴──┐  ┌────────┐  ┌──────────┐ ││
│  │  │ ClickHouse      │  │ Redis  │  │ GCS Blob │ ││
│  │  │ (in-cluster)    │  │(in-cl.)│  │ Bucket   │ ││
│  │  └─────────────────┘  └────────┘  └──────────┘ ││
│  └─────────────────────────────────────────────────┘│
│                    │ PSA (10.2.224.0/20)             │
└────────────────────┼────────────────────────────────┘
                     ▼
        ┌────────────────────────┐
        │ Cloud SQL (A-03)       │
        │ macro-ai-dev-db        │
        │ ├── enterprise_ai      │
        │ ├── airflow            │
        │ └── langfuse           │
        └────────────────────────┘
```

## Decisiones de diseno

- **Langfuse self-hosted** sobre Langfuse Cloud: control total de datos, requisito bancario
- **Namespace dedicado** (`langfuse`): aislamiento de otros servicios del cluster
- **Cloud SQL compartido, database separada**: las 3 apps (enterprise_ai, airflow, langfuse) comparten la instancia `macro-ai-dev-db` pero con databases y usuarios aislados. Esto reduce costos en dev sin comprometer aislamiento logico.
- **Cloud SQL Auth Proxy sidecar** (ADR-012): TLS automatico + autenticacion via Workload Identity, sin passwords en pods
- **ClickHouse + Redis in-cluster**: componentes stateful del chart Helm. En dev, corren como sub-charts. ClickHouse tiene tolerations para el `datastore-pool`.
- **GCS blob storage nativo**: en vez de MinIO in-cluster, se usa un bucket GCS (`macro-ai-dev-langfuse-blob`) con acceso via Workload Identity
- **Telemetria deshabilitada**: requisito bancario, `telemetryEnabled: false`
- **Sign-up deshabilitado**: solo admins crean cuentas, `signUpDisabled: true`

## Out of scope

- Instrumentacion del codigo de la aplicacion (spec T1-S2-03)
- Callbacks de LangChain/LangGraph (spec T1-S2-03)
- Ingress/TLS para Langfuse UI (siguiente etapa, post port-forward)
- Dashboard custom de Langfuse (post-MVP)
