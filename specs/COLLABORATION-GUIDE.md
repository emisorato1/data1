# Guia de Colaboracion Spec-Driven con GitHub

> **Proyecto:** Sistema RAG Enterprise Bancario
> **Metodologia:** Spec-Driven Development + Vibecoding
> **Equipo:** 7-8 personas, 5 tracks, 4 sprints

---

## 1. Tabla Maestra de Specs

### Sprint 1: Foundation

| Spec ID | Titulo | Track | Owner | Prioridad | Estado | Depende de | Bloquea a | Ruta Critica | Rama sugerida |
|---------|--------|-------|-------|-----------|--------|------------|-----------|:------------:|---------------|
| T1-S1-01 | Init monorepo UV | T1 | Franco | Critica | done | - | T1-S1-02, T1-S1-03, T1-S1-05 | **Si** | `feat/T1-S1-01_init-monorepo` |
| T1-S1-02 | Estructura directorios hexagonal | T1 | Franco | Critica | done | T1-S1-01 | T1-S1-04, T2-S1-01, T3-S1-01, T4-S1-01, T4-S1-02 | **Si** | `feat/T1-S1-02_directory-structure` |
| T1-S1-03 | Docker Compose dev local | T1 | Agus | Critica | done | T1-S1-01 | T1-S1-04, T2-S1-01, T3-S1-01 | **Si** | `feat/T1-S1-03_docker-compose` |
| T1-S1-04 | Alembic + schema base | T1 | Agus | Critica | done | T1-S1-02, T1-S1-03 | T1-S2-01, T2-S2-01 | **Si** | `feat/T1-S1-04_alembic-schema` |
| T1-S1-05 | CI linting + type checking | T1 | Franco | Alta | done | T1-S1-01 | - | No | `feat/T1-S1-05_ci-linting` |
| T1-S1-06 | Deploy Langfuse K8s | T1 | Agus | Critica | done | Externo (itmind-infra) | T1-S2-03 | No | `feat/T1-S1-06_langfuse-k8s` |
| T2-S1-01 | FastAPI skeleton | T2 | Ema | Critica | done | T1-S1-02, T1-S1-03 | T2-S1-02, T2-S2-01, T2-S2-02, T2-S2-03 | **Si** | `feat/T2-S1-01_fastapi-skeleton` |
| T2-S1-02 | Error handling base | T2 | Branko | Alta | done | T2-S1-01 | Todos los tracks | No | `feat/T2-S1-02_error-handling` |
| T3-S1-01 | FileValidator + doc loaders | T3 | Gaston | Alta | done | T1-S1-02 | T3-S1-02 | **Si** | `feat/T3-S1-01_file-validator` |
| T3-S1-02 | Chunking strategy | T3 | Gaston | Alta | done | T3-S1-01 | T3-S2-01 | **Si** | `feat/T3-S1-02_chunking-strategy` |
| T4-S1-01 | LangGraph state machine | T4 | Emi | Alta | done | T1-S1-02 | T4-S2-03, T4-S3-01, T4-S3-02 | **Si** | `feat/T4-S1-01_langgraph-state` |
| T4-S1-02 | Gemini client wrapper | T4 | Lautaro | Alta | done | T1-S1-02 | T4-S2-03, T3-S2-01 | **Si** | `feat/T4-S1-02_gemini-client` |

### Sprint 2: Core Pipeline

