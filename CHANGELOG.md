# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **[T2-S4-01]** Rate limiting basico con Redis sliding window. Middleware ASGI puro (SSE-safe, sin BaseHTTPMiddleware): limite por IP 100 req/min para endpoints publicos, por usuario 30 req/min para chat. Response 429 con `Retry-After`, fail-open si Redis no disponible, configurable via settings. Archivos: `src/infrastructure/api/middleware/rate_limiter.py` (creado), `src/config/settings.py` (5 settings nuevos), `src/infrastructure/api/main.py` (middleware registrado en stack). Tests: `tests/unit/test_rate_limiting.py` (35 tests, 8 clases).
- **[T1-S1-06]** Deploy Langfuse en K8s: manifests Helm (`infra/langfuse/values.yaml`, `namespace.yaml`, `secret.template.yaml`), README con instrucciones paso a paso, script de verificacion (`scripts/test-langfuse.py`). Todas las specs de Sprint 1 completadas (12/12).
- **[T1-S1-05]** Pipeline CI basico con GitHub Actions (`.github/workflows/ci.yml`): ejecuta `ruff check`, `ruff format --check` y `mypy src/` en cada push/PR a `main`/`develop`. Cache de pip y concurrency con cancel-in-progress.
- **[T1-S1-05]** Pre-commit hooks opcionales (`.pre-commit-config.yaml`): Ruff lint+fix, Ruff format y mypy.
- **[AUDIT]** `agent/AUDITORIA_TECNICA.md`: Informe de auditoría técnica integral (~700 líneas) con 7 hallazgos críticos, 16 inconsistencias, ERD unificado, directorio propuesto y 12 acciones priorizadas.
- **[AUDIT-P0-4]** Tabla `security_events` con ENUM `security_event_type` agregada a `database-setup/SKILL.md`.
- **[AUDIT-P0-2]** Tabla `user_memories` unificada (merging 3 fuentes) agregada a `database-setup/SKILL.md` con ENUM `memory_category`.

