# ADR-012: Cloud SQL Managed en lugar de PostgreSQL in-cluster

## Status

**Accepted**

## Date

2026-02-19

## Context

La [Section 7 — Deployment View](../07_deployment_view.md) original describe PostgreSQL como un StatefulSet con bitnami sub-chart dentro del namespace `enterprise-ai` del cluster GKE. Sin embargo, el despliegue se realiza en la infraestructura de Banco Macro, un tenant bancario con requisitos estrictos de compliance, auditoría y operación.

El equipo de infraestructura (T1) gestiona los recursos de GCP via Terraform (FAST framework). Necesitamos decidir si PostgreSQL se despliega como:
- StatefulSet self-managed dentro de GKE (bitnami Helm chart)
- Cloud SQL for PostgreSQL (servicio managed de Google)

Esta decisión afecta a las tres bases de datos del proyecto: `enterprise_ai` (ADR-004), `langfuse` (ADR-010) y `airflow` (ADR-005).

**Nota**: Redis para session cache (ADR-006) permanece como Deployment in-cluster via bitnami sub-chart. Redis almacena solo datos efímeros de sesión sin requisitos de compliance para persistencia.

## Considered Options

### Opción 1: Cloud SQL for PostgreSQL 16 (managed)

Instancia Cloud SQL con IP privada via Private Service Access (PSA), CMEK, backups automáticos.

### Opción 2: StatefulSet bitnami/postgresql (self-managed)

PostgreSQL como sub-chart Helm dentro del namespace `enterprise-ai` del cluster GKE.

## Decision

**Cloud SQL for PostgreSQL 16 con conexión via Cloud SQL Auth Proxy + Workload Identity (Opción 1).**

### Justificación

| Criterio | Cloud SQL (managed) | StatefulSet (self-managed) |
|----------|--------------------|-----------------------------|
| **Backups** | Automáticos con PITR, 7 días retención | Manual (velero/pg_dump) o script custom |
| **HA** | REGIONAL failover automático (1 flag) | Requiere configuración manual (pgpool/patroni) |
| **CMEK** | Nativo (`encryption_key_name`) | Requiere PVC encryption custom |
| **Patching** | Maintenance windows automáticas | Manual: actualizar imagen, rolling restart |
| **SLA** | 99.95% (regional), 99.99% con Gemini | Ninguno (self-managed) |
| **TLS** | `ENCRYPTED_ONLY` nativo | Configuración manual de certificados |
| **Audit** | Cloud SQL audit logs + database flags | Solo database flags |
| **Monitoring** | Cloud SQL Insights (query-level) | Requiere pg_stat_statements + Prometheus |
| **Scaling** | Cambiar tier sin downtime (vertical) | Recrear StatefulSet |
| **Compliance** | SOC 2, ISO 27001, PCI DSS (inherente) | Responsabilidad del operador |
| **Costo (dev)** | ~$100-150/mes (db-custom-4-16384) | ~$50-80/mes (solo compute) |
| **Costo (prod)** | ~$250-400/mes (regional HA) | ~$100-200/mes + ops overhead |
| **Operación** | Google la opera | El equipo T1 la opera |

**Razón decisiva**: En el sector bancario, la compliance y auditabilidad son requisitos no negociables. Cloud SQL provee SOC 2, ISO 27001 y PCI DSS de forma inherente. Con StatefulSet, estas certificaciones son responsabilidad del operador, requiriendo documentación adicional y esfuerzo operacional significativo.

### Arquitectura de conexión

