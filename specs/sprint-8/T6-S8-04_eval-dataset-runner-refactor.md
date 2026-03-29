# T6-S8-04: Refacción de evaluaciones — ambiguous_queries, cache_behavior, memory_shortterm, memory_episodic

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | — |
| Depende de | T6-S7-02 (done), T6-S7-02b (done) |
| Skill | `testing-strategy/SKILL.md` |
| Estimacion | L (4-8h) |

> Las 4 categorías de evaluación creadas en T6-S7-02 y orquestadas por T6-S7-02b no producen resultados útiles. Esta spec corrige los datasets, evaluadores y runners para que midan comportamiento real de la aplicación.

## Contexto

T6-S7-02 creó el golden dataset (70 samples) y T6-S7-02b el runner que ejecuta las preguntas contra la API. Sin embargo, 4 de las 9 categorías no son efectivas:

| Categoría | Problema |
|-----------|----------|
| `ambiguous_queries` (6 samples) | Evaluador pasa con cualquier `?` en la respuesta. Sin `expected_contains`. Sin test file ni fixture en conftest. |
| `cache_behavior` (2 samples) | Testea semantic cache que **no existe** en la app. Validación puramente temporal (flaky). Solo 2 samples. Sin test file ni fixture. |
| `memory_shortterm` (9 samples) | 5/9 samples sin `expected_contains` → pasan con cualquier respuesta no vacía. Métricas custom (`context_retention_rate`) definidas pero no usadas por el runner. Solo evalúa el último turno de la cadena. |
| `memory_episodic` (6 samples) | Campos `validation` y `should_not_contain` ignorados por el evaluador. Fase "store" siempre pasa (non-empty). ME-006 envía meta-instrucción en vez de pregunta real. Solo 3 pares. |

Las preguntas se basan en los 22 documentos bancarios demo indexados en `tests/data/demo/`.

## Spec

Refaccionar los 4 datasets, mejorar el evaluador y runner, y agregar los test files faltantes para que estas evaluaciones midan comportamiento real.

### 1. Datasets JSON (4 archivos a reescribir)

#### `ambiguous_queries.json` — 6 → 10 samples

Agregar campos de validación y 4 samples nuevos:

| Campo nuevo | Descripción |
|-------------|-------------|
| `min_options` | Mínimo de opciones/alternativas que la respuesta debe ofrecer |
| `expected_contains_any` | Al menos uno de estos keywords debe aparecer (opciones relevantes al dominio) |

Samples nuevos basados en documentos demo:

| ID | Input | Ambigüedad | Keywords esperados |
|----|-------|------------|-------------------|
| AQ-007 | "¿Cuánto me sale?" | Costo de qué producto/servicio | paquete, tarjeta, préstamo, seguro |
| AQ-008 | "Quiero cambiar mi tarjeta" | TD vs TC, cambio vs reposición | débito, crédito |
| AQ-009 | "Necesito un certificado" | Laboral, médico, de haberes | trabajo, médico, haberes |
| AQ-010 | "¿Cuál es el límite?" | TD, TC o préstamo | tarjeta, débito, crédito, préstamo |

Samples existentes (AQ-001 a AQ-006): mantener `input` y agregar `min_options: 2`.

#### `cache_behavior.json` — 2 → 8 samples

**Rediseño**: el pass/fail se basa en **contenido correcto** (`expected_contains`), no solo tiempo. El tiempo se registra como métrica informativa hasta que se implemente semantic cache.

Cada sample es una pregunta de dato puntual verificable contra documentos:

| ID | Input | expected_contains | Documento fuente |
|----|-------|-------------------|------------------|
| CB-001 | ¿Cuál es el teléfono de la ART? | ["0800-888-0093"] | 008 RRHH - Salud |
| CB-002 | ¿Cuántas visitas gratis a la caja de seguridad por mes? | ["5"] | CS001 |
| CB-003 | ¿Cuántos días tengo para revocar un préstamo? | ["10"] | PP004 |
| CB-004 | ¿Dónde está el consultorio médico de Rosario? | ["San Lorenzo 1338"] | 008 RRHH - Salud |
| CB-005 | ¿Cuántos días de licencia por matrimonio? | ["12"] | 001 RRHH - Admin |
| CB-006 | ¿Cuánto tarda el cambio de límite provisorio de TD? | ["24", "48"] | TD002 |
| CB-007 | ¿Cuántos días de licencia por nacimiento tiene el padre? | ["20"] | 001 RRHH - Admin |
| CB-008 | ¿Hasta qué edad están cubiertos los hijos en la obra social? | ["21"] | 001 RRHH - Admin |

