# ADR-005: Airflow como Servicio de Indexación Separado

## Status

**Accepted**

## Date

2026-02-13

## Context

El pipeline de indexación (validar → chunkar → generar embeddings → almacenar en pgvector) tiene un perfil de ejecución fundamentalmente diferente al pipeline de query-time:

| Aspecto | Query-time (RAG) | Indexing |
|---------|-------------------|---------|
| Patrón | Sincrónico, request-response | Batch, asincrónico |
| Latencia | p95 < 3s | Minutos a horas |
| Frecuencia | 30 QPS pico | Bajo demanda |
| Recursos | CPU/memoria moderados | CPU/memoria intensivos (embeddings batch) |
| Trigger | Request del usuario | Manual u operador |
| Fallas | Retry inmediato, fallback | Retry con backoff, reintento de DAG |

Esta diferencia natural justifica que el indexing sea un servicio separado, incluso en un diseño monolito modular.

## Considered Options

### Opción 1: Airflow en namespace dedicado de K8s

DAGs de Airflow 3 orquestan el pipeline de indexación. La lógica de negocio (chunking, embeddings, storage) vive en `src/` como código reutilizable que Airflow importa.

### Opción 2: Background workers en FastAPI (Celery/ARQ)

Cola de tareas dentro del monolito.

### Opción 3: Cloud Functions / Cloud Run Jobs

Funciones serverless triggered por eventos.

## Decision

**Airflow 3 en namespace dedicado de K8s (Opción 1).**

### Arquitectura

```
┌─────────────────────────────────────────────────────┐
│ Namespace: airflow                                    │
│                                                       │
│  Airflow 3 (Helm chart oficial)                       │
│  ├── KubernetesExecutor (cada task = un Pod)          │
│  ├── GCS bucket sidecar (DAGs sincronizados via gsutil rsync) │
│  ├── cloud-sql-proxy sidecar (ADR-012)                │
│  └── Connections: Cloud SQL + Vertex AI (Gemini)      │
│                                                       │
│  DAGs:                                                │
│  ├── rag_indexing    (validate → chunk → embed → store)│
│  ├── cdc_sync        (OpenText CDC — post-MVP)        │
│  └── ragas_eval      (evaluación de calidad — post-MVP)│
└─────────────────────────────────────────────────────┘
         │
         │ cloud-sql-proxy → Private IP (PSA)
         ↓
┌─────────────────────────────────────────────────────┐
│ Cloud SQL for PostgreSQL 16 (ADR-012)                 │
│                                                       │
│  ├── airflow         ← metadata de Airflow            │
│  │   (DAG runs, task instances, XCom, connections)    │
│  │                                                    │
│  └── enterprise_ai   ← datos de la aplicación         │
│      (workers escriben embeddings via IndexingService) │
└─────────────────────────────────────────────────────┘
```

### Reutilización de código

```python
# dags/indexing/rag_indexing_dag.py
from src.application.services.indexing_service import IndexingService

@task
def validate_and_chunk(file_path: str):
    service = IndexingService(...)
    return service.validate_and_chunk(file_path)
```

Los DAGs orquestan; la lógica vive en `src/` y es importable tanto desde Airflow como desde FastAPI (post-MVP: upload vía API).

### Justificación sobre alternativas

| Criterio | Airflow | Celery/ARQ | Cloud Functions |
|----------|---------|------------|-----------------|
| UI de monitoreo | Airflow UI (built-in) | Flower (básico) | Cloud Console |
| Retry/backoff | Nativo por task | Configurable | Configurable |
| DAG visualization | Built-in | No | No |
| Scheduling | Cron nativo | Celery Beat | Cloud Scheduler |
| K8s native | KubernetesExecutor | Requiere workers separados | Serverless |
| Ya en el stack | Sí (requisito del proyecto) | Dependencia adicional | Vendor lock-in GCP |
| Complejidad | Media (Helm + config) | Baja | Baja |

Airflow ya es un requisito del proyecto (desplegado en K8s), con lo cual no agrega complejidad nueva. Celery añadiría otro sistema de colas. Cloud Functions generaría vendor lock-in.

## Consequences

### Positivas

- Separación natural: indexing batch no compite con query-time resources
- Airflow UI para operadores (trigger manual, monitoreo, logs)
- KubernetesExecutor: cada task es un Pod con recursos dedicados
- DAGs como código en el monorepo (sincronizados a GCS bucket)
- Lógica reutilizable desde `src/` (no duplicada)
- Retry, backoff, y SLA monitoring nativos de Airflow

### Negativas

- Airflow es un sistema complejo de operar (mitigado: equipo de infra T1 lo gestiona)
- DAGs necesitan importar `src/` lo cual requiere que el paquete esté disponible en el Pod de Airflow (imagen custom de Airflow con el paquete instalado)
- Latencia de startup de Pods con KubernetesExecutor (mitigado con Pod templates preconfigurados)
