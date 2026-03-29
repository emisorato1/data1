# T6-S7-02b: Script runner de evaluacion golden dataset contra API desplegada

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco, team) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T6-S8-01 |
| Depende de | T6-S7-02 (done) |
| Skill | `testing-strategy/SKILL.md` + `observability/SKILL.md` |
| Estimacion | M (2-4h) |

> Extiende T6-S7-02 (golden dataset estatico) con un runner que ejecuta las preguntas contra la API real desplegada en Kubernetes, validando comportamiento end-to-end del pipeline RAG con vectores reales en Cloud SQL.

## Contexto

T6-S7-02 creo un golden dataset de 62 preguntas y tests que validan la *estructura* del dataset. Sin embargo, para evaluar el comportamiento real del pipeline RAG se necesita enviar las preguntas al endpoint de chat de la API desplegada, capturar las respuestas streaming (SSE) y compararlas contra los `expected_output`, `expected_behavior` y `should_not_contain` definidos en cada sample.

La API usa autenticacion por HTTPOnly cookies (JWT) y responde con Server-Sent Events (SSE) con eventos `token`, `done`, `error` y `guardrail_blocked`.

## Spec

Crear un script runner en `evals/` que se conecte a la API desplegada (URL configurable por variable de entorno), se autentique, ejecute las preguntas single-turn del golden dataset, y genere reportes en JSON, Markdown y Langfuse.

### Alcance: categorias single-turn (47 preguntas)

| Categoria | Archivo | Preguntas | Validacion |
|-----------|---------|-----------|------------|
| Retrieval Accuracy | `retrieval_accuracy.json` | 18 | `expected_output`, `expected_behavior`, `source_document` |
| Guardrails Input | `guardrails_input.json` | 9 | `expected_behavior` (block/deflect), `expected_category`, `should_not_contain` |
| Topic Classification | `topic_classification.json` | 8 | `expected_classification`, `expected_behavior` |
| Guardrails Output | `guardrails_output.json` | 6 | `expected_behavior` (redact/block/allow), `should_not_contain` |
| System Prompt | `system_prompt_behavior.json` | 6 | `expected_behavior`, `should_not_contain` |

**Out of scope de este script**: categorias multi-turno (`memory_shortterm.json`) y cross-session (`memory_episodic.json`). Requieren orquestacion de sesiones y turnos secuenciales — spec futura.

### Configuracion

Variables de entorno:

| Variable | Requerida | Default | Descripcion |
|----------|-----------|---------|-------------|
| `EVAL_API_URL` | Si | — | URL base del backend (ej. `https://api.example.com`, `http://localhost:8000`) |
| `EVAL_USER_EMAIL` | Si | — | Email del usuario para autenticacion |
| `EVAL_USER_PASSWORD` | Si | — | Password del usuario |
| `EVAL_CATEGORIES` | No | `all` | Categorias a ejecutar, separadas por coma (ej. `retrieval_accuracy,guardrails_input`) |
| `EVAL_TIMEOUT` | No | `60` | Timeout en segundos por pregunta |
| `LANGFUSE_PUBLIC_KEY` | No | — | Si presente, envia scores a Langfuse |
| `LANGFUSE_SECRET_KEY` | No | — | Si presente, envia scores a Langfuse |
| `LANGFUSE_HOST` | No | — | Host de Langfuse |

### Flujo del script

```
1. Leer configuracion (env vars)
2. POST /api/v1/auth/login → obtener cookies de sesion (access_token)
3. Para cada categoria habilitada:
   a. Cargar samples del JSON correspondiente
   b. Para cada sample:
      i.   POST /api/v1/conversations → crear conversacion
      ii.  POST /api/v1/conversations/{id}/messages con {"message": sample.input}
      iii. Parsear SSE stream: acumular tokens, capturar evento done (sources, message_id)
      iv.  Evaluar respuesta contra criterios del sample
      v.   Registrar resultado (pass/fail, respuesta, tiempo, sources)
   c. Calcular metricas por categoria
4. Generar reporte JSON detallado
5. Generar reporte Markdown con tablas comparativas
6. Enviar scores a Langfuse (si configurado)
7. Imprimir resumen en terminal
```

### Parseo SSE

El endpoint responde con Server-Sent Events:

- `event: token` → `{"content": "..."}` — acumular contenido
- `event: done` → `{"sources": [...], "message_id": "..."}` — fin del stream
- `event: error` → `{"code": "...", "message": "..."}` — error
- `event: guardrail_blocked` → `{"content": "..."}` — respuesta sanitizada por guardrail

Para guardrails input (block esperado), un `event: guardrail_blocked` o respuesta con mensaje de bloqueo predefinido cuenta como **pass**.

### Evaluacion de respuestas por tipo de validacion