#### `memory_shortterm.json` — 9 → 12 samples (3 → 4 chains)

Agregar validación a los 5 samples que solo tienen `expected_behavior` sin `expected_contains`:

| ID | Campo agregado | Valor |
|----|----------------|-------|
| MS-003 | `expected_contains` | ["25 de Mayo 160"] |
| MS-005 | `expected_contains_any` | ["PIN", "blanqueo", "tarjeta de débito"] |
| MS-006 | `expected_contains_any` | ["IVR", "Banca Internet", "App", "BancoChat", "canal"] |
| MS-007 | `expected_contains_any` | ["Selecta", "baja", "retención"] |
| MS-008 | `expected_contains_any` | ["bonificación", "campaña", "retención"] |

Nueva **Chain 4** — Caja de seguridad (doc CS001):

| ID | Turno | Input | Validación |
|----|-------|-------|------------|
| MS-010 | T1 | "Quiero contratar una caja de seguridad, ¿qué necesito?" | `expected_contains_any: ["cuenta", "18", "antigüedad"]` |
| MS-011 | T2 | "¿Qué tamaños hay disponibles?" | `expected_contains_any: ["10x10", "tamaño", "medida"]` |
| MS-012 | T3 | "¿Cuántas veces puedo ir al mes sin cargo?" | `expected_contains: ["5"]` |

#### `memory_episodic.json` — 6 → 10 samples (3 → 5 pares)

Mejorar existentes:
- Agregar `expected_contains_any` a fases "store" para que no pasen solo con respuesta no vacía
- Cambiar ME-006 de meta-instrucción a pregunta real de compliance

| ID | Cambio |
|----|--------|
| ME-001 (store) | Agregar `expected_contains_any: ["viñeta", "lista", "entendido"]` |
| ME-003 (store) | Agregar `expected_contains_any: ["RRHH", "onboarding", "entendido"]` |
| ME-005 (store) | Agregar `expected_contains_any: ["compliance", "entendido"]` |
| ME-006 (recall) | Cambiar input a "¿Qué procedimientos de compliance debo seguir?". Agregar `expected_contains_any: ["compliance"]`, mantener `should_not_contain: ["32.456.789"]` |

Nuevos pares:

| ID | Sesión | Input | Validación |
|----|--------|-------|------------|
| ME-007 | S1 (store) | "Trabajo en la sucursal de Córdoba, soy gerente regional" | `store_preference`, `expected_contains_any: ["Córdoba", "gerente"]` |
| ME-008 | S2 (recall) | "¿Dónde puedo hacer un control médico?" | `personalize_by_role`, `expected_contains: ["25 de Mayo 160"]` |
| ME-009 | S1 (store) | "Me interesan los beneficios para mi familia" | `store_preference`, `expected_contains_any: ["beneficio", "familia"]` |
| ME-010 | S2 (recall) | "¿Qué novedades hay de RRHH?" | `personalize_by_role`, `expected_contains_any: ["beneficio", "familia", "guardería", "hijo"]` |

---

### 2. Evaluador (`evals/runner/evaluator.py`)

#### 2a. Nuevo campo `expected_contains_any` en `_eval_generic_contains`

Semántica: al menos **uno** de los keywords debe aparecer (a diferencia de `expected_contains` donde **todos** deben aparecer).

```python
expected_any = sample.get("expected_contains_any", [])
if expected_any:
    found_any = any(str(p).lower() in actual_lower for p in expected_any)
    if not found_any:
        return Verdict(passed=False, reason=f"none of {expected_any} found")
```

#### 2b. Mejorar `_eval_clarification_options`

Actual: pasa si hay `?`, `-` o `*`.
Nuevo:
1. Verificar respuesta no vacía
2. Verificar que contiene `?` (pregunta clarificadora)
3. Contar opciones (patrones: `- `, `• `, `* `, `\d+\.`, `\d+\)`)
4. Verificar `min_options` si presente en sample
5. Verificar `expected_contains_any` si presente
6. Verificar `should_not_contain` si presente

#### 2c. Nuevo evaluador `_eval_apply_preference`

Para ME-002 (recall de preferencia de formato viñetas):
1. Verificar `expected_contains_any` (contenido correcto)
2. Verificar que la respuesta usa formato lista/viñetas (buscar `- `, `• `, `* `, `\d+\.`)

Registrar: `_EVALUATORS["apply_preference"] = _eval_apply_preference`

---

### 3. Runner (`evals/run_eval.py`)

#### 3a. `_run_cache_behavior` — Validación de contenido

