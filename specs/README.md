# Specs - Enterprise AI Platform

> **Metodologia**: Spec-Driven Development
> **Proyecto**: Sistema RAG Enterprise Bancario
> **MVP**: Sprints 1-4 (completados) | **Post-MVP**: Sprints 5-11 + Go-Live

---

## Contexto del Proyecto

| Aspecto | Valor |
|---------|-------|
| **Equipo** | 7-8 personas (ver tracks) |
| **Deadline MVP** | < 1 mes (4 sprints semanales) |
| **Estrategia** | Hibrido: MVP con auth basica, iterar post-MVP |
| **Infra target** | Kubernetes con Helm chart "Enterprise AI Platform" |
| **Orquestacion pipelines** | Apache Airflow 3 (desplegado en K8s) |
| **Observabilidad agentica** | Langfuse (desplegado en K8s) |
| **Monitoring infra** | Google Cloud Monitoring (Cloud Operations Suite) |
| **Dev local** | Docker Compose solo PG+Redis. Langfuse y Airflow del cluster compartido |
| **Repo aplicacion** | Monorepo (backend Python + frontend Next.js + DAGs Airflow + Helm charts) |
| **Repo infraestructura** | `itmind-infrastructure` — Terraform (FAST framework) para GKE, Cloud SQL, VPC, IAM, KMS |
| **Dev approach** | Spec-driven con Claude Code |
| **OpenText** | Datos sinteticos primero, CDC via Airflow DAG despues |

