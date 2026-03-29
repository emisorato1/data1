# Guia de Auditoria por Spec — Enterprise AI Platform

> **Version**: 4.0 | **Fecha**: 2026-03-09 | **Skill**: `audit-spec-pr`

---

## 1. Que es esta guia

Esta guia explica como usar la skill `audit-spec-pr` para auditar **cada spec/tarea individual** a lo largo de su ciclo de vida. La skill esta instalada en `.opencode/skills/audit-spec-pr/` y `.agent/skills/audit-spec-pr/`.

### Diferencia con audit-sprint-checklist

| | `audit-spec-pr` (esta guia) | `audit-sprint-checklist` |
|---|---|---|
| **Cuando** | En cada tarea/spec | Al final del sprint |
| **Granularidad** | Una spec | Todo el sprint |
| **Uso** | Dia a dia de desarrollo | Gate de release |
| **Invocacion** | Un prompt por etapa | Un solo prompt |

### Que audita

- Acceptance Criteria cumplidos 1:1
- Out of scope respetado
- Arquitectura hexagonal y ADRs
- Tecnologias permitidas (solo Gemini/Vertex AI)
- Calidad: tests, coverage >= 80%, linting, typing
- Seguridad: OWASP Web + LLM
- Impacto en specs dependientes

### Que NO audita

- Specs no relacionadas
- Funcionalidad futura (Out of scope)
- Decisiones de negocio del banco
- Infraestructura GCP (eso lo cubre `audit-sprint-checklist`)

---

## 2. Setup (una sola vez)

### Verificar entorno

```bash
uv run ruff check --version && uv run mypy --version && uv run pytest --version && docker compose version
```

### Verificar que la skill existe

```bash
ls .opencode/skills/audit-spec-pr/SKILL.md
ls .agent/skills/audit-spec-pr/SKILL.md
```

No se necesitan skills externos (`npx`). Todo esta integrado en la skill.

---

## 3. Flujo General

```
main (produccion)
  └── develop (integracion)
        └── T{X}-S{Y}-{Z}_{slug}  ← rama por spec, PRs van a develop
```

```
  Etapa 1                Etapa 2              Etapa 3              Etapa 4
  IMPLEMENTAR            PRE-PR               REVIEW               POST-MERGE
  ─────────────          ───────              ──────               ──────────
  Desarrollador          Auditor (local)      Auditor (en PR)      Auditor (develop)
  Implementa spec        Verifica en rama     Code review formal   Regresion + registro
  Tests + calidad        Spec alignment       Decision final       
                         Diff analysis        APPROVE/REJECT       
```

### Resumen de prompts

| Etapa | Prompt exacto | Quien lo ejecuta |
|-------|---------------|------------------|
| 1. Implementar | `Procede con la spec {SPEC_ID} siguiendo la skill audit-spec-pr, Etapa 1` | Desarrollador |
| 2. Pre-PR | `Audita la spec {SPEC_ID} siguiendo la skill audit-spec-pr, Etapa 2 (Pre-PR)` | Auditor |
| 3. Review | `Audita la spec {SPEC_ID} siguiendo la skill audit-spec-pr, Etapa 3 (Review)` | Auditor |
| 4. Post-merge | `Audita la spec {SPEC_ID} siguiendo la skill audit-spec-pr, Etapa 4 (Post-Merge)` | Auditor |

> Reemplaza `{SPEC_ID}` con el ID de la spec, ej: `T2-S5-01`

---

## 4. Etapa 1: Implementar (Desarrollador)

### Cuando

Al comenzar a trabajar en una spec.

### Preparacion

```bash
git fetch origin && git checkout -b T{X}-S{Y}-{Z}_{slug} origin/develop
uv sync && uv sync --extra test
docker compose up -d
```

### Prompt

Copia y pega este prompt en OpenCode o Claude:

```text
Procede con la spec {SPEC_ID} siguiendo la skill audit-spec-pr, Etapa 1.

Recordatorio de los pasos:
1. CONTEXTO: Busca la spec (glob "specs/**/T{SPEC_ID}*"). Lee spec + skill referenciado.
   Verifica dependencias en estado done. Si falta alguna, PARA y reporta.
2. PLAN: Lista archivos a crear/modificar. Espera mi OK.
3. IMPLEMENTACION: Sigue AC + skill + Out of Scope. Arquitectura hexagonal.
4. PREPARACION ENTORNO: Ejecuta `uv sync` y `uv sync --extra test`. Levanta los servicios necesarios con `docker compose up -d` (BD, Redis, etc.) para evitar problemas al correr los tests.
5. TESTS: Tests para CADA AC. Happy path + errores + edge cases. Coverage >= 80%.
6. CALIDAD: Ejecuta ruff check, ruff format, mypy, pytest. 0 errores.
7. SPEC ALIGNMENT: Para cada AC -> IMPLEMENTADO / NO IMPLEMENTADO + evidencia.
8. CIERRE: Marcar spec como done. Agregar registro de implementacion.
```

### Que esperar

El agente va a:
1. Buscar y leer la spec automaticamente
2. Presentarte un plan para tu aprobacion
3. Implementar todo paso a paso
4. Ejecutar tests y calidad al final
5. Darte una tabla de AC cumplidos con evidencia
6. Agregar el registro de implementacion a la spec

### Despues del prompt

```bash
# Push a la rama
git add -A && git commit -m "feat: {SPEC_ID} - {descripcion}" && git push -u origin HEAD
```

---

## 5. Etapa 2: Pre-PR (Auditor en rama)

### Cuando

Despues de que el desarrollador pushea. Antes de abrir la PR.

### Preparacion

```bash
git fetch origin && git checkout T{X}-S{Y}-{Z}_{slug} && git pull
uv sync && uv sync --extra test
docker compose up -d
```

### Prompt

```
Audita la spec {SPEC_ID} siguiendo la skill audit-spec-pr, Etapa 2 (Pre-PR).

Ejecuta los 5 pasos en orden:
1. CONTEXTO: Lee spec + skill + instructions.md. Ejecuta git diff develop...HEAD.
   Resume: AC, Out of scope, dependencias, archivos esperados vs reales.
2. ANALISIS DE DIFF: Busca bugs, seguridad (OWASP), code smells, violaciones
   de arquitectura hexagonal, tecnologias prohibidas.
3. TESTS Y CALIDAD: Ejecuta pytest, ruff, mypy, coverage.
   Distingue fallos de esta spec vs pre-existentes.
4. SPEC ALIGNMENT: Tabla por cada AC con Estado/Evidencia/Test.
   + Out of Scope violations + Archivos extra.
5. DEPENDENCIAS: Verifica "Depende de" y "Bloqueante para" de la spec.
```

### Que esperar

El agente va a:
1. Analizar todos los cambios del diff
2. Ejecutar la suite completa de tests y calidad
3. Generar una tabla detallada de AC alignment
4. Identificar problemas antes de abrir la PR

### Despues del prompt

Si hay problemas: corregir y volver a ejecutar.
Si todo OK: abrir la PR a develop.

---

## 6. Etapa 3: Review (Auditor, PR abierta)

### Cuando

La PR ya esta abierta en GitHub contra develop.

### Prompt

```
Audita la spec {SPEC_ID} siguiendo la skill audit-spec-pr, Etapa 3 (Review).

Ejecuta las 4 revisiones:

3.1 CODE REVIEW (7 pasos):
    Comprension, Arquitectura, Logica, Seguridad, Testing, Naming/Style, Performance.
    Por paso: OK | ISSUE (archivo:linea) | SUGGESTION

3.2 ARCHITECTURE REVIEW:
    Clean Architecture, ADRs, patrones obligatorios (Repository, DI, Pydantic, structlog).

3.3 SECURITY REVIEW:
    OWASP Web + OWASP LLM (si aplica) + criterios bancarios.
    Severidad por finding: CRITICAL/HIGH/MEDIUM/LOW/INFO.

3.4 DECISION FINAL:
    Genera reporte con veredicto APPROVE / REQUEST CHANGES / COMMENT.
    Incluye: AC alignment, tests, architecture, security, issues bloqueantes, sugerencias.
```

### Que esperar

El agente va a:
1. Hacer un code review exhaustivo en 7 pasos
2. Verificar arquitectura contra ADRs
3. Hacer un security review completo
4. Darte un veredicto final con reporte

### Decision

| Veredicto | Significado |
|-----------|-------------|
| **APPROVE** | 100% AC, sin CRITICAL/HIGH, tests pasan, arquitectura ok |
| **REQUEST CHANGES** | Issues CRITICAL/HIGH o AC faltantes. Vuelve a Etapa 1. |
| **COMMENT** | Sugerencias menores. Se puede mergear. |