| `expected_behavior` | Logica de evaluacion |
|---------------------|---------------------|
| `exact_match` | `expected_output.lower()` presente en la respuesta (case-insensitive substring) |
| `contains_all` | Todos los valores de `expected_output` (split por coma) presentes en respuesta |
| `semantic_match` | Respuesta no vacia, relevante al `source_document`, sin `should_not_contain` |
| `negation` | La respuesta contiene negacion explicita (\"no aplica\", \"no es posible\", etc.) |
| `block` | Respuesta es un mensaje de bloqueo predefinido O evento `guardrail_blocked` |
| `deflect` | Respuesta no contiene ninguno de los `should_not_contain` |
| `redact` | Los tokens de `expected_redacted_contains` (`[DNI]`, `[CUIT]`, etc.) aparecen en respuesta |
| `allow` | Los `should_not_contain` surrogate tokens NO aparecen en respuesta |
| `respond_in_spanish` | Respuesta en espanol (heuristica: no contiene patrones ingles/portugues dominantes) |
| `fallback_no_context` | Contiene frase de fallback Y no contiene `should_not_contain` |
| `partial_response` | Respuesta no vacia y no contiene todos los `should_not_contain` |
| `greeting` / `greeting_with_help` | Respuesta no vacia (saludo corporativo) |
| `fail_open` | Respuesta no vacia (sistema no bloqueo) |

### Formato de reporte JSON

```json
{
  "run_id": "uuid",
  "timestamp": "2026-03-18T16:00:00Z",
  "api_url": "https://api.example.com",
  "duration_seconds": 180,
  "summary": {
    "total": 47,
    "passed": 42,
    "failed": 5,
    "pass_rate": 0.893
  },
  "categories": {
    "retrieval_accuracy": {
      "total": 18,
      "passed": 16,
      "failed": 2,
      "pass_rate": 0.889
    }
  },
  "results": [
    {
      "id": "RA-001",
      "category": "retrieval_accuracy",
      "input": "...",
      "expected_output": "30 dias",
      "actual_output": "...",
      "sources": ["008 RRHH - Salud..."],
      "verdict": "pass",
      "reason": "exact_match found",
      "duration_ms": 2340
    }
  ]
}
```

### Formato de reporte Markdown

```markdown
# Eval Run: {run_id}
**Fecha**: {timestamp} | **API**: {api_url} | **Duracion**: {duration}s

## Resumen
| Categoria | Total | Pass | Fail | Rate |
|-----------|-------|------|------|------|
| retrieval_accuracy | 18 | 16 | 2 | 88.9% |
| ... | ... | ... | ... | ... |
| **TOTAL** | **47** | **42** | **5** | **89.3%** |

## Detalle: Retrieval Accuracy
| ID | Pregunta | Expected | Actual (truncado) | Veredicto |
|----|----------|----------|--------------------|-----------|
| RA-001 | ¿Cual es el periodo...? | 30 dias | ...30 dias... | PASS |
| RA-005 | ¿Que pasa si...? | queda ineditable | ...no se encontro... | FAIL |

## Failures
| ID | Categoria | Razon del fallo |
|----|-----------|----------------|
| RA-005 | retrieval_accuracy | expected 'queda ineditable' not found in response |
```

### Integracion Langfuse

Si las variables `LANGFUSE_PUBLIC_KEY` y `LANGFUSE_SECRET_KEY` estan configuradas:

1. Crear un trace por corrida de evaluacion con metadata (run_id, api_url, timestamp)
2. Para cada sample evaluado, enviar un score al trace:
   - `name`: ID del sample (ej. `RA-001`)
   - `value`: 1.0 (pass) o 0.0 (fail)
   - `comment`: razon del veredicto
3. Enviar scores agregados por categoria:
   - `name`: `eval_{categoria}_pass_rate` (ej. `eval_retrieval_accuracy_pass_rate`)
   - `value`: pass_rate (0.0 a 1.0)

### Estructura de archivos

```
evals/
├── runner/
│   ├── __init__.py
│   ├── api_client.py          # Auth, session management, SSE parsing
│   ├── evaluator.py           # Logica de evaluacion por tipo de comportamiento
│   ├── reporter.py            # Generacion de reportes JSON + Markdown
│   └── langfuse_reporter.py   # Envio de scores a Langfuse (opcional)
├── run_eval.py                # Entry point: python -m evals.run_eval
└── ...                        # (archivos existentes de T6-S7-02)
```

### Ejecucion

```bash
# Configurar variables
export EVAL_API_URL=https://api.example.com
export EVAL_USER_EMAIL=test@example.com
export EVAL_USER_PASSWORD=secret

# Ejecutar todas las categorias single-turn
python -m evals.run_eval

# Ejecutar categorias especificas
EVAL_CATEGORIES=retrieval_accuracy,guardrails_input python -m evals.run_eval

# Con Langfuse
export LANGFUSE_PUBLIC_KEY=pk-...
export LANGFUSE_SECRET_KEY=sk-...
export LANGFUSE_HOST=https://langfuse.example.com
python -m evals.run_eval
```

Los reportes se guardan en `evals/experiments/{run_id}/`:
- `results.json` — reporte JSON detallado
- `report.md` — reporte Markdown con tablas

## Acceptance Criteria

- [x] Modulo `evals/runner/` con `api_client.py`, `evaluator.py`, `reporter.py`, `langfuse_reporter.py`
- [x] `evals/run_eval.py` como entry point ejecutable con `python -m evals.run_eval`
- [x] Autenticacion funcional contra API desplegada via `POST /api/v1/auth/login` con manejo de cookies
- [x] Parseo correcto de SSE stream: acumulacion de tokens, captura de evento `done` con sources
- [x] Evaluacion de las 5 categorias single-turn (47 preguntas) con logica de validacion por `expected_behavior`
- [x] Reporte JSON detallado con resultados por sample, metricas por categoria y resumen global
- [x] Reporte Markdown con tablas comparativas (pregunta, expected, actual, veredicto) y seccion de failures
- [x] Integracion Langfuse opcional: trace por corrida, score por sample, scores agregados por categoria
- [x] Configuracion 100% por variables de entorno (no credenciales hardcodeadas)
- [x] Reportes guardados en `evals/experiments/{run_id}/` (directorio ya gitignored)
- [x] Manejo de errores: timeout por pregunta, fallos de conexion, refresh de token si expira mid-run

## Archivos a crear/modificar

- `evals/runner/__init__.py` (crear)
- `evals/runner/api_client.py` (crear)
- `evals/runner/evaluator.py` (crear)
- `evals/runner/reporter.py` (crear)
- `evals/runner/langfuse_reporter.py` (crear)
- `evals/run_eval.py` (crear)
- `evals/README.md` (modificar — agregar seccion de ejecucion contra API)

## Decisiones de diseno

- **URL configurable por env var**: Permite apuntar al cluster K8s (dominio publico), a un port-forward local, o a localhost para desarrollo. Sin acoplamiento a infraestructura especifica.
- **Solo single-turn**: Las categorias multi-turno y cross-session requieren orquestacion de sesiones y turnos secuenciales que agregan complejidad significativa. Se deja para una spec futura una vez validado el runner basico.
- **Cookies para auth (no bearer token)**: La API usa HTTPOnly cookies, asi que el script usa una session `httpx` que persiste cookies automaticamente entre requests.
- **Conversacion por pregunta**: Cada sample crea una conversacion nueva para aislar contexto y evitar contaminacion entre preguntas.
- **Tres reportes complementarios**: JSON para procesamiento programatico, Markdown para revision humana, Langfuse para tracking historico y tendencias.
- **`evals/runner/` como submodulo**: Separado de los tests de estructura (T6-S7-02) para mantener responsabilidades claras — los tests validan el dataset, el runner ejecuta contra la API.

## Out of scope

- Categorias multi-turno (`memory_shortterm.json`) y cross-session (`memory_episodic.json`)
- Evaluacion con metricas RAGAS (faithfulness, context_precision) — requiere acceso a chunks internos
- Ejecucion automatica en CI/CD
- Reintentos automaticos de samples fallidos
- Comparacion entre corridas (diff entre reportes)
- Dashboard visual de resultados

## Registro de implementacion

| Campo | Valor |
|-------|-------|
| Fecha | 2026-03-18 |
| Branch | `T6-S7-02_golden-eval-dataset` |
| Tests | 52 unit tests (87% coverage en evals/runner/) |
| Linting | ruff check + ruff format: 0 errores |
| Types | mypy: 0 errores (8 archivos) |
| Regresion | 0 regresiones (fallos pre-existentes: e2e/Gemini API, demo docs count) |

### Archivos creados
- `evals/runner/__init__.py`
- `evals/runner/__main__.py`
- `evals/runner/api_client.py` — Auth HTTPOnly cookies, SSE parsing, token refresh
- `evals/runner/evaluator.py` — 13 evaluadores por `expected_behavior` tipo
- `evals/runner/reporter.py` — JSON + Markdown report generation
- `evals/runner/langfuse_reporter.py` — Optional Langfuse score upload
- `evals/run_eval.py` — Entry point con CLI via env vars
- `tests/unit/test_eval_runner.py` — 52 tests cubriendo evaluator, SSE, reporter, langfuse

### Archivos modificados
- `evals/README.md` — Seccion de ejecucion contra API + estructura actualizada
- `specs/sprint-7/T6-S7-02b_eval-runner-api.md` — Estado → done, ACs marcados