### Arquitectura

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster (GKE)                           │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────────┐│
│  │   Airflow     │  │   Langfuse   │  │  Enterprise AI Platform     ││
│  │  (pipelines)  │  │  (tracing)   │  │  ┌───────────────────────┐ ││
│  │              │  │              │  │  │  FastAPI (API)         │ ││
│  │  DAGs:       │  │              │  │  │  LangGraph (RAG)       │ ││
│  │  - indexing  │  │              │  │  │  Next.js (UI)          │ ││
│  │  - cdc-sync  │  │              │  │  └───────────────────────┘ ││
│  │  - ragas-eval│  │              │  │  ┌───────────────────────┐ ││
│  └──────────────┘  └──────────────┘  │  │  PostgreSQL+pgvector   │ ││
│                                       │  │  Redis                 │ ││
│  ┌────────────────────────────────┐  │  └───────────────────────┘ ││
│  │  Google Cloud Monitoring       │  └─────────────────────────────┘│
│  │  (metricas, alertas, logging)  │                                  │
│  └────────────────────────────────┘                                  │
└──────────────────────────────────────────────────────────────────────┘
```

**Flujo de datos (MVP):**
- **Query-time (sincrono):** Usuario -> FastAPI -> LangGraph (retrieve+generate) -> streaming SSE
- **Indexing (batch):** Gaston prepara documentos -> Airflow DAG ejecuta pipeline (validate -> chunk -> embed -> store)
- **Post-MVP:** Upload via API -> trigger Airflow DAG (ver `post-mvp/`)

### Equipo y Tracks

| Track | Owner(s) | Responsabilidad |
|-------|----------|-----------------|
| **T1: Infra & Platform** | Franco, Agus | Repo, Docker Compose, K8s, Helm charts, deploy Airflow+Langfuse, CI, GCP monitoring |
| **T2: Backend & API** | Ema, Branko | FastAPI, Auth, endpoints, middleware, error handling |
| **T3: RAG Indexing & Data** | Gaston | Ingesta, chunking, embeddings, pgvector, Airflow DAGs, datos sinteticos |
| **T4: RAG Generation & Agents** | Emi, Lautaro | LangGraph, retrieval, generation, guardrails, streaming |
| **T5: Frontend** | Ema (desde Sprint 3) | Next.js, chat UI, auth UI, streaming SSE |
| **T6: Delivery & QA** | Franco (lead), equipo | Calibracion, testing, capacitacion, deploy, go-live, soporte |

### Scope MVP

- Auth basica (JWT login/logout/refresh)
- Pipeline RAG completo (indexing via Airflow DAG batch + retrieval + generation)
- Hybrid search + reranking
- LangGraph orchestration con checkpointer
- Guardrails basicos (input: prompt injection, output: faithfulness basico)
- Chat UI con streaming SSE + historial de conversaciones
- API de conversaciones (listar, reactivar)
- Airflow desplegado en K8s con DAG de indexacion batch
- Langfuse desplegado en K8s con instrumentacion basica
- Google Cloud Monitoring para metricas y alertas
- Helm chart base de Enterprise AI Platform
- Docker Compose local (PG+Redis)
- CI basico (lint + tests)

**Fuera del MVP:** Upload de documentos via API, Security Mirror, memoria episodica, guardrails avanzados, admin dashboard, CD automatico. Ver `post-mvp/`.

---

## Convenciones

### Naming
```
{TRACK}-{SPRINT}-{SEQ}_{slug}.md
```
Ejemplo: `T1-S1-03_docker-compose.md`

### Estados
| Estado | Significado |
|--------|-------------|
| `draft` | Spec en borrador, no lista para implementar |
| `pending` | Spec lista, esperando que se resuelvan dependencias |
| `in-progress` | En implementacion activa |
| `done` | Implementada y validada |
| `blocked` | Bloqueada por dependencia externa o decision pendiente |

### Reglas para agentes
1. **Leer la spec completa** antes de implementar
2. **Leer el skill referenciado** en el campo `Skill`
3. **Respetar "Out of scope"** — no implementar mas de lo pedido
4. **Verificar dependencias** — no arrancar si las specs de las que depende no estan `done`
5. **Reportar bloqueantes** — si algo impide avanzar, documentar en la spec

### Prioridades
| Nivel | Significado |
|-------|-------------|
| Critica | Bloquea a otros tracks/specs |
| Alta | Necesaria para el sprint goal |
| Media | Mejora calidad pero no bloquea |

### Estimaciones
| Talla | Tiempo |
|-------|--------|
| S | 1-2 horas |
| M | 2-4 horas |
| L | 4-8 horas |
| XL | 8+ horas |

---

## Sprint 1: Foundation (Semana 1)

> **Objetivo:** Todos los tracks arrancan en paralelo. Al final de Sprint 1, cada dev puede ejecutar su stack local (PG+Redis) y hay un esqueleto funcional. T1 arranca deploy de Airflow+Langfuse en K8s.

### Estado

| Spec | Titulo | Prioridad | Estado | Owner | Depende de |
|------|--------|-----------|--------|-------|------------|
| T1-S1-01 | Inicializar monorepo con UV | Critica | done | Franco | - |
| T1-S1-02 | Estructura de directorios hexagonal | Critica | done | Franco | T1-S1-01 |
| T1-S1-03 | Docker Compose desarrollo local | Critica | done | Agus | T1-S1-01 |
| T1-S1-04 | Configurar Alembic y schema base | Critica | done | Agus | T1-S1-02 |
| T1-S1-05 | CI basico (linting + type checking) | Alta | done | Franco | T1-S1-01 |
| T1-S1-06 | Deploy Langfuse en K8s | Critica | done | Agus | Infra: GKE + Cloud SQL (`itmind-infrastructure`) |
| T2-S1-01 | FastAPI skeleton con health checks | Critica | done | Ema | T1-S1-02 |
| T2-S1-02 | Excepciones y error handling base | Alta | done | Branko | T2-S1-01 |
| T3-S1-01 | FileValidator y document loaders | Alta | done | Gaston | T1-S1-02 |
| T3-S1-02 | Estrategia de chunking | Alta | done | Gaston | T3-S1-01 |
| T4-S1-01 | LangGraph state machine design | Alta | done | Emi | T1-S1-02 |
| T4-S1-02 | Gemini client wrapper y prompts | Alta | done | Lautaro | T1-S1-02 |

### Dependencias

```
T1-S1-01 (done) ──> T1-S1-02 (done) ──> T2-S1-01 ──> T2-S1-02
                         │
                         ├──> T1-S1-04
                         ├──> T3-S1-01 ──> T3-S1-02
                         ├──> T4-S1-01
                         └──> T4-S1-02