| Spec ID | Titulo | Track | Owner | Prioridad | Estado | Depende de | Bloquea a | Ruta Critica | Rama sugerida |
|---------|--------|-------|-------|-----------|--------|------------|-----------|:------------:|---------------|
| T1-S2-01 | Schema SQL completo | T1 | Franco, Agus | Critica | done | T1-S1-04 | T3-S2-01, T3-S3-01, T4-S2-01 | **Si** | `feat/T1-S2-01_sql-schema` |
| T1-S2-02 | Deploy Airflow K8s | T1 | Franco, Agus | Critica | done | Externo (itmind-infra) | T3-S2-03 | **Si** | `feat/T1-S2-02_airflow-k8s` |
| T1-S2-03 | Langfuse instrumentation | T1 | Agus | Alta | done | T1-S1-06 | T1-S3-03 | No | `feat/T1-S2-03_langfuse-instrumentation` |
| T2-S2-01 | Auth JWT + refresh | T2 | Ema, Branko | Critica | done | T1-S1-04, T2-S1-01 | T2-S2-03, T2-S3-01, T2-S3-02, T2-S4-01, T5-S3-01 | **Si** | `feat/T2-S2-01_auth-jwt` |
| T2-S2-02 | Security middleware | T2 | Branko | Alta | done | T2-S1-01 | - | No | `feat/T2-S2-02_security-middleware` |
| T2-S2-03 | API conversaciones | T2 | Ema | Alta | done | T2-S2-01, T2-S1-01 | T2-S3-02, T5-S4-01 | No | `feat/T2-S2-03_conversations-api` |
| T3-S2-01 | Embeddings + pgvector | T3 | Gaston | Critica | done | T1-S2-01, T3-S1-02, T4-S1-02 | T3-S2-02, T4-S2-01 | **Si** | `feat/T3-S2-01_embeddings-pgvector` |
| T3-S2-02 | Indexing service | T3 | Gaston | Alta | done | T3-S2-01 | T3-S2-03 | **Si** | `feat/T3-S2-02_indexing-service` |
| T3-S2-03 | Airflow DAG indexing | T3 | Gaston | Critica | done | T1-S2-02, T3-S2-02 | T3-S3-02, T3-S4-01 | **Si** | `feat/T3-S2-03_airflow-dag-indexing` |
| T4-S2-01 | Hybrid search (vector+BM25) | T4 | Emi, Lautaro | Critica | done | T1-S2-01, T3-S2-01 | T4-S2-02, T4-S3-02 | **Si** | `feat/T4-S2-01_hybrid-search` |
| T4-S2-02 | Reranking Vertex AI | T4 | Lautaro | Alta | done | T4-S2-01 | T4-S3-02 | **Si** | `feat/T4-S2-02_reranking` |
| T4-S2-03 | Generation node | T4 | Emi | Critica | done | T4-S1-01, T4-S1-02 | T2-S3-01, T4-S3-02 | **Si** | `feat/T4-S2-03_generation-node` |

### Sprint 3: Integration + UI

| Spec ID | Titulo | Track | Owner | Prioridad | Estado | Depende de | Bloquea a | Ruta Critica | Rama sugerida |
|---------|--------|-------|-------|-----------|--------|------------|-----------|:------------:|---------------|
| T1-S3-01 | Dockerfile multi-stage | T1 | Franco | Alta | done | - | T1-S4-01 | **Si** | `feat/T1-S3-01_dockerfile` |
| T1-S3-02 | Helm chart base | T1 | Agus | Critica | done | - | T1-S4-01 | **Si** | `feat/T1-S3-02_helm-chart` |
| T1-S3-03 | Google Cloud Monitoring | T1 | Agus | Media | pending | T1-S2-03 | T1-S4-02 | No | `feat/T1-S3-03_gcp-monitoring` |
| T2-S3-01 | Chat SSE endpoint | T2 | Branko | Critica | done | T4-S2-03, T2-S2-01 | T5-S3-02 | **Si** | `feat/T2-S3-01_chat-sse-endpoint` |
| T2-S3-02 | API integration tests | T2 | Branko | Alta | done | T2-S2-01, T2-S2-03 | - | No | `feat/T2-S3-02_integration-tests` |
| T3-S3-01 | OpenText synthetic tables | T3 | Gaston | Media | done | T1-S2-01 | - (post-MVP) | No | `feat/T3-S3-01_opentext-synthetic` |
| T3-S3-02 | Indexing pipeline tests | T3 | Gaston | Alta | done | T3-S2-03 | - | No | `feat/T3-S3-02_indexing-tests` |
| T4-S3-01 | Input guardrail | T4 | Lautaro | Alta | done | T4-S1-01 | T4-S3-02 | **Si** | `feat/T4-S3-01_input-guardrail` |
| T4-S3-02 | E2E graph integration | T4 | Emi | Critica | done | T4-S2-01, T4-S2-02, T4-S2-03, T4-S3-01 | T4-S4-01, T4-S4-02 | **Si** | `feat/T4-S3-02_e2e-integration` |
| T5-S3-01 | Next.js setup + login | T5 | Ema | Alta | done | T2-S2-01 | T5-S3-02 | **Si** | `feat/T5-S3-01_nextjs-login` |
| T5-S3-02 | Chat UI streaming SSE | T5 | Ema | Critica | done | T5-S3-01, T2-S3-01 | T5-S4-02 | **Si** | `feat/T5-S3-02_chat-ui` |

### Sprint 4: Polish + Demo MVP