---

## 7. Etapa 4: Post-Merge

### Cuando

Despues de mergear la PR a develop.

### Preparacion

```bash
git checkout develop && git pull origin develop
uv sync && uv sync --extra test
docker compose up -d
```

### Prompt

```
Audita la spec {SPEC_ID} siguiendo la skill audit-spec-pr, Etapa 4 (Post-Merge).

1. REGRESION: Ejecuta suite completa en develop.
   pytest tests/ -x -v --tb=short --cov=src --cov-fail-under=80
   Reporta: tests nuevos OK, pre-existentes OK, regresiones, coverage.

2. INTEGRACION: Verifica endpoints, migraciones, docker compose, ruff/mypy.

3. REGISTRO: Agrega entrada a la tabla de seguimiento.
```

### Que esperar

El agente va a:
1. Ejecutar todos los tests en develop para detectar regresiones
2. Verificar que la integracion no rompio nada
3. Registrar la auditoria completada

---

## 8. Referencia Rapida

### Comandos manuales (si necesitas ejecutar algo sin el agente)

```bash
# Tests
uv run pytest tests/unit/ -x -v --tb=short
uv run pytest tests/integration/ -x -v --tb=short
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80

# Calidad
uv run ruff check src/ --fix && uv run ruff format src/
uv run mypy src/

# Diff contra develop
git diff develop...HEAD --stat
git diff develop...HEAD
```

### Skills por track

Al auditar, el agente carga automaticamente los skills del track de la spec:

| Track | Skills que se cargan |
|-------|---------------------|
| T1 Infra | `database-setup`, `docker-deployment`, `observability` |
| T2 Backend | `api-design`, `authentication`, `error-handling`, `testing-strategy` |
| T3 RAG Index | `rag-indexing`, `security-mirror`, `database-setup` |
| T4 RAG Gen | `rag-retrieval`, `langgraph`, `prompt-engineering`, `guardrails`, `chat-memory` |
| T5 Frontend | `frontend` |
| T6 QA | `testing-strategy`, `security-pentesting` |

### Criterios bloqueantes (REQUEST CHANGES)

| Criterio | Umbral |
|----------|--------|
| AC no implementado | Falta cualquier AC |
| Test critico falla | Auth, seguridad, core logic |
| Seguridad critica | SQL injection, passwords en logs, auth bypass |
| Tecnologia prohibida | Import de openai, cohere |
| Coverage < 70% | Archivos nuevos sin tests |
| Viola Clean Architecture | domain/ importa de infrastructure/ |
| Out of scope implementado | Funcionalidad de otra spec |

### ADRs clave

| ADR | Decision | Verificar |
|-----|----------|-----------|
| 001 | Monolith modular hexagonal | Capas: domain, application, infrastructure |
| 003 | REST + SSE | No WebSocket |
| 004 | PostgreSQL unificado | No multi-DB |
| 006 | JWT HTTPOnly | No localStorage |
| 008 | Ecosistema Google | Solo Gemini + Vertex AI |
| 009 | halfvec(768) | Float16 para embeddings |
| 010 | Langfuse + structlog | No print() |
| 011 | src/ como package root | Imports desde src/ |

### Metricas target

| Metrica | Target |
|---------|--------|
| Coverage | >= 80% |
| Ruff / Mypy | 0 errors |
| Recall@10 | > 0.85 |
| Faithfulness | > 0.90 |
| Latencia p95 | < 3s |

---

## 9. Registro de Auditoria

### Tabla de seguimiento

Mantener actualizada en este archivo o en un archivo separado:

| Spec ID | Sprint | Fecha | Auditor | Veredicto | PR # | Issues | Coverage | Notas |
|---------|--------|-------|---------|-----------|------|--------|----------|-------|
| | | | | | | | | |

---

## Apendice: Archivos de la skill

```
.opencode/skills/audit-spec-pr/
├── SKILL.md                           # Instrucciones completas de la skill
└── references/
    ├── adrs-reference.md              # Tabla de ADRs y como verificarlos
    ├── registro-template.md           # Templates de reporte y registro
    └── severidad-criterios.md         # Criterios CRITICAL/HIGH/MEDIUM/LOW

.agent/skills/audit-spec-pr/           # Espejo identico para Claude Code
└── (misma estructura)
```