T1-S1-01 ──> T1-S1-03
T1-S1-01 ──> T1-S1-05

T1-S1-06 (depende de itmind-infrastructure: GKE + Cloud SQL)
```

---

## Sprint 2: Core Pipeline (Semana 2)

> **Objetivo:** Pipeline RAG funciona E2E. Auth protege endpoints. Airflow operativo en K8s.

| Spec | Titulo | Estado |
|------|--------|--------|
| T1-S2-01 | Schema SQL completo + migraciones | done |
| T1-S2-02 | Deploy Airflow en K8s | done |
| T1-S2-03 | Langfuse instrumentacion | done |
| T2-S2-01 | Auth completa (JWT + refresh) | done |
| T2-S2-02 | Middleware de seguridad global | done |
| T2-S2-03 | API de conversaciones | done |
| T3-S2-01 | Gemini embeddings + pgvector | done |
| T3-S2-02 | Indexing service reutilizable | done |
| T3-S2-03 | Airflow DAG de indexacion | done |
| T4-S2-01 | Hybrid Search (vector + BM25) | done |
| T4-S2-02 | Reranking con Vertex AI | done |
| T4-S2-03 | Nodo de generacion RAG | done|

---

## Sprint 3: Integration + UI (Semana 3)

> **Objetivo:** Sistema funciona E2E: login -> preguntar -> respuesta con streaming.

| Spec | Titulo | Estado |
|------|--------|--------|
| T1-S3-01 | Dockerfile multi-stage | done |
| T1-S3-02 | Helm chart base | done |
| T1-S3-03 | Google Cloud Monitoring | pending |
| T2-S3-01 | Endpoint chat con streaming SSE | done |
| T2-S3-02 | Tests integracion API | done |
| T3-S3-01 | Tablas OpenText sinteticas | done |
| T3-S3-02 | Testing pipeline indexacion | done |
| T4-S3-01 | Guardrail de entrada | done |
| T4-S3-02 | Integracion E2E grafo RAG | done |
| T5-S3-01 | Setup Next.js + login screen | done |
| T5-S3-02 | Chat UI con streaming SSE | done |

---

## Sprint 4: Polish + Demo MVP (Semana 4)

> **Objetivo:** MVP listo para demo. Deploy en K8s staging via Helm chart.

| Spec | Titulo | Estado |
|------|--------|--------|
| T1-S4-01 | Deploy completo K8s staging | pending |
| T1-S4-02 | Monitoring y alertas GCP | pending |
| T2-S4-01 | Rate limiting basico | done |
| T3-S4-01 | Carga dataset demo via Airflow | done |
| T3-S4-02 | Tuning de retrieval | done |
| T4-S4-01 | Guardrail de salida basico | done |
| T4-S4-02 | Demo flow + edge cases | done |
| T5-S4-01 | Sidebar historial conversaciones | done |
| T5-S4-02 | Citaciones + polish UI | done |

---

## Post-MVP: Backlog tecnico

> Backlog detallado en `post-mvp/backlog-post-mvp-v2.md`. Los 32 items (POST-01 a POST-32) se distribuyeron en Sprints 5-11.

| Bloque | Titulo | Specs | Sprint(s) |
|--------|--------|-------|-----------|
| A | Document Management (Upload via API) | POST-01 a POST-06 | 5, 7 |
| B | Security Mirror + Permisos Granulares | POST-07 a POST-10 | 6 |
| C | Memoria Avanzada | POST-11 a POST-13 | 5, 6 |
| D | Guardrails Avanzados | POST-14 a POST-16 | 9 |
| E | Observabilidad + Evaluacion | POST-17 a POST-19 | 5 |
| F | Frontend Avanzado | POST-20 a POST-23 | 5, 6, 8 |
| G | Pipelines Airflow Avanzados | POST-24 a POST-26 | 7, 10 |
| H | Hardening + Production | POST-27 a POST-32 | 7, 8, 9 |

---

## Sprint 5: Document Management Core + Observability + Memory

> **Fechas:** 16-20 Mar 2026
> **Roadmap:** IA-14 (observabilidad), IA-15 (corpus documental)
> **Objetivo:** Upload de documentos, memoria episodica, evaluacion RAGAS, audit logging, dashboard costos, feedback widget.

| Spec | Titulo | Track | Prioridad | Estado | Owner | Depende de |
|------|--------|-------|-----------|--------|-------|------------|
| T2-S5-01 | API upload documentos + validacion | T2 | Critica | pending | Ema | - |
| T2-S5-02 | Storage GCS + registro DB | T2 | Critica | pending | Branko | T2-S5-01, INFRA-S5-01 |
| T1-S5-01 | Trigger Airflow DAG desde upload | T1 | Alta | pending | Franco | T2-S5-02 |
| T3-S5-01 | DAG evaluacion RAGAS | T3 | Alta | done | Gaston | - |
| T2-S5-03 | Audit logging forense SHA-256 | T2 | Media | pending | Branko | - |
| T1-S5-02 | Dashboard costos Vertex AI | T1 | Media | pending | Agus | T1-S3-03 (done) |
| T4-S5-01 | Extraccion recuerdos episodicos | T4 | Alta | pending | Emi | - |
| T4-S5-02 | Long-term memory retrieval | T4 | Alta | done | Lautaro | T4-S5-01 |
| T4-S5-01 | Extraccion recuerdos episodicos | T4 | Alta | done | Emi | - |
| T4-S5-02 | Long-term memory retrieval | T4 | Alta | pending | Lautaro | T4-S5-01 |
| T5-S5-01 | Widget feedback thumbs up/down | T5 | Media | done | Ema | T5-S4-02 (done) |

**Infra (itmind-infrastructure):** INFRA-S5-01 (GCS bucket), INFRA-S5-02 (GCP Monitoring dashboards)

---

## Sprint 6: Security Mirror + Calibracion

> **Fechas:** 25-27 Mar 2026 (3 dias — feriados 23-24 Mar)
> **Roadmap:** IA-06 (sync xECM), IA-16+17 (calibracion), IA-19 (escenarios xECM)
> **Objetivo:** Permission resolver, filtros permisos, calibracion sistema, escenarios xECM.

| Spec | Titulo | Track | Prioridad | Estado | Owner | Depende de |
|------|--------|-------|-----------|--------|-------|------------|
| T3-S6-01 | PermissionResolver datos sinteticos | T3 | Critica | done | Gaston | T3-S3-01 (done) |
| T3-S6-02 | Recursive CTE membersia grupos | T3 | Alta | done | Gaston | T3-S6-01 |
| T4-S6-01 | Filtros permisos hybrid search | T4 | Critica | done | Emi | T3-S6-02 |
| T4-S6-02 | Sanitizacion PII en memorias | T4 | Alta | pending | Lautaro | T4-S5-01 |
| T5-S6-01 | Dark mode | T5 | Media | done | Ema | - |
| T6-S6-01 | Calibracion sistema | T6 | Critica | done | Franco, Emi | Sprint 4, [Entregable #5] |
| T6-S6-02 | Escenarios prueba xECM | T6 | Alta | done | Franco, Gaston | [Entregable #2], [Entregable #5] |

---

## Sprint 7: CDC + Document CRUD + Rate Limiting

> **Fechas:** 30 Mar - 03 Abr 2026 (3 dias — feriados 02-03 Abr)
> **Roadmap:** IA-07 (testing interno)
> **Objetivo:** CDC OpenText, CRUD documentos, rate limiting avanzado, frontend documentos, testing interno.

| Spec | Titulo | Track | Prioridad | Estado | Owner | Depende de |
|------|--------|-------|-----------|--------|-------|------------|
| T2-S7-01 | Endpoints CRUD documentos | T2 | Alta | pending | Ema | T2-S5-02 |
| T2-S7-02 | Rate limiting token bucket | T2 | Media | done | Branko | T2-S4-01 (done) |
| T3-S7-01 | CDC OpenText DAG | T3 | Critica | pending | Gaston | T3-S6-01 |
| T3-S7-02 | DAG re-indexacion batch | T3 | Media | pending | Gaston | T3-S2-03 (done) |
| T5-S7-01 | Frontend gestion documentos | T5 | Alta | pending | Ema | T2-S7-01, T1-S5-01 |
| T6-S7-01 | Testing interno plataforma | T6 | Alta | pending | Franco, team | T6-S6-01 |

**Infra:** INFRA-S7-01 (Pub/Sub CDC OpenText)

---

## Sprint 8: Frontend Avanzado + CD Pipeline + QAS Transport

> **Fechas:** 06-10 Abr 2026
> **Roadmap:** IA-18 (testing DEV), IA-20 (validacion xECM), IA-21 (transporte QAS)
> **Objetivo:** Admin dashboard, CD pipeline, Helm multi-env, pruebas integracion, transporte QAS.

| Spec | Titulo | Track | Prioridad | Estado | Owner | Depende de |
|------|--------|-------|-----------|--------|-------|------------|
| T1-S8-01 | CD automatico Helm upgrade | T1 | Alta | pending | Franco | T1-S4-01 (done) |
| T1-S8-02 | Helm multi-entorno | T1 | Alta | pending | Agus | T1-S3-02 (done) |
| T5-S8-01 | Admin dashboard | T5 | Alta | pending | Ema | T5-S7-01, T1-S5-02 |
| T5-S8-02 | Vista estado pipelines | T5 | Media | pending | Ema | T5-S7-01 |
| T6-S8-01 | Pruebas integracion DEV | T6 | Alta | pending | Franco, Branko | T6-S7-01 |
| T6-S8-02 | Validacion datos reales xECM | T6 | Alta | pending | Franco, Gaston | T6-S6-02, [Entregable #1] |
| T6-S8-03 | Transporte DEV a QAS | T6 | Critica | pending | Franco, Agus | T6-S8-01, T6-S8-02 |

**Infra:** INFRA-S8-01 (CD trigger), INFRA-S8-02 (QAS environment scaffold)

---

## Sprint 9: Guardrails Avanzados + Hardening

> **Fechas:** 13-17 Abr 2026
> **Roadmap:** IA-23 (QAS testing), IA-22 (capacitacion), IA-26 (seguridad)
> **Objetivo:** PII detection, faithfulness, topic control, pentesting, load testing, pruebas QAS.

| Spec | Titulo | Track | Prioridad | Estado | Owner | Depende de |
|------|--------|-------|-----------|--------|-------|------------|
| T4-S9-01 | PII detection output | T4 | Critica | pending | Emi | T4-S4-01 (done) |
| T4-S9-02 | Faithfulness scoring | T4 | Alta | pending | Lautaro | - |
| T4-S9-03 | Topic control bancario | T4 | Alta | pending | Emi | T4-S3-01 (done) |
| T2-S9-01 | Pentesting OWASP | T2 | Critica | pending | Branko | - |
| T1-S9-01 | Load testing K6/Locust | T1 | Alta | pending | Agus | T1-S4-01 (done) |
| T3-S9-01 | Document versioning | T3 | Media | pending | Gaston | T3-S7-01 |
| T6-S9-01 | Pruebas QAS | T6 | Critica | pending | Franco, team | T6-S8-03 |
| T6-S9-02 | Capacitacion key users | T6 | Alta | pending | Franco | T6-S8-03 |

---

## Sprint 10: Pre-Production + GDPR + Config Produccion

> **Fechas:** 20-24 Abr 2026
> **Roadmap:** IA-24-28 (estabilizacion QAS, config PRD, seguridad pre-prod)
> **Objetivo:** Config produccion, GDPR DAG, estabilizacion QAS, seguridad pre-prod, testing integrado.

| Spec | Titulo | Track | Prioridad | Estado | Owner | Depende de |
|------|--------|-------|-----------|--------|-------|------------|
| T1-S10-01 | Config ambiente produccion | T1 | Critica | pending | Franco | T1-S8-02 |
| T3-S10-01 | DAG GDPR forget-user | T3 | Alta | pending | Gaston | - |
| T6-S10-01 | Estabilizacion QAS | T6 | Alta | pending | team | T6-S9-01 |
| T6-S10-02 | Seguridad filtros avanzados | T6 | Critica | pending | Emi, Lautaro | T4-S9-01, T4-S9-02, T4-S9-03 |
| T6-S10-03 | Seguridad permisos documentales | T6 | Critica | pending | Gaston, Emi | T4-S6-01, T3-S7-01, [Entregable #6] |
| T6-S10-04 | Testing integrado pre-produccion | T6 | Critica | pending | Franco, team | T6-S10-01..03, T2-S9-01, T1-S9-01 |

**Infra:** INFRA-S10-01 (PRD stage), INFRA-S10-02 (IAM), INFRA-S10-03 (secrets), INFRA-S10-04 (monitoring)

---

## Sprint 11: Go-Live + Soporte (27 Abr - 08 May)

> **Fechas:** 27 Abr - 08 May 2026 (2 semanas, feriado 01 May)
> **Roadmap:** IA-29 a IA-33
> **Objetivo:** Deploy produccion, UAT, capacitacion, go-live, monitoreo.

| Spec | Titulo | Track | Prioridad | Estado | Owner | Depende de |
|------|--------|-------|-----------|--------|-------|------------|
| T6-S11-01 | Deploy produccion | T6 | Critica | pending | Franco, Agus | T6-S10-04, T1-S10-01 |
| T6-S11-02 | UAT key users | T6 | Critica | pending | Franco, team | T6-S11-01 |
| T6-S11-03 | Capacitacion usuarios finales | T6 | Alta | pending | Franco | T6-S11-02 |
| T6-S11-04 | Go-Live | T6 | Critica | pending | Franco | T6-S11-02, T6-S11-03, [Aprobacion banco] |
| T6-S11-05 | Monitoreo post go-live | T6 | Critica | pending | Franco, Agus, team | T6-S11-04 |

**Infra:** INFRA-S11-01 (PRD deploy validation), INFRA-S11-02 (Airflow + Langfuse PRD Helm)

---

## Post-Sprint: Soporte y Cierre (11+ May)

> **Roadmap:** IA-34 a IA-36

| Spec | Titulo | Track | Prioridad | Estado | Owner | Depende de |
|------|--------|-------|-----------|--------|-------|------------|
| T6-PS-01 | Soporte continuo | T6 | Alta | pending | Franco, team | T6-S11-05 |
| T6-PS-02 | Ajuste fino RAG | T6 | Alta | pending | Emi, Lautaro | T6-PS-01 |
| T6-PS-03 | Informe cierre proyecto | T6 | Alta | pending | Franco | T6-PS-02 |

---

## Resumen de Sprints Post-MVP

| Sprint | Fechas | Foco | Features | Delivery | Infra | Total |
|--------|--------|------|----------|----------|-------|-------|
| **5** | 16-20 Mar | Doc Mgmt + Observability + Memory | 9 | 0 | 2 | 11 |
| **6** | 25-27 Mar | Security Mirror + Calibracion | 5 | 2 | 0 | 7 |
| **7** | 30 Mar-03 Abr | CDC + CRUD + Rate Limiting | 5 | 1 | 1 | 7 |
| **8** | 06-10 Abr | Frontend + CD + QAS Transport | 4 | 3 | 2 | 9 |
| **9** | 13-17 Abr | Guardrails + Hardening | 6 | 2 | 0 | 8 |
| **10** | 20-24 Abr | Pre-Production + GDPR | 2 | 4 | 4 | 10 |
| **11** | 27 Abr-08 May | Go-Live + Soporte | 0 | 5 | 2 | 7 |
| **Post** | 11+ May | Soporte + Cierre | 0 | 3 | 0 | 3 |
| | | **Totales** | **31** | **20** | **11** | **62** |

---

## Dependencias entre Tracks (MVP — Sprints 1-4)

```
Sprint 1:
  T1 (repo+docker+alembic) ──────> T2 (backend), T3 (indexing code), T4 (agents)
  T1 (Langfuse K8s) ──────────────> Equipo completo (tracing)
                                    [T2, T3, T4 arrancan en paralelo desde dia 2-3]