| Spec ID | Titulo | Track | Owner | Prioridad | Estado | Depende de | Bloquea a | Ruta Critica | Rama sugerida |
|---------|--------|-------|-------|-----------|--------|------------|-----------|:------------:|---------------|
| T1-S4-01 | Deploy K8s staging | T1 | Franco, Agus | Critica | pending | T1-S3-01, T1-S3-02 | **DEMO MVP** | **Si** | `feat/T1-S4-01_deploy-staging` |
| T1-S4-02 | GCP monitoring & alerts | T1 | Agus | Media | pending | T1-S3-03 | - | No | `feat/T1-S4-02_monitoring-alerts` |
| T2-S4-01 | Rate limiting | T2 | Branko | Media | done | T2-S2-01 | - | No | `feat/T2-S4-01_rate-limiting` |
| T3-S4-01 | Demo dataset via Airflow | T3 | Gaston | Critica | done | T3-S2-03 | T3-S4-02, T4-S4-02 | **Si** | `feat/T3-S4-01_demo-dataset` |
| T3-S4-02 | Retrieval tuning | T3 | Gaston | Alta | pending | T3-S4-01 | - | No | `feat/T3-S4-02_retrieval-tuning` |
| T4-S4-01 | Output guardrail | T4 | Lautaro | Alta | pending | T4-S3-02 | T4-S4-02 | **Si** | `feat/T4-S4-01_output-guardrail` |
| T4-S4-02 | Demo flow + edge cases | T4 | Emi, Lautaro | Critica | pending | T4-S3-02, T3-S4-01, T4-S4-01 | **DEMO MVP** | **Si** | `feat/T4-S4-02_demo-flow` |
| T5-S4-01 | Conversation sidebar | T5 | Ema | Alta | done | T2-S2-03 | - | No | `feat/T5-S4-01_conversation-sidebar` |
| T5-S4-02 | Citations + UI polish | T5 | Ema | Alta | pending | T5-S3-02 | **DEMO MVP** | **Si** | `feat/T5-S4-02_citations-polish` |

---

## 2. Rutas Criticas hacia el MVP

Hay **3 rutas criticas independientes** que convergen en el Demo MVP. Si cualquiera se retrasa, el MVP se retrasa.

### Ruta Critica A: Infraestructura de Deploy (10 specs)

```
T1-S1-01 -> T1-S1-02 -> T1-S1-03 -> T1-S1-04 -> T1-S2-01
                                                        |
T1-S3-01 (Dockerfile) -----> T1-S4-01 (Deploy) --------> DEMO MVP
T1-S3-02 (Helm Chart) ----/
```

**Cuello de botella:** T1-S3-02 (Helm Chart, XL) y T1-S4-01 (Deploy, XL). Son las tareas mas grandes del track.

### Ruta Critica B: Pipeline RAG E2E (17 specs)

```
T1-S1-01 -> T1-S1-02 -> T3-S1-01 -> T3-S1-02 -> T3-S2-01 -> T3-S2-02 -> T3-S2-03 -> T3-S4-01
                |                                      ^                       ^              |
                |-> T4-S1-02 -------------------------/                       |              v
                |                                                              |         T4-S4-02 -> DEMO MVP
                |-> T4-S1-01 -> T4-S2-03 -> T4-S3-02 ---- T4-S4-01 --------/              ^
                |                    ^          ^                                           |
                |                    |          |-> T4-S3-01                                |
                v                    |          |                                           |
           T1-S1-04 -> T1-S2-01 -> T4-S2-01 -> T4-S2-02                                   |
                                                                                            |
                        T1-S2-02 (Airflow K8s) --> T3-S2-03 ------> T3-S4-01 -------------/
```

**Cuello de botella:** T3-S2-01 (depende de 3 specs de tracks distintos), T4-S3-02 (confluencia de 4 specs), T1-S2-02 (dep. externa).

### Ruta Critica C: Frontend + API Chat (8 specs)

```
T2-S1-01 -> T2-S2-01 -> T5-S3-01 -> T5-S3-02 -> T5-S4-02 -> DEMO MVP
                |                          ^
                v                          |
            T2-S3-01 (Chat SSE) ----------/
                ^
                |
           T4-S2-03 (Generation node)
```

**Cuello de botella:** T2-S3-01 tiene dependencia cross-track con T4 (generation node debe estar listo para que SSE funcione).

### Resumen de Cuellos de Botella Criticos

| Spec | Por que es cuello de botella | Impacto si se retrasa |
|------|-----------------------------|-----------------------|
| T1-S2-02 (Airflow K8s) | Dep. externa (itmind-infra) | Bloquea DAG indexing -> demo dataset -> demo flow |
| T3-S2-01 (Embeddings) | Confluencia de T1+T3+T4 | Bloquea todo el pipeline de busqueda |
| T4-S3-02 (E2E Integration) | Confluencia de 4 specs T4 | Bloquea guardrails de salida y demo flow |
| T2-S3-01 (Chat SSE) | Dep. cross-track con T4 | Bloquea todo el frontend de chat |
| T1-S4-01 (Deploy staging) | Necesita Dockerfile + Helm | Bloquea demo |

---

## 3. Dependencias Cross-Track (Puntos de Coordinacion)

