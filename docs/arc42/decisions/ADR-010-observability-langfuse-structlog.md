# ADR-010: Langfuse + structlog como Stack de Observabilidad

## Status

**Accepted**

## Date

2026-02-13

## Context

Un sistema RAG enterprise bancario requiere observabilidad completa para:
- **Debugging**: Trazar el flujo completo de una query RAG (11+ nodos de LangGraph)
- **Auditoría**: Registro de todas las consultas, respuestas, y acciones por usuario
- **Costos**: Tracking de tokens consumidos y costos por query/usuario/área
- **Calidad**: Métricas RAGAS (faithfulness, relevancy, recall)
- **Operacional**: Latencia, error rates, throughput

La observabilidad tiene dos dimensiones:
1. **Observabilidad agéntica** (traces de LLM, RAG pipeline): Langfuse
2. **Observabilidad de infraestructura** (métricas K8s, logs): Google Cloud Monitoring

## Considered Options

### Opción 1: Langfuse (agéntica) + structlog (logging) + Google Cloud Monitoring (infra)

Stack triple: cada herramienta para su dominio.

### Opción 2: LangSmith (agéntica) + structlog + GCP Monitoring

LangSmith de LangChain para traces.

### Opción 3: OpenTelemetry unificado + Grafana

Todo vía OpenTelemetry con Grafana como UI.

## Decision

**Langfuse + structlog + Google Cloud Monitoring (Opción 1).**

### Responsabilidades

| Capa | Herramienta | Qué captura |
|------|-------------|-------------|
| **Traces RAG/LLM** | Langfuse | Cada nodo del grafo LangGraph, tokens consumidos, latencia por paso, costo por query |
| **Logs aplicativos** | structlog (JSON) | Request/response logs, errores, audit events, con contexto `request_id`, `user_id`, `trace_id` |
| **Métricas infra** | Google Cloud Monitoring | CPU, memoria, latencia HTTP, error rates, K8s pod health |
| **Alertas** | Google Cloud Monitoring | Error rate > 5%, latencia p95 > 10s |
| **Evaluación calidad** | Langfuse + RAGAS | Faithfulness, relevancy, precision (offline via Airflow DAG) |

### Deployment

```
Namespace: langfuse
├── Langfuse Server (Helm chart)
├── PostgreSQL dedicado (metadata de traces)
└── UI accesible para el equipo

Namespace: enterprise-ai
├── FastAPI con structlog (JSON → stdout → Cloud Logging)
├── Langfuse SDK (@observe decorator + LangChain callback)
└── Métricas custom → Cloud Monitoring (via OpenTelemetry o cliente GCP)
```

### Instrumentación típica

```python
from langfuse.decorators import observe
import structlog

logger = structlog.get_logger()

@observe(name="retrieve")
async def retrieve_node(state: RAGState) -> dict:
    logger.info("retrieve_started", query=state["query"], user_id=state["user_id"])
    chunks = await hybrid_search(state["query_embedding"], state["query"])
    logger.info("retrieve_completed", chunks_found=len(chunks))
    return {"retrieved_chunks": chunks}
```

### Justificación sobre alternativas

| Criterio | Langfuse | LangSmith | OpenTelemetry+Grafana |
|----------|----------|-----------|----------------------|
| Self-hosted | Sí (K8s) | No (SaaS only) | Sí |
| Costo | Gratis (self-hosted) | Paid después de free tier | Gratis (OSS) |
| LLM-specific features | Sí (tokens, costos, prompts) | Sí | No (genérico) |
| LangChain integration | Callback nativo | Nativo | Requiere adaptador |
| RAGAS integration | Sí (scores como metadata) | Sí | Manual |
| Data residency | Tu cluster (compliance bancario) | USA (LangSmith servers) | Tu cluster |
| UI | Excelente para traces LLM | Excelente | Requiere dashboards custom |

**Razón crítica**: Data residency. En el sector bancario, los traces contienen queries de usuarios y respuestas con contenido bancario. Langfuse self-hosted mantiene todos los datos dentro del cluster K8s propio, cumpliendo con requisitos de compliance.

## Consequences

### Positivas

- Data residency: todos los traces en nuestro cluster (compliance bancario)
- Costo cero para Langfuse (self-hosted, sin licencia)
- Traces detallados de cada nodo LangGraph con métricas de tokens y costos
- structlog JSON compatible con Cloud Logging sin configuración adicional
- Google Cloud Monitoring para alertas y métricas de infraestructura (nativo en GKE)
- Evaluación de calidad RAGAS integrable en Langfuse

### Negativas

- Langfuse self-hosted requiere mantenimiento (PostgreSQL dedicado, upgrades)
- Tres herramientas para cubrir todo (vs una solución unificada)
- structlog no tiene UI propia (se consulta vía Cloud Logging)

## References

- [Langfuse Documentation](https://langfuse.com/docs)
- [Langfuse Self-Hosting](https://langfuse.com/docs/deployment/self-host)
- [structlog Documentation](https://www.structlog.org/)
- [RAGAS Documentation](https://docs.ragas.io/)
- Skill: `.claude/skills/observability/SKILL.md`
