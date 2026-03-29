# Architecture Documentation (arc42)

> **Framework**: [arc42](https://arc42.org/) — Template for Software Architecture Documentation
> **Proyecto**: Enterprise AI Platform — Sistema RAG Enterprise Bancario

---

## Secciones

| # | Sección | Documento | Estado |
|---|---------|-----------|--------|
| 04 | **Solution Strategy** | [04_solution_strategy.md](04_solution_strategy.md) | Completo |
| 07 | **Deployment View** | [07_deployment_view.md](07_deployment_view.md) | Completo |
| 09 | **Architecture Decisions** | [decisions/](decisions/) (12 ADRs) | Completo |

### Secciones pendientes

| # | Sección | Descripción |
|---|---------|-------------|
| 01 | Introduction and Goals | Requisitos, stakeholders, quality goals |
| 02 | Constraints | Restricciones técnicas, organizacionales, convenciones |
| 03 | Context and Scope | Diagrama de contexto C4 Level 1 |
| 05 | Building Block View | Diagrama C4 Level 2-3, módulos internos |
| 06 | Runtime View | Flujos dinámicos (query RAG, indexación, auth) |
| 08 | Cross-cutting Concepts | Seguridad, observabilidad, error handling, persistencia |
| 10 | Quality Requirements | Quality tree, escenarios de calidad |
| 11 | Risks and Technical Debt | Riesgos conocidos, deuda técnica |
| 12 | Glossary | Términos del dominio bancario y técnico |

---

## Architecture Decisions (ADRs)

> **Formato**: [MADR](https://adr.github.io/madr/) (Markdown Architectural Decision Records)
> **Referencia**: [arc42 Section 9](https://docs.arc42.org/section-9/)

| ADR | Título | Estado | Fecha |
|-----|--------|--------|-------|
| [001](decisions/ADR-001-modular-monolith.md) | Monolito Modular Hexagonal como estilo arquitectónico | Accepted | 2026-02-13 |
| [002](decisions/ADR-002-langgraph-embedded-library.md) | LangGraph como librería embebida en FastAPI | Accepted | 2026-02-13 |
| [003](decisions/ADR-003-frontend-backend-communication.md) | REST + SSE como protocolo frontend-backend | Accepted | 2026-02-13 |
| [004](decisions/ADR-004-unified-postgresql-pgvector.md) | PostgreSQL + pgvector como base de datos unificada | Accepted | 2026-02-13 |
| [005](decisions/ADR-005-airflow-separated-indexing.md) | Airflow como servicio de indexación separado | Accepted | 2026-02-13 |
| [006](decisions/ADR-006-jwt-httponly-auth.md) | JWT con HTTPOnly cookies y refresh tokens | Accepted | 2026-02-13 |
| [007](decisions/ADR-007-hybrid-search-rrf.md) | Búsqueda híbrida Vector + BM25 + RRF | Accepted | 2026-02-13 |
| [008](decisions/ADR-008-google-ecosystem-unified.md) | Ecosistema Google unificado (Gemini + Vertex AI) | Accepted | 2026-02-13 |
| [009](decisions/ADR-009-halfvec-768-storage.md) | halfvec(768) para almacenamiento vectorial | Accepted | 2026-02-13 |
| [010](decisions/ADR-010-observability-langfuse-structlog.md) | Langfuse + structlog como stack de observabilidad | Accepted | 2026-02-13 |
| [011](decisions/ADR-011-python-root-layout.md) | Backend Python en la raíz del monorepo | Accepted | 2026-02-18 |
| [012](decisions/ADR-012-cloud-sql-managed.md) | Cloud SQL managed en lugar de PostgreSQL in-cluster | Accepted | 2026-02-19 |

---

## Repositorios relacionados

| Repositorio | Contenido | Relacion |
|-------------|-----------|----------|
| `enterprise-ai-platform` (este repo) | Aplicacion: FastAPI, LangGraph, Next.js, Helm charts, Airflow DAGs | Codigo de aplicacion y despliegue |
| `itmind-infrastructure` | Terraform (FAST): GKE, Cloud SQL, VPC, IAM, KMS, Secret Manager | Infraestructura GCP base sobre la que se despliega la aplicacion |

Las dependencias de infraestructura estan documentadas en [ADR-012](decisions/ADR-012-cloud-sql-managed.md) y en la [Deployment View](07_deployment_view.md).

---

### Convenciones ADR

- **Status**: `Proposed` → `Accepted` → `Deprecated` / `Superseded by ADR-NNN`
- **Numeración**: Secuencial, nunca se reutiliza un número
- **Inmutabilidad**: Un ADR aceptado no se modifica; se crea uno nuevo que lo reemplaza
- **Contexto**: Cada ADR debe poder leerse de forma independiente