Estos son los momentos donde **dos tracks distintos deben coordinarse** porque una spec de un track depende de otra spec de otro track:

| De (Proveedor) | A (Consumidor) | Interfaz/Contrato | Coordinacion necesaria |
|-----------------|----------------|-------------------|----------------------|
| T1-S1-04 (schema base) | T2-S2-01 (auth JWT) | Tablas `users`, `refresh_tokens` | PR de T1 debe estar merged antes de empezar T2 |
| T1-S2-01 (schema SQL) | T3-S2-01 (embeddings) | Tabla `document_chunks` con `halfvec(768)` | Acordar schema exacto de chunks |
| T1-S2-01 (schema SQL) | T4-S2-01 (hybrid search) | Indices GIN, tsvector columns | Acordar columnas de busqueda full-text |
| T1-S2-02 (Airflow K8s) | T3-S2-03 (DAG indexing) | Airflow operativo, conexiones configuradas | T1 notifica cuando Airflow esta listo |
| T4-S1-02 (Gemini client) | T3-S2-01 (embeddings) | Metodo `generate_embeddings()` | Acordar interfaz del cliente Gemini |
| T4-S2-03 (generation) | T2-S3-01 (chat SSE) | LangGraph `rag_graph.astream()` | Acordar formato de streaming events |
| T2-S2-01 (auth) | T5-S3-01 (Next.js login) | Endpoints `/auth/login`, cookie format | Acordar contrato API de auth |
| T2-S3-01 (chat SSE) | T5-S3-02 (chat UI) | SSE events: `token`, `done`, `error` | Acordar formato exacto de SSE events |
| T2-S2-03 (conv. API) | T5-S4-01 (sidebar) | Endpoints CRUD conversaciones | Acordar paginacion y response schema |
| T3-S4-01 (demo data) | T4-S4-02 (demo flow) | Docs indexados en pgvector | Gaston confirma dataset listo |

---

## 4. Estrategia de Branching (Spec-Driven)

### Modelo: GitHub Flow + Feature Branches por Spec

```
main (protegida, siempre deployable)
  |
  |-- feat/T1-S2-01_sql-schema          (Franco, Agus)
  |-- feat/T2-S2-03_conversations-api   (Ema)
  |-- feat/T3-S2-01_embeddings-pgvector (Gaston)
  |-- feat/T4-S2-01_hybrid-search       (Emi, Lautaro)
  |-- feat/T4-S2-03_generation-node     (Emi)
  |-- feat/T1-S2-03_langfuse-instr      (Agus)
  ...
```

### Reglas de Naming

```
feat/{SPEC-ID}_{slug}       # Feature nueva (la mayoria de specs)
fix/{SPEC-ID}_{descripcion} # Fix a una spec ya implementada
test/{SPEC-ID}_{slug}       # Specs que son solo tests (T2-S3-02, T3-S3-02)
infra/{SPEC-ID}_{slug}      # Specs de infra/deploy (T1-S3-01, T1-S3-02, T1-S4-01)
```

**Ejemplos:**
```bash
git checkout -b feat/T3-S2-01_embeddings-pgvector
git checkout -b feat/T4-S2-03_generation-node
git checkout -b infra/T1-S3-02_helm-chart
git checkout -b test/T2-S3-02_integration-tests
```

### Ciclo de Vida de una Rama

```
1. VERIFICAR deps     -> Todas las specs "Depende de" estan merged en main?
2. CREAR rama         -> git checkout main && git pull && git checkout -b feat/T{X}-S{Y}-{Z}_{slug}
3. IMPLEMENTAR        -> Vibecoding con Claude Code, siguiendo la spec + skill
4. TESTS locales      -> pytest, linting, type-check
5. PUSH + PR          -> git push -u origin feat/T{X}-S{Y}-{Z}_{slug}
6. CODE REVIEW        -> Minimo 1 reviewer del track + 1 de track dependiente (si aplica)
7. CI pasa            -> Ruff + mypy + tests
8. MERGE              -> Squash merge a main
9. NOTIFICAR          -> En el canal del equipo: "T{X}-S{Y}-{Z} merged, desbloquea T{A}-S{B}-{C}"
```

---

## 5. Estrategia de Pull Requests

### Template de PR (vincular a spec)

```markdown
## Spec: T{X}-S{Y}-{Z} - {Titulo}

**Link:** specs/sprint-{Y}/T{X}-S{Y}-{Z}_{slug}.md

### Que implementa
- [ ] Resumen de lo implementado segun la spec

### Checklist
- [ ] Lee la spec completa antes de revisar
- [ ] Respeta "Out of scope" de la spec
- [ ] Tests incluidos (unit / integration)
- [ ] Linting + type-check pasan
- [ ] No rompe specs ya implementadas

### Dependencias (pre-merge)
- [x] T{A}-S{B}-{C} (merged en #{PR_number})
- [x] T{D}-S{E}-{F} (merged en #{PR_number})

### Desbloquea
- T{G}-S{H}-{I} (@owner)
- T{J}-S{K}-{L} (@owner)
```