```
┌─── GKE Pod (backend) ──────────────────────────────────┐
│                                                        │
│  ┌──────────────┐    ┌────────────────────────────────┐│
│  │  FastAPI     │    │  Cloud SQL Auth Proxy          ││
│  │  container   │───►│  sidecar container             ││
│  │              │    │                                ││
│  │  conecta a   │    │  - Workload Identity (sin keys)││
│  │  localhost   │    │  - TLS automático              ││
│  │  :5432       │    │  - Connection management       ││
│  └──────────────┘    └───────────┬────────────────────┘│
│                                  │                     │
└──────────────────────────────────┼─────────────────────┘
                                   │ Private IP (PSA)
                                   │ 10.2.224.0/20
                                   ▼
                    ┌───────────────────────────────┐
                    │  Cloud SQL for PostgreSQL 16  │
                    │  macro-ai-dev-db              │
                    │                               │
                    │  ├── enterprise_ai (ADR-004)  │
                    │  │   pgvector + relational    │
                    │  │   + BM25 + LangGraph       │
                    │  │                            │
                    │  ├── langfuse (ADR-010)       │
                    │  │   trace metadata           │
                    │  │                            │
                    │  └── airflow (ADR-005)        │
                    │      DAG runs, task instances,│
                    │      XCom, connections        │
                    │                               │
                    │  CMEK: macro-data-key         │
                    │  TLS: ENCRYPTED_ONLY          │
                    └───────────────────────────────┘
```

### Cloud SQL Auth Proxy + Workload Identity

El patrón de conexión desde GKE usa Cloud SQL Auth Proxy como sidecar:

1. **Sin passwords para el proxy**: El Auth Proxy se autentica contra Cloud SQL usando Workload Identity (IAM), no passwords.
2. **Passwords PostgreSQL via Secret Manager**: La autenticación de usuario PostgreSQL (`enterprise_ai_admin`, `langfuse_admin`, `airflow_admin`) usa passwords almacenados en Secret Manager, accedidos desde los pods via Workload Identity.
3. **TLS automático**: El Auth Proxy negocia TLS automáticamente. La aplicación conecta a `localhost:5432` sin configurar TLS.
4. **Audit trail completo**: Todas las conexiones quedan registradas en Cloud SQL audit logs + IAM audit logs.

```yaml
# Ejemplo: sidecar en deployment backend (Helm chart)
containers:
  - name: backend
    image: gcr.io/proyecto/backend:v1.0
    env:
      - name: DATABASE_URL
        value: "postgresql://enterprise_ai_admin:$(DB_PASSWORD)@localhost:5432/enterprise_ai"
  - name: cloud-sql-proxy
    image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2
    args:
      - "--structured-logs"
      - "--auto-iam-authn"
      - "$(INSTANCE_CONNECTION_NAME)"
    securityContext:
      runAsNonRoot: true
```

### ¿Por qué no Cloud SQL Auth Proxy para Redis?

Redis en esta arquitectura es exclusivamente cache de sesión (ADR-006). No almacena datos regulados, no requiere PITR ni backups, y no tiene requisitos de compliance bancaria. Un Deployment bitnami/redis in-cluster es suficiente y más simple. Si en el futuro Redis almacena datos regulados, se evaluará Memorystore.

## Consequences

### Positivas

- Compliance automática: SOC 2, ISO 27001, PCI DSS inherentes a Cloud SQL
- Backups automáticos con PITR sin intervención del equipo
- HA regional activable con un flag (`availability_type = "REGIONAL"`)
- CMEK nativo con una sola línea de configuración
- Cloud SQL Insights para debugging de queries sin pg_stat_statements manual
- Maintenance windows automáticas: parches de seguridad sin downtime manual
- Scaling vertical sin downtime (cambiar tier)
- Infrastructure as Code: toda la configuración gestionada via Terraform

### Negativas

- Costo mayor (~$50-100/mes más que self-managed en dev)
- Menor control sobre configuración PostgreSQL (no todos los parámetros son configurables via database flags)
- Cloud SQL Auth Proxy agrega un container sidecar por pod (overhead mínimo: ~10MB RAM)
- Requiere PSA configurado en la VPC (ya provisionado en networking stage)
- Vendor lock-in parcial con Cloud SQL (mitigado: PostgreSQL estándar, migrable con pg_dump/pg_restore)

## References

- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/connect-auth-proxy)
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [ADR-004: PostgreSQL + pgvector unificado](ADR-004-unified-postgresql-pgvector.md)
- [ADR-009: halfvec(768)](ADR-009-halfvec-768-storage.md)
- [ADR-005: Airflow separado](ADR-005-airflow-separated-indexing.md)
- [ADR-010: Langfuse + structlog](ADR-010-observability-langfuse-structlog.md)
- Infrastructure spec: `itmind-infrastructure/specs/workloads-dev/A-03_ai-cloudsql-secrets.md`