Actual: solo mide `duration_ms < 1500`.
Nuevo:
1. Enviar mensaje (prime)
2. Enviar mismo mensaje de nuevo (medir tiempo)
3. **Evaluar contenido** de la 2da respuesta contra `expected_contains` con `evaluate_sample`
4. Verdict = contenido correcto. Tiempo en `reason` como info.

#### 3b. `_run_memory_shortterm` — Evaluar todos los turnos

Actual: solo guarda `last_verdict` (sobrescribe intermedios).
Nuevo: acumular verdicts de **todos** los turnos asistente. Si alguno falla → fail global con detalle de cuál turno falló.

---

### 4. Fixtures (`evals/conftest.py`)

Agregar 2 fixtures faltantes:

```python
@pytest.fixture(scope="session")
def ambiguous_queries_dataset() -> list[dict[str, Any]]:
    return _load_golden("ambiguous_queries.json")["samples"]

@pytest.fixture(scope="session")
def cache_behavior_dataset() -> list[dict[str, Any]]:
    return _load_golden("cache_behavior.json")["samples"]
```

---

### 5. Test files nuevos

#### `evals/test_ambiguous.py`

| Test | Validación |
|------|-----------|
| `test_dataset_completeness` | 10 samples, IDs AQ-001..AQ-010 |
| `test_samples_have_required_fields` | id, input, expected_behavior, min_options, tags |
| `test_all_expect_clarification` | todos con behavior `clarification_options` |
| `test_min_options_reasonable` | todos min_options >= 2 |
| `test_tag_variety` | >= 6 tags específicos de ambigüedad |
| `test_option_keywords_present` | samples con `expected_contains_any` tienen >= 2 items |

#### `evals/test_cache.py`

| Test | Validación |
|------|-----------|
| `test_dataset_completeness` | 8 samples, IDs CB-001..CB-008 |
| `test_samples_have_required_fields` | id, input, expected_behavior, expected_contains, tags |
| `test_all_have_expected_contains` | todos con >= 1 item |
| `test_source_documents_referenced` | todos con source_document |
| `test_tag_coverage` | >= 4 tags de dominio distintos |

---

### 6. Test file actualizado (`evals/test_memory.py`)

| Cambio | De | A |
|--------|-----|---|
| `TestMemoryShortTerm.test_dataset_completeness` | 9 samples | 12 samples |
| `TestMemoryShortTerm.test_three_chains_present` | chains {1,2,3} | chains {1,2,3,4} |
| `TestMemoryEpisodic.test_dataset_completeness` | 6 samples | 10 samples |
| `TestMemoryEpisodic.test_three_pairs_present` | pairs {1,2,3} | pairs {1,2,3,4,5} |
| Nuevo: `test_all_assistant_turns_have_validation` | — | Verificar que todos los turns asistente tienen `expected_contains` o `expected_contains_any` |

---

### 7. Manifest (`evals/datasets/golden/manifest.json`)

Actualizar conteos:

| Categoría | Antes | Después |
|-----------|-------|---------|
| ambiguous_queries | 6 | 10 |
| cache_behavior | 2 | 8 |
| memory_shortterm | 9 | 12 |
| memory_episodic | 6 | 10 |
| **total_samples** | **70** | **86** |

---

## Acceptance Criteria

- [ ] `ambiguous_queries.json` con 10 samples, todos con `min_options` y `expected_behavior: clarification_options`
- [ ] `cache_behavior.json` con 8 samples, todos con `expected_contains` verificable contra documentos demo
- [ ] `memory_shortterm.json` con 12 samples (4 chains), **todos** los turns asistente con `expected_contains` o `expected_contains_any`
- [ ] `memory_episodic.json` con 10 samples (5 pares), fases store con validación y ME-006 con pregunta real
- [ ] `evaluator.py` soporta `expected_contains_any` (al menos uno debe matchear)
- [ ] `_eval_clarification_options` valida `min_options`, `expected_contains_any` y `should_not_contain`
- [ ] Nuevo evaluador `_eval_apply_preference` verifica formato viñetas/lista
- [ ] `_run_cache_behavior` evalúa contenido (no solo tiempo)
- [ ] `_run_memory_shortterm` evalúa **todos** los turnos asistente (no solo el último)
- [ ] `conftest.py` tiene fixtures `ambiguous_queries_dataset` y `cache_behavior_dataset`
- [ ] `test_ambiguous.py` creado con >= 6 tests de estructura
- [ ] `test_cache.py` creado con >= 5 tests de estructura
- [ ] `test_memory.py` actualizado con counts correctos (12 shortterm, 10 episodic)
- [ ] `manifest.json` actualizado (total_samples: 86)
- [ ] `pytest evals/ -v` pasa sin errores