### Reglas de Review

| Tipo de Spec | Reviewers requeridos | Razon |
|--------------|---------------------|-------|
| **Spec critica (ruta critica)** | 2: owner del track + owner del track bloqueado | Evitar bloqueos por bugs |
| **Spec con dep. cross-track** | 2: owner del track + owner del track proveedor | Validar que la interfaz es correcta |
| **Spec intra-track sin bloqueos** | 1: cualquier dev del track | Review rapido, no bloquear |
| **Specs de test / observabilidad** | 1: cualquier dev | Low risk |

### Reviewers Sugeridos por Spec (Cross-Track)

| PR de Spec | Reviewer primario | Reviewer cross-track | Por que |
|------------|-------------------|---------------------|---------|
| T3-S2-01 (embeddings) | Gaston (owner) | Lautaro (T4, usa Gemini client) | Interfaz de embeddings afecta search |
| T4-S2-03 (generation) | Emi (owner) | Branko (T2, necesita para SSE) | Formato de streaming afecta endpoint |
| T2-S3-01 (chat SSE) | Branko (owner) | Ema (T5, consume SSE en UI) | Formato de events afecta frontend |
| T1-S2-01 (schema SQL) | Franco (owner) | Gaston (T3) + Emi (T4) | Schema afecta indexing y search |
| T5-S3-01 (Next.js login) | Ema (owner) | Branko (T2, provee auth API) | Contrato auth debe coincidir |

---

## 6. Estrategia de Merge

### Metodo: Squash Merge (Obligatorio)

```bash
# En GitHub: configurar repo para "Squash and merge" como default
# Cada PR = 1 commit limpio en main con formato:
#   feat(T3-S2-01): implement Gemini embeddings + pgvector storage
```

**Por que Squash Merge:**
- Historial limpio: cada spec = 1 commit en main
- Facil revert: si una spec rompe algo, `git revert {commit}` revierte toda la spec
- Facil auditoria: `git log --oneline` muestra el progreso spec por spec

### Formato de Commit Message (en Squash)

```
{tipo}({spec-id}): {descripcion concisa}

{body opcional con detalles}

Refs: #{PR_number}
```

**Tipos:** `feat`, `fix`, `test`, `infra`, `docs`

**Ejemplos:**
```
feat(T3-S2-01): implement Gemini embeddings with pgvector halfvec(768) storage
feat(T4-S2-03): add LangGraph generation node with streaming and citations
infra(T1-S3-02): create Helm chart base with PostgreSQL and Redis sub-charts
test(T2-S3-02): add API integration tests for auth and conversations
```

### Orden de Merge Recomendado (por Sprint)

#### Sprint 2 (specs pendientes) - Orden optimo de merge

| Orden | Spec | Puede empezar cuando | Merge deadline sugerido |
|:-----:|------|----------------------|------------------------|
| 1 | T1-S2-02 (Airflow K8s) | Infra externa lista | Inicio Sprint 2 |
| 2 | T1-S2-03 (Langfuse instr.) | T1-S1-06 done | Dia 1-2 |
| 3 | T2-S2-03 (Conv. API) | T2-S2-01 done | Dia 1-2 |
| 4 | T3-S2-01 (Embeddings) | T1-S2-01 + T3-S1-02 + T4-S1-02 done | Dia 2-3 |
| 5 | T4-S2-01 (Hybrid search) | T1-S2-01 + T3-S2-01 merged | Dia 3-4 |
| 6 | T4-S2-03 (Generation) | T4-S1-01 + T4-S1-02 done | Dia 2-3 (paralelo a T3-S2-01) |
| 7 | T4-S2-02 (Reranking) | T4-S2-01 merged | Dia 4-5 |
| 8 | T3-S2-02 (Indexing svc) | T3-S2-01 merged | Dia 3-4 |
| 9 | T3-S2-03 (Airflow DAG) | T1-S2-02 + T3-S2-02 merged | Dia 4-5 |

#### Sprint 3 - Orden optimo de merge