### Changed
- **[T1-S1-05]** `pyproject.toml`: mypy relajado (`strict = false`, `ignore_missing_imports = true` global) para endurecimiento gradual. Eliminado override por modulo y opciones `disallow_untyped_defs`/`disallow_any_generics`.
- **[T1-S1-05]** `src/infrastructure/database/models/conversation.py` y `user.py`: Auto-formateados por Ruff.
- **[AUDIT-P0-1]** `guardrails/SKILL.md`: `AgentState` → `RAGState`, `state["context"]` → `state["context_text"]`, `state["answer"]` → `state["response"]`.
- **[AUDIT-P0-2]** `chat-memory/SKILL.md`: Modelo `UserMemory` actualizado con columnas `thread_id`, `importance`, `last_accessed_at` y tipo ENUM `MemoryCategory`.
- **[AUDIT-P0-3]** `database-setup/SKILL.md`: Eliminada tabla `checkpoints` manual (conflicto con `PostgresSaver.setup()`). Agregado comentario de exclusión de Alembic.
- **[AUDIT-P0-5]** `instructions.md`: Diagrama de costos corregido: `Gemini (smart)` → `GPT-4o (multi-tier)` para generación.
- **[AUDIT-P1-6]** `CLAUDE.md`: Corregido conteo de skills (11→16), eliminada referencia a `skill_faltantes.md` inexistente, agregados `PLAN_MEJORAS.md` y `AUDITORIA_TECNICA.md`.
- **[AUDIT-P1-7]** `database-setup/SKILL.md`: Sección Docker Compose reemplazada con referencia al skill autorativo `docker-deployment`.
- **[AUDIT-P1-9]** `instructions.md` + `CLAUDE.md`: Versión Python actualizada de `3.11+` a `3.12+` para alinear con Dockerfiles.
- **[AUDIT-P3-12]** `SKILLS.md`: Corregida numeración duplicada en sección de prioridad baja (#13-16 → #16-19).

### Removed
- **[AUDIT-P0-3]** Tabla `checkpoints` manual de `database-setup/SKILL.md` (autogestionada por LangGraph).
- **[AUDIT-P1-7]** Bloque Docker Compose duplicado de `database-setup/SKILL.md`.

### Added
- CLAUDE.md con instrucciones del proyecto para Claude Code
- Plan de mejoras colaborativo (`agent/PLAN_MEJORAS.md`) con 58 tareas en 5 fases
- Auditoria comparativa contra 12 skills externos de skills.sh
- Identificacion de mejoras criticas para database-setup, rag-indexing, rag-retrieval, observability, error-handling
- Identificacion de skills faltantes: langgraph, docker-deployment, prompt-engineering

### Changed
- **[0.1.1]** Reestructurar skill `observability`: SKILL.md reducido de 1128 a 186 lineas. Extraidos 7 archivos a `references/` (cost-calculator, ragas-evaluator, prometheus-metrics, logging-config, audit-logging, sentry-config, dashboard-service). Sin perdida de informacion.
- **[0.1.2]** Reestructurar skill `security-mirror`: SKILL.md reducido de 1042 a 234 lineas. Extraidos 5 archivos a `references/` (membresia-recursiva, chinese-walls, python-integration, sync-dauditnew, auditoria-forense). Sin perdida de informacion.
- **[0.1.3]** Reestructurar skill `rag-retrieval`: SKILL.md reducido de 1035 a 210 lineas. Extraidos 7 archivos a `references/` (query-processing, pgvector-store, reranking, semantic-cache, context-assembly, generation-service, retrieval-service). Sin perdida de informacion.
- **[0.1.4]** Reestructurar skill `rag-indexing`: SKILL.md reducido de 775 a 126 lineas. Extraidos 4 archivos a `references/` (document-loaders, chunking-area, gemini-embeddings, indexing-service). Sin perdida de informacion.
- **[0.1.5]** Reestructurar skill `testing-strategy`: SKILL.md reducido de 675 a 126 lineas. Extraidos 2 archivos a `references/` (fixtures-globales, tests-ejemplos). Sin perdida de informacion. **Grupo 0.1 completado.**
- **[0.2.1]** Reescribir `description` con triggers de activacion en los 12 skills. Todos incluyen ahora frase "Activar cuando..." para mejorar la seleccion automatica de skills.
- **[0.3.1]** Unificar idioma: traducidos titulos H1, H2 y H3 de ingles a espanol en los 12 SKILL.md. Comentarios dentro de bloques de codigo no modificados.
- **[0.4.1]** Resolver inconsistencia LLM: documentada estrategia multi-proveedor en `instructions.md` (seccion 5 de decisiones). GPT-4o para generacion, Gemini para embeddings/guardrails. Alineado pipeline en `rag-retrieval`. **Fase 0 completada.**
- **[1.1.1-5]** Skill `database-setup`: Creados 5 archivos de referencia avanzados en `references/`:
  - `ef-search-tuning.md`: Tabla de tuning `ef_search` con precision vs velocidad, configuracion por sesion con `SET LOCAL`, benchmark SQL.
  - `binary-quantization.md`: Binary Quantization para reduccion 32x de memoria sobre `halfvec`, implementacion two-phase search con reranking.
  - `iterative-scan.md`: Iterative scan con `relaxed_order`/`strict_order` para resolver over-filtering en HNSW con filtros.
  - `monitoring-queries.md`: Queries SQL de monitoreo pgvector (index status, cache hit ratio, bloat, slow queries) + script Python health check.
  - `bulk-loading.md`: Best practices bulk loading (drop index, COPY/unnest batch, rebuild). Comparativa rendimiento naive vs optimizado.
- **[1.2.1-5]** Skill `rag-indexing`: Creados 4 archivos de referencia avanzados en `references/`:
  - `gemini-task-types.md`: Documentacion de los 8 task types de Gemini embeddings con matriz de decision para nuestro pipeline.
  - `batch-embedding-caveats.md`: Bug de batch ordering (>328 items), limites de memoria por batch, rate limiting con TPM/RPM.
  - `embedding-normalization.md`: Normalizacion L2 obligatoria para Matryoshka truncado (768 != 3072), funciones normalize + verificacion.
  - `multi-index-strategy.md`: Estrategia multi-indice con 3 opciones (particionamiento, tablas separadas, indices parciales) + query routing.
- **[1.3.1-5]** Skill `rag-retrieval`: Creados 3 archivos de referencia avanzados en `references/`:
  - `query-transforms.md`: Pipeline de transformacion de queries con HyDE, Multi-Query, Step-Back Prompting + pipeline integrado con auto-seleccion.
  - `agentic-rag.md`: Patron Agentic RAG con QueryRouter (7 tipos de query), herramientas especializadas (SimpleRetrieval, MultiStep, Clarification) + orquestador.
  - `contextual-compression.md`: Compresion contextual con RelevanceFilter, SentenceExtractor (sin LLM) y LLMContentExtractor (con LLM).
- **[1.4.1-4]** Skill `observability`: Creados 4 archivos de referencia avanzados en `references/`:
  - `sli-slo-management.md`: Definiciones SLI/SLO para disponibilidad, latencia y calidad RAG. SLI collectors con Prometheus metrics, error budgets.
  - `compliance-monitoring.md`: Monitor PCI-DSS bancario con deteccion de datos sensibles, sanitizacion de respuestas, checks periodicos.
  - `otel-collector.md`: Configuracion completa OTel Collector con receivers (OTLP, Prometheus), processors (tail sampling, batch) y exporters.
  - `observability-as-code.md`: Dashboards Grafana como JSON, recording rules Prometheus YAML, alertas versionadas, Docker Compose monitoring stack.
- **[1.5.1-3]** Skill `error-handling`: Creados 3 archivos de referencia avanzados en `references/`:
  - `batch-processing.md`: Patron BatchResult generico con succeeded/failed tracking, FailureReason enum, retry logic, metricas Prometheus.
  - `exception-chaining.md`: Patrones `raise...from` con 3 escenarios (dominio, multi-nivel, supresion) + decorador `translate_exceptions`.
  - `progress-reporting.md`: ProgressTracker con callbacks (Logging, Redis, SSE), calculo ETA, endpoint API para streaming de progreso. **Fase 1 completada.**
- **[2.1.1-5]** Skill `api-design`: Creados 5 archivos de referencia avanzados en `references/`:
  - `cve-awareness.md`: CVE-2024-47874 (SSRF via multipart boundary), CVE-2024-12868 (path traversal StaticFiles) con middleware de deteccion y tests de regresion.
  - `magic-bytes-validation.md`: Validacion de archivos por firma binaria (magic bytes). FileValidator con deteccion de Office (ZIP interno), bloqueo de PE/ELF, endpoint integrado.
  - `cursor-pagination.md`: Paginacion cursor-based (keyset) reemplazando offset-based. CursorPage schema, encode/decode base64, repository con WHERE (created_at, id) < cursor.
  - `connection-pooling.md`: Connection pooling asyncpg optimizado. Pool sizing formula (workers × 2 + 3), health checks, Prometheus monitoring, graceful shutdown.
  - `concurrency-patterns.md`: Patrones asyncio.gather con semaforos, timeouts, background tasks con FastAPI, TaskGroup (Python 3.11+), circuit breaker pattern.
- **[2.2.1-4]** Skill `testing-strategy`: Creados 2 archivos de referencia + mejoras a templates existentes:
  - `parametrize-patterns.md`: Patrones @pytest.mark.parametrize avanzados (IDs descriptivos, producto cartesiano, indirect fixtures, generacion dinamica de payloads).
  - `mocking-strategies.md`: Estrategias de mocking con pytest-mock + unittest.mock (AsyncMock, spy, side_effect, datetime mock, spec-based type safety).
  - Mejorado `fixtures-globales.md`: Agregada documentacion de scopes, plugins recomendados (pytest-xdist, pytest-mock, pytest-timeout, etc.), hooks utiles (pytest_configure, pytest_collection_modifyitems, auto-timing fixture).
  - Mejorado `SKILL.md` pytest.ini: Agregados timeout default, markers smoke, filterwarnings, variables de entorno para tests, cobertura de migraciones excluida.
- **[2.3.1-2]** Skill `authentication`: Creados 2 archivos de referencia avanzados en `references/`:
  - `cve-auth-dependencies.md`: CVEs de PyJWT (CVE-2022-29217 algorithm confusion), passlib/bcrypt timing attack, python-jose deprecado. Tests de regresion, migracion jose→PyJWT, versiones minimas seguras.
  - `owasp-mapping.md`: Mapping completo OWASP Top 10 (2021) con mitigaciones especificas para RAG enterprise. A01 (RBAC + vector search con permisos), A02 (bcrypt+JWT), A03 (ORM parametrizado), A05 (headers OWASP), A07 (rate limiting + lockout), A09 (audit trail), A10 (SSRF validation).
- Actualizados SKILL.md de los 3 skills con tablas de referencias avanzadas y checklist items vinculados. **Fase 2 completada.**
- **[3.1.1-5]** Skill `langgraph` (**NUEVO**): Creado skill completo con SKILL.md (~190 lineas) + 3 archivos de referencia:
  - `SKILL.md`: Arquitectura del grafo RAG, definicion de RAGState con custom reducers (merge_chunks, accumulate_sources), compilacion del grafo con conditional edges, uso con PostgresSaver.
  - `references/rag-nodes.md`: Implementacion de 10 nodos (validate_input, process_query, route_query, retrieve, rerank, assemble_context, generate, validate_output, extract_memory, respond_blocked).
  - `references/conditional-routing.md`: 5 patrones de routing (query type, retry con limite, guardrail gate, retrieval quality, subgrafos).
  - `references/anti-patterns.md`: 6 anti-patterns con solucion (loops infinitos, nodos sin return, estado gigante, side effects, sin checkpointer, hardcoding).
- **[3.2.1-5]** Skill `docker-deployment` (**NUEVO**): Creado skill completo con SKILL.md (~170 lineas) + 3 archivos de referencia:
  - `SKILL.md`: Arquitectura de servicios, Dockerfile multi-stage, Docker Compose resumen, tabla de security hardening.
  - `references/multi-stage-dockerfile.md`: Dockerfile detallado con builder/runtime, .dockerignore, entrypoint con Alembic, comparativa de tamaos.
  - `references/compose-full-stack.md`: docker-compose.yml completo (FastAPI, PostgreSQL/pgvector tuneado, Redis, Langfuse, pgAdmin con profile), init SQL, .env example, comandos utiles.
  - `references/security-hardening.md`: Non-root user, secrets management, read-only FS, network segmentation, image scanning, resource limits, checklist pre-deploy.
- **[3.3.1-4]** Skill `chat-memory` (EXPANDIDO): Verificado skill existente (v0.3.0, 144 lineas). Agregados 2 archivos de referencia + actualizado SKILL.md:
  - `references/redis-session-cache.md`: SessionCache con Redis (add/get messages, session state, TTL, extend, clear). Arquitectura cache vs persistencia.
  - `references/langgraph-memory-integration.md`: Nodos load_memory y save_memory para el grafo, MemoryRepository con pgvector, extraccion de recuerdos con LLM (Gemini Flash).
  - Actualizado SKILL.md con tabla de referencias y checklist expandido. **Fase 3 completada.**
- **[4.1.1-4]** Skill `prompt-engineering` (**NUEVO**): Creado skill completo con SKILL.md (~170 lineas) + 3 archivos de referencia:
  - `SKILL.md`: Arquitectura de prompts, system prompt base con 6 secciones obligatorias, selector automatico de tecnica (zero-shot, few-shot, CoT, step-back), defensa prompt injection resumen (4 capas), delimitadores XML.
  - `references/few-shot-banking.md`: Patrones few-shot domain-specific bancario. 3 categorias de ejemplos (requisitos, comparaciones, procedimientos). Selector automatico de ejemplos por clasificacion de query, banco de ejemplos versionable, metricas de impacto.
  - `references/chain-of-thought.md`: 3 templates CoT especializados (sintesis multi-fuente, comparaciones, condicionales). Selector automatico por indicadores linguisticos, PromptBuilder integrado, CoT visible vs interno, metricas de impacto.
  - `references/prompt-injection-defense.md`: Sistema de defensa en 4 capas (L1 sanitizacion regex con 15+ patrones, L2 deteccion con Gemini Flash, L3 aislamiento XML, L4 post-validacion output). Tests de regresion con pytest parametrize (10+ ataques + 5 queries seguros).
- **[4.2.1-2]** Skill `frontend` (**NUEVO**): Creado skill completo con SKILL.md (~180 lineas) + 2 archivos de referencia:
  - `SKILL.md`: Arquitectura general (Chat UI + Admin Dashboard), stack tecnologico (Next.js 14+, TypeScript, Tailwind, shadcn/ui, React Query, Zustand), estructura de rutas App Router, componente ChatInterface con streaming SSE, SourceCitations expandible, middleware de autorizacion por rol, sistema de diseno.
  - `references/chat-components.md`: Componentes detallados: ChatMessage (Markdown rendering, citaciones como badges), ChatInput (auto-resize, envio con Enter, cancel streaming), FeedbackWidget (thumbs up/down + comentario), ConversationSidebar (historial con timestamps), API Client centralizado, atajos de teclado.
  - `references/admin-dashboard.md`: Dashboard completo: Layout con sidebar, MetricsOverview (4 cards KPI), LatencyChart (LineChart con SLO reference line), DocumentsPage (tabla con filtros, upload, re-indexar, eliminar), AuditPage (logs de seguridad por severidad), responsive design con useMediaQuery, dark mode con next-themes, testing con Vitest + Testing Library.
- Actualizados SKILLS.md e instructions.md con los 2 nuevos skills. **Fase 4 completada. Plan de mejoras 100% completado.**
- **[SECURITY]** Skill `frontend` actualizado tras analisis de vulnerabilidades criticas en React Server Components:
  - 5 CVEs documentados: CVE-2025-55182 (RCE critico), CVE-2025-55184/67779/CVE-2026-23864 (DoS alta), CVE-2025-55183 (source code exposure).
  - Versiones pineadas: React >= 19.2.4, Next.js >= 15.5.10 (antes decia "14+").
  - Agregada seccion "Security Advisories" con tabla de CVEs, versiones seguras por release line, reglas obligatorias para Server Functions (no hardcodear secretos, validar con Zod, rate limiting), y links a los blog posts oficiales.
  - Actualizado checklist con 2 pasos nuevos: `npm audit` obligatorio y pinear versiones exactas.

## [0.3.0] - 2026-02-10

### Added
- Documentacion de decisiones arquitectonicas RAG (`docs/DECISIONES_ARQUITECTONICAS_RAG.md`)
- Estrategia de chunking adaptativo (`docs/ESTRATEGIA_CHUNKING_ADAPTATIVO.md`)
- Estrategia de memoria RAG (`docs/ESTRATEGIA_MEMORIA_RAG.md`)
- Estrategia de permisos vectoriales (`docs/ESTRATEGIA_PERMISOS_VECTORIALES.md`)
- Skill `chat-memory` para memoria conversacional con LangGraph
- Skill `guardrails` para validacion de entrada/salida
- Identificacion de skills faltantes (frontend, memoria, guardrails)

## [0.2.0] - 2026-02-10

### Added
- Skills iniciales: database-setup, observability, rag-indexing, rag-retrieval
- Skills de seguridad: authentication, security-pentesting, error-handling
- Skill api-design con estandares REST
- Skill testing-strategy con configuracion Pytest
- Indice de skills (`agent/SKILLS.md`)

### Changed
- Actualizacion de instrucciones fundacionales a v2.0
- Refinamiento de skill api-design

## [0.1.0] - 2026-02-10

### Added
- Estructura inicial del proyecto con instrucciones del agente
- Guia fundacional del sistema RAG enterprise (`agent/instructions.md`)

### Removed
- Codigo fuente inicial (reset para enfocarse en fase de planificacion)
- Dockerfile y configuracion de dependencias

[Unreleased]: https://github.com/data-oilers/rag_framework_skills/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/data-oilers/rag_framework_skills/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/data-oilers/rag_framework_skills/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/data-oilers/rag_framework_skills/releases/tag/v0.1.0