Sprint 2:
  T1 (schema SQL) ──────> T3 (embeddings+pgvector), T4 (search)
  T1 (Airflow K8s) ─────> T3 (DAG indexacion)
  T3 (IndexingService) ──> T3 (DAG indexacion)
  T3 (embeddings) ────────> T4 (search)  [necesita datos para buscar]

Sprint 3:
  T2 (API chat) + T4 (grafo) ──> T5 (frontend chat)
  T4 (todos nodos) ─────────────> T4 (integracion E2E)

Sprint 4:
  T1 (Helm chart) ──> T1 (deploy staging)
  T3 (dataset via Airflow) ──> T4 (demo) ──> DEMO MVP
```

## Dependencias entre Tracks (Post-MVP — Sprints 5-11)

```
Sprint 5:
  T2 (upload API) ──> T2 (storage GCS) ──> T1 (trigger DAG)
  T4 (memory extract) ──> T4 (memory retrieval)
  INFRA-S5-01 (GCS) ──> T2-S5-02

Sprint 6:
  T3 (PermResolver) ──> T3 (CTE) ──> T4 (permission filters)
  T6 (calibracion) ──> T6 (testing Sprint 7)

Sprint 7:
  T2 (CRUD docs) ──> T5 (document UI)
  T6 (testing interno) ──> T6 (integracion DEV Sprint 8)