| Orden | Spec | Puede empezar cuando | Notas |
|:-----:|------|----------------------|-------|
| 1a | T1-S3-01 (Dockerfile) | Sin deps internas | Paralelo |
| 1b | T1-S3-02 (Helm chart) | Sin deps internas | Paralelo |
| 1c | T4-S3-01 (Input guardrail) | T4-S1-01 done | Paralelo |
| 1d | T5-S3-01 (Next.js login) | T2-S2-01 done | Paralelo |
| 2a | T1-S3-03 (GCP monitoring) | T1-S2-03 merged | |
| 2b | T3-S3-01 (OpenText synth) | T1-S2-01 done | Non-blocking |
| 2c | T2-S3-01 (Chat SSE) | T4-S2-03 merged | **Blocker para frontend** |
| 3 | T4-S3-02 (E2E integration) | T4-S2-01 + T4-S2-02 + T4-S2-03 + T4-S3-01 | Confluencia |
| 4a | T5-S3-02 (Chat UI) | T5-S3-01 + T2-S3-01 merged | |
| 4b | T3-S3-02 (Indexing tests) | T3-S2-03 merged | Non-blocking |
| 4c | T2-S3-02 (API tests) | T2-S2-01 + T2-S2-03 merged | Non-blocking |

#### Sprint 4 - Orden optimo de merge

| Orden | Spec | Puede empezar cuando | Notas |
|:-----:|------|----------------------|-------|
| 1a | T3-S4-01 (Demo dataset) | T3-S2-03 merged | Critico para demo |
| 1b | T4-S4-01 (Output guardrail) | T4-S3-02 merged | |
| 1c | T2-S4-01 (Rate limiting) | T2-S2-01 done | Non-blocking |
| 1d | T5-S4-01 (Sidebar) | T2-S2-03 merged | |
| 2a | T3-S4-02 (Retrieval tuning) | T3-S4-01 merged | |
| 2b | T1-S4-01 (Deploy staging) | T1-S3-01 + T1-S3-02 merged | **Critico** |
| 2c | T5-S4-02 (Citations+polish) | T5-S3-02 merged | **Critico** |
| 3 | T4-S4-02 (Demo flow) | T4-S3-02 + T3-S4-01 + T4-S4-01 | **Ultimo antes de demo** |
| 4 | T1-S4-02 (GCP alerts) | T1-S3-03 merged | Nice-to-have |

---

## 7. Gestion de Conflictos

### Zonas de Conflicto Frecuente

| Archivo/Directorio | Tracks que lo tocan | Tipo de conflicto | Mitigacion |
|-------------------|--------------------|--------------------|------------|
| `pyproject.toml` | Todos | Dependencias agregadas en paralelo | Merge manual, trivial (agregar lineas) |
| `alembic/versions/` | T1, T2, T3 | Migraciones con heads divergentes | Ejecutar `alembic merge heads` |
| `src/infrastructure/persistence/models/` | T1, T2, T3 | Modelos SQLAlchemy nuevos | Archivos separados por dominio, bajo conflicto |
| `src/presentation/api/v1/` | T2, T5 | Endpoints nuevos | Archivos separados por recurso (auth.py, chat.py, conversations.py) |
| `src/application/services/` | T3, T4 | Servicios nuevos | Archivos separados, bajo conflicto |
| `src/domain/` | Todos | Entidades, value objects | Archivos separados por bounded context |
| `docker-compose.yml` | T1, posiblemente T3 | Servicios nuevos | T1 es owner exclusivo |
| `.github/workflows/ci.yml` | T1 | Steps nuevos | T1 es owner exclusivo |
| `frontend/` | T5 exclusivo | - | Sin conflicto (track unico) |
| `dags/` | T3 exclusivo | - | Sin conflicto (track unico) |

### Protocolo de Resolucion de Conflictos

#### Conflicto Tipo 1: Migraciones Alembic Divergentes

**Escenario:** Franco agrega tablas de OpenText, Gaston modifica `document_chunks` -- ambos generan migraciones.

```bash
# Detectar el conflicto
alembic heads
# Output: abc123, def456 (dos heads = conflicto)

# Resolver: crear merge migration
alembic merge heads -m "merge T1-S2-01 and T3-S2-01 migrations"

# Verificar
alembic upgrade head
alembic check  # sin errores
```

**Prevencion:** Antes de crear una migracion, hacer `git pull main` y verificar `alembic heads`.

#### Conflicto Tipo 2: pyproject.toml (Dependencias)

**Escenario:** T3 agrega `pymupdf`, T4 agrega `langgraph` en branches paralelas.

```toml
# Branch T3:
dependencies = [
    "fastapi>=0.115",
+   "pymupdf>=1.24",
]

# Branch T4:
dependencies = [
    "fastapi>=0.115",
+   "langgraph>=0.2",
]
```

**Resolucion:** Git no puede auto-resolver. El segundo PR que mergea ve el conflicto:
```bash
git checkout feat/T4-S2-01_hybrid-search
git fetch origin && git merge origin/main
# Resolver: mantener AMBAS lineas
# Ejecutar: uv sync para verificar compatibilidad
```