## Archivos a crear/modificar

| Archivo | Acción |
|---------|--------|
| `evals/datasets/golden/ambiguous_queries.json` | Reescribir |
| `evals/datasets/golden/cache_behavior.json` | Reescribir |
| `evals/datasets/golden/memory_shortterm.json` | Reescribir |
| `evals/datasets/golden/memory_episodic.json` | Reescribir |
| `evals/runner/evaluator.py` | Modificar |
| `evals/run_eval.py` | Modificar |
| `evals/conftest.py` | Modificar |
| `evals/test_ambiguous.py` | **Crear** |
| `evals/test_cache.py` | **Crear** |
| `evals/test_memory.py` | Modificar |
| `evals/datasets/golden/manifest.json` | Modificar |

## Decisiones de diseño

- **`expected_contains_any` vs `expected_contains`**: Se introduce `expected_contains_any` (al menos uno debe matchear) como complemento a `expected_contains` (todos deben matchear). Esto permite validación flexible para respuestas donde cualquiera de N keywords válidos indica correcto comportamiento.
- **Cache: contenido > tiempo**: Sin semantic cache implementado, la validación temporal es inútil. Se valida contenido correcto y se registra tiempo como métrica informativa para cuando se implemente cache.
- **Evaluar todos los turnos**: Evaluar solo el último turno enmascaraba fallos en turnos intermedios. Ahora se acumulan y se falla si cualquier turno asistente no cumple.
- **ME-006 con pregunta real**: Enviar una meta-instrucción ("Verificar que la memoria no contenga DNI") no testea el sistema — testea si el bot interpreta meta-instrucciones. Se reemplaza por pregunta real de compliance con `should_not_contain` para PII.
- **Preguntas de dato puntual para cache**: Las preguntas de cache tienen respuestas verificables con datos exactos de los documentos, lo que permite validación determinista independiente del cache.

## Out of scope

- Implementación del semantic cache (feature no existente en la app)
- Evaluación con métricas RAGAS (faithfulness, context_precision)
- Cambios en categorías que ya funcionan (retrieval_accuracy, guardrails_input, guardrails_output, topic_classification, system_prompt_behavior)
- Dashboard de resultados de evaluación
- Ejecución automática en CI/CD

## Registro de Implementacion
**Fecha**: 2026-03-26 | **Rama**: develop

| Archivo | Accion | Motivo |
|---------|--------|--------|
| `evals/datasets/golden/ambiguous_queries.json` | Reescrito | 6→10 samples con min_options y expected_contains_any (AC-1) |
| `evals/datasets/golden/cache_behavior.json` | Reescrito | 2→8 samples con expected_contains y source_document (AC-2) |
| `evals/datasets/golden/memory_shortterm.json` | Reescrito | 9→12 samples, 3→4 chains, todos los turns con validacion (AC-3) |
| `evals/datasets/golden/memory_episodic.json` | Reescrito | 6→10 samples, 3→5 pares, ME-006 con pregunta real (AC-4) |
| `evals/runner/evaluator.py` | Modificado | expected_contains_any en _eval_generic_contains, _eval_clarification_options mejorado, _eval_apply_preference nuevo (AC-5,6,7) |
| `evals/run_eval.py` | Modificado | _run_cache_behavior valida contenido, _run_memory_shortterm evalua todos los turnos (AC-8,9) |
| `evals/conftest.py` | Modificado | Fixtures ambiguous_queries_dataset y cache_behavior_dataset (AC-10) |
| `evals/test_ambiguous.py` | Creado | 6 tests de estructura para ambiguous queries (AC-11) |
| `evals/test_cache.py` | Creado | 5 tests de estructura para cache behavior (AC-12) |
| `evals/test_memory.py` | Modificado | Counts actualizados (12/4/10/5), test_all_assistant_turns_have_validation (AC-13) |
| `evals/datasets/golden/manifest.json` | Modificado | Version 2.0.0, total_samples 87, counts actualizados (AC-14) |

### Notas de Implementacion
- El total real es 87 samples (no 86 como estimaba la spec) porque la suma correcta incluye guardrails_input=9.
- ruff check: 1 error SIM108 pre-existente en run_eval.py:60 (no modificado por esta spec).
- mypy: 2 errores pre-existentes en evaluator.py:68 y run_eval.py:251 (no modificados por esta spec).
- CB-006 usa `expected_contains_any` en vez de `expected_contains` porque la respuesta puede mencionar "24" o "48" horas indistintamente.
- ME-006 cambio de meta-instruccion ("Verificar que la memoria...") a pregunta real ("¿Que procedimientos de compliance debo seguir?") con should_not_contain para PII.