Sprint 8:
  T6 (integracion + validacion xECM) ──> T6 (transporte QAS)
  T6 (transporte QAS) ──> T6 (pruebas QAS Sprint 9)

Sprint 9:
  T4 (guardrails avanzados) ──> T6 (seguridad pre-prod Sprint 10)
  T6 (pruebas QAS) ──> T6 (estabilizacion Sprint 10)

Sprint 10:
  T6 (estabilizacion + seguridad + testing) ──> T6 (deploy produccion Sprint 11)
  INFRA-S10 (PRD infra) ──> T1-S10-01 (config PRD)

Sprint 11:
  T6 (deploy PRD) ──> T6 (UAT) ──> T6 (Go-Live) ──> T6 (monitoreo)
```

---

## Dependencias externas (Entregables del banco)

| Entregable | Requerido por | Bloquea specs |
|------------|---------------|---------------|
| #1: OpenText CS operativo | 10/03 | T6-S8-02 (validacion xECM) |
| #2: xECM config (carpetas, roles) | 20/03 | T6-S6-02, T3-S6-01 |
| #3: Corpus documental | 12/03 | T3-S5-01 (RAGAS eval) |
| #5: Escenarios de prueba | 17/03 | T6-S6-01 (calibracion), T6-S6-02 |
| #6: Permisos documentales xECM | 11/04 | T6-S10-03 (seguridad permisos) |
| Aprobacion banco | Pre Go-Live | T6-S11-04 (Go-Live) |

---

## Carga de trabajo por persona por Sprint

| Sprint | Franco (T1) | Agus (T1) | Ema (T2/T5) | Branko (T2) | Gaston (T3) | Emi (T4) | Lautaro (T4) |
|--------|-------------|-----------|-------------|-------------|-------------|----------|---------------|
| **S1** | Repo, CI, Docker | Langfuse K8s, Alembic | FastAPI skeleton | Error handling | Loaders, chunking | LangGraph design | Gemini client |
| **S2** | Schema SQL | Airflow K8s, Langfuse instr. | Auth, API conv. | Middleware seg. | Embeddings, DAG indexacion | Hybrid search, generation | Reranking |
| **S3** | Dockerfile | Helm chart, GCP monitoring | **Frontend**: login+chat | API chat SSE, tests integracion | OpenText synth, tests DAG | Integration E2E | Guardrail input |
| **S4** | Deploy staging | GCP alertas | **Frontend**: historial+polish | Rate limiting | Dataset demo, tuning | Demo flow | Guardrail output |
| **S5** | DAG trigger | GCP dashboard | Upload API + Feedback | Storage + Audit log | RAGAS DAG | Memory extract | Memory retrieval |
| **S6** | Calibracion (T6) | - | Dark mode | - | PermResolver + CTE | Search filters + Calibracion (T6) | PII sanitize mem |
| **S7** | Testing (T6) | - | Doc CRUD + Doc UI | Rate limiting | CDC DAG + Re-index DAG | - | - |
| **S8** | CD pipeline + Testing (T6) | Helm multi-env + QAS (T6) | Admin dashboard + Pipeline view | Testing DEV (T6) | xECM validation (T6) | - | - |
| **S9** | - | Load testing | - | Pentesting OWASP | Doc versioning | PII output + Topic ctrl | Faithfulness |
| **S10** | Config PRD + Pre-prod (T6) | - | - | - | GDPR DAG + Perms (T6) | Seguridad filtros (T6) | Seguridad filtros (T6) |
| **S11** | Deploy PRD + Go-Live (T6) | Deploy PRD (T6) | UAT soporte (T6) | - | - | Monitoreo (T6) | Monitoreo (T6) |

---

## Metricas de Exito del MVP

| Metrica | Target |
|---------|--------|
| Pipeline E2E funcional | Login -> preguntar -> respuesta con citaciones + streaming |
| Latencia p95 query | < 5 segundos |
| Documentos indexados | 10-20 docs bancarios via Airflow DAG |
| Test coverage | > 70% en modulos core |
| Uptime staging | Sistema estable para demo |
| Guardrail input | Bloquea prompt injection basico |
| Guardrail output | Detecta datos sensibles en respuesta |
| Streaming | Tokens aparecen incrementalmente en UI |
| Airflow | DAG de indexacion ejecuta exitosamente |
| Langfuse | Trazas visibles de cada query RAG |
| Helm | `helm install` despliega todo el stack |
| GCP Monitoring | Dashboard con metricas basicas visibles |

## Metricas de Exito Post-MVP (Produccion)

| Metrica | Target |
|---------|--------|
| Latencia p95 query | < 5 segundos bajo 50 usuarios concurrentes |
| Faithfulness RAGAS | > 0.8 con datos reales |
| Error rate | < 1% en endpoints principales |
| PII detection | < 5% false positives |
| Uptime produccion | > 99.5% primer mes |
| Pentesting | 0 vulnerabilidades criticas/altas sin remediar |
| Go-Live | Aprobacion del banco obtenida |
| Soporte | < 1h SLA para incidencias criticas |