#### Conflicto Tipo 3: Interfaces Compartidas (Raro pero Critico)

**Escenario:** T4 cambia la firma de `GeminiClient.generate_embeddings()` y T3 ya la esta usando.

**Protocolo:**
1. **Comunicar antes de cambiar interfaces** -- mensaje en canal de equipo
2. Si ya hay conflicto: el track que consume la interfaz adapta su codigo
3. Si la interfaz original era incorrecta: PR de fix primero, luego ambos tracks rebase

#### Conflicto Tipo 4: Cambios en Archivos Config Compartidos

**Escenario:** Multiples tracks modifican `src/infrastructure/config/settings.py` para agregar sus env vars.

**Prevencion:**
- Cada track agrega sus settings en un bloque separado con comentario `# Track T{X}`
- O mejor: separar en archivos por dominio (`settings/auth.py`, `settings/rag.py`, etc.)

### Comando Rapido: Actualizar Branch con Main

```bash
# ANTES de hacer PR, siempre actualizar:
git checkout feat/T{X}-S{Y}-{Z}_{slug}
git fetch origin
git rebase origin/main

# Si hay conflictos:
# 1. Resolver en el editor
# 2. git add <archivos>
# 3. git rebase --continue

# Si el rebase es muy complejo, usar merge:
git merge origin/main
```

---

## 8. Paralelismo Maximo por Sprint

### Sprint 2: Hasta 6 ramas en paralelo

```
Semana 2, Dia 1-2:
  [Franco/Agus] feat/T1-S2-02_airflow-k8s        (independiente, dep. externa)
  [Agus]        feat/T1-S2-03_langfuse-instr       (dep. T1-S1-06)
  [Ema]         feat/T2-S2-03_conversations-api    (dep. T2-S2-01 done)
  [Branko]      (disponible -- puede ayudar en reviews o adelantar T2-S3-01 scaffolding)
  [Gaston]      feat/T3-S2-01_embeddings-pgvector  (deps done)
  [Emi]         feat/T4-S2-03_generation-node      (deps done)
  [Lautaro]     (espera T4-S2-01 -- puede ayudar en T4-S2-03 o preparar T4-S2-02)

Semana 2, Dia 3-5:
  [Emi/Lautaro] feat/T4-S2-01_hybrid-search        (espera T3-S2-01)
  [Lautaro]     feat/T4-S2-02_reranking            (espera T4-S2-01)
  [Gaston]      feat/T3-S2-02_indexing-service     (espera T3-S2-01)
  [Gaston]      feat/T3-S2-03_airflow-dag-indexing (espera T1-S2-02 + T3-S2-02)
```

### Sprint 3: Hasta 7 ramas en paralelo

```
Dia 1 (paralelo total):
  [Franco]      infra/T1-S3-01_dockerfile
  [Agus]        infra/T1-S3-02_helm-chart
  [Lautaro]     feat/T4-S3-01_input-guardrail
  [Ema]         feat/T5-S3-01_nextjs-login
  [Gaston]      feat/T3-S3-01_opentext-synthetic
  [Branko]      feat/T2-S3-01_chat-sse-endpoint     (si T4-S2-03 ya merged)
  [Emi]         (espera para T4-S3-02 -- review de PRs)

Dia 3-5:
  [Emi]         feat/T4-S3-02_e2e-integration      (confluencia de 4 deps)
  [Ema]         feat/T5-S3-02_chat-ui              (espera T2-S3-01)
  [Branko]      test/T2-S3-02_integration-tests
  [Gaston]      test/T3-S3-02_indexing-tests
  [Agus]        feat/T1-S3-03_gcp-monitoring
```

---

## 9. Workflow Completo: De Spec a Merge

### Paso a Paso para un Dev

```bash
# 1. ELEGIR spec (verificar que deps estan done en main)
#    Consultar esta tabla: Depende de = done? -> Proceder

# 2. CREAR rama
git checkout main
git pull origin main
git checkout -b feat/T3-S2-01_embeddings-pgvector

# 3. IMPLEMENTAR (vibecoding con Claude Code)
#    - Abrir la spec: specs/sprint-2/T3-S2-01_embeddings-pgvector.md
#    - Leer el skill referenciado
#    - Implementar siguiendo la spec al pie de la letra
#    - NO implementar nada "Out of scope"

# 4. TESTS
uv run pytest tests/ -x -v
uv run ruff check src/
uv run mypy src/

# 5. ACTUALIZAR con main (por si alguien mergeo algo)
git fetch origin
git rebase origin/main
# Resolver conflictos si los hay

# 6. PUSH
git push -u origin feat/T3-S2-01_embeddings-pgvector

# 7. CREAR PR (usando gh CLI)
gh pr create \
  --title "feat(T3-S2-01): implement Gemini embeddings + pgvector storage" \
  --body "$(cat <<'EOF'
## Spec: T3-S2-01 - Gemini Embeddings + pgvector

**Link:** specs/sprint-2/T3-S2-01_embeddings-pgvector.md

### Que implementa
- EmbeddingService con Gemini text-embedding-004
- Batch processing (max 100 texts)
- L2 normalization
- Storage en pgvector con halfvec(768)
- HNSW index verification

### Dependencias (pre-merge)
- [x] T1-S2-01 (merged en #42)
- [x] T3-S1-02 (merged en #38)
- [x] T4-S1-02 (merged en #40)

### Desbloquea
- T3-S2-02 Indexing Service (@gaston)
- T4-S2-01 Hybrid Search (@emi @lautaro)

### Checklist
- [x] Spec leida completa
- [x] Tests unitarios
- [x] Linting + type-check pasan
- [x] No rompe specs ya implementadas
EOF
)" \
  --reviewer gaston,lautaro

# 8. ESPERAR REVIEW + CI

# 9. MERGE (squash merge desde GitHub UI)

# 10. NOTIFICAR
#     "T3-S2-01 merged! @emi @lautaro pueden empezar T4-S2-01"
```

---

## 10. GitHub Repo Settings Recomendados

### Branch Protection Rules (main)

```
Settings > Branches > Branch protection rules > main:

[x] Require a pull request before merging
    [x] Require approvals: 1
    [x] Dismiss stale pull request approvals when new commits are pushed
[x] Require status checks to pass before merging
    [x] ruff-check
    [x] mypy-check
    [x] pytest
[x] Require branches to be up to date before merging
[x] Restrict who can push to matching branches (solo merge via PR)
[ ] Require signed commits (opcional)
[x] Do not allow bypassing the above settings
```

### Merge Settings

```
Settings > General > Pull Requests:

[x] Allow squash merging (DEFAULT)
    Commit message: Pull request title and description
[ ] Allow merge commits (deshabilitado)
[ ] Allow rebase merging (deshabilitado)
[x] Automatically delete head branches
```

### Labels Sugeridos

```
track:T1-infra       (color: #0075ca)
track:T2-backend     (color: #e4e669)
track:T3-indexing    (color: #0e8a16)
track:T4-agents      (color: #d93f0b)
track:T5-frontend    (color: #5319e7)
priority:critica     (color: #b60205)
priority:alta        (color: #d93f0b)
priority:media       (color: #fbca04)
sprint:1             (color: #c5def5)
sprint:2             (color: #c5def5)
sprint:3             (color: #c5def5)
sprint:4             (color: #c5def5)
critical-path        (color: #b60205)
cross-track          (color: #d876e3)
blocked              (color: #000000)
```

---

## 11. Cheat Sheet para el Equipo

### Antes de empezar una spec

```bash
# Verificar que las dependencias estan en main
git log --oneline main | grep "T{X}-S{Y}-{Z}"  # para cada dep
```

### Si mi branch tiene conflictos con main

```bash
git fetch origin
git rebase origin/main
# Resolver archivo por archivo
git add <archivo_resuelto>
git rebase --continue
```

### Si alembic tiene multiples heads

```bash
alembic heads              # ver heads divergentes
alembic merge heads -m "merge migrations"
alembic upgrade head       # verificar
```

### Si necesito el trabajo de otro branch que aun no esta en main

```bash
# OPCION A: Esperar (preferida)
# OPCION B: Rebase temporal (si es urgente)
git checkout feat/mi-spec
git rebase feat/otra-spec-que-necesito
# CUIDADO: cuando la otra spec mergee a main, hacer rebase a main inmediatamente
```

### Si rompi main (revert de emergencia)

```bash
# Encontrar el commit de la spec que rompio
git log --oneline main | head -5
# Revert del squash commit
git revert {commit_hash}
# PR de emergencia (1 reviewer, merge rapido)
```

---

## 12. Resumen Visual: Flujo de una Spec

```
  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Spec ready   │────>│ Create branch │────>│  Vibecoding  │
  │  (deps done)  │     │  feat/T{X}... │     │  con Claude  │
  └──────────────┘     └──────────────┘     └──────┬───────┘
                                                    │
                                                    v
  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Merge a main │<────│  Code Review  │<────│  Push + PR   │
  │  (squash)     │     │  (1-2 revs)   │     │  CI verde    │
  └──────┬───────┘     └──────────────┘     └──────────────┘
         │
         v
  ┌──────────────┐
  │  Notificar    │
  │  tracks       │
  │  desbloqueados│
  └──────────────┘
```
