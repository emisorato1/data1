# Golden Evaluation Framework

Framework de evaluacion para el pipeline RAG enterprise, separado de los tests unitarios/integracion.

---

## 1. Que es un Golden Evaluation Dataset

Un **golden dataset** es un conjunto curado de pares input/expected_output que representan el comportamiento esperado del sistema. A diferencia de los tests unitarios que validan funciones individuales, el golden dataset evalua el comportamiento end-to-end del pipeline RAG.

### Golden vs Synthetic

| Aspecto | Golden Dataset | Synthetic Dataset |
|---------|---------------|-------------------|
| Creacion | Curado manualmente por domain experts | Generado automaticamente (RAGAS Synthesizer, DeepEval) |
| Versionado | Inmutable una vez promovido, versionado en git | Descartable, se regenera en cada corrida |
| Confiabilidad | Alta — validado contra documentacion fuente | Variable — puede contener artefactos del generador |
| Uso | Baseline medible para detectar regresiones | Exploracion de edge cases, stress testing |

### Gold vs Silver

Un dataset es **silver** mientras esta en proceso de revision. Se promueve a **gold** cuando un domain expert valida cada expected_output contra la documentacion fuente y aprueba la promocion en `manifest.json`.

---

## 2. Por que separar `evals/` de `tests/`

| Aspecto | `tests/` (tradicional) | `evals/` (RAG evaluation) |
|---------|----------------------|--------------------------|
| Determinismo | Deterministico — misma entrada = misma salida | No-deterministico — LLM genera respuestas variables |
| Costo | Cero (mocks, fixtures) | Alto (LLM API calls reales por sample) |
| Frecuencia | Cada commit (CI) | Manual o scheduled (pre-release, post-calibracion) |
| Assertion | Exact match, exceptions | Thresholds (score > 0.8), semantic similarity |
| Timeout | 30s por test | 120s+ por test (LLM latency) |
| Dependencias | Mocks, TestContainers | Servicios reales: LLM, vector DB, embeddings |

Esta separacion es la practica recomendada por:

- **RAGAS**: Separa `EvaluationDataset` del test suite, ejecuta evaluaciones como scripts independientes
- **DeepEval**: Distingue entre `Golden` (dataset curado) y `LLMTestCase` (instancia de evaluacion en runtime)
- **LangSmith**: Usa datasets remotos con `@pytest.mark.langsmith`, separados de pytest standard

---

## 3. Frameworks de referencia

### RAGAS

Metricas estandar de evaluacion RAG:

- **faithfulness**: ¿La respuesta esta soportada por el contexto recuperado?
- **answer_relevancy**: ¿La respuesta es relevante a la pregunta?
- **context_precision**: ¿Los chunks recuperados son precisos?
- **context_recall**: ¿Se recuperaron todos los chunks necesarios?

Formato: `EvaluationDataset` con `SingleTurnSample(user_input, response, retrieved_contexts, reference)`.

### DeepEval

- **Golden**: Solo input + expected_output (sin actual_output). Se llena en runtime como `LLMTestCase`
- Integracion nativa con pytest via `assert_test(test_case, [metric])`
- Metricas: `FaithfulnessMetric`, `AnswerRelevancyMetric`, `GEval` (custom)

### LangSmith

- Datasets remotos con upload/download
- 4 dimensiones: correctness, relevance, groundedness, retrieval relevance
- Plugin pytest: `@pytest.mark.langsmith` para ejecucion aislada

### Mapeo a nuestras categorias

| Nuestra categoria | RAGAS | DeepEval | LangSmith |
|-------------------|-------|----------|-----------|
| retrieval_accuracy | context_precision, context_recall | ContextualRelevancyMetric | retrieval relevance |
| faithfulness | faithfulness | FaithfulnessMetric | groundedness |
| memory | — (custom) | — (custom) | — (custom) |
| guardrails | — (custom) | — (custom) | — (custom) |
| topic_classification | — (custom) | — (custom) | — (custom) |

---

## 4. Estructura del directorio

```
evals/
├── __init__.py
├── conftest.py                        # Loaders de datasets, fixtures, markers
├── run_eval.py                        # Entry point: python -m evals.run_eval
├── datasets/
│   └── golden/
│       ├── manifest.json              # Version, revisor, conteos por categoria
│       ├── retrieval_accuracy.json    # 18 preguntas: conocimiento documental
│       ├── memory_shortterm.json      # 9 preguntas: 3 cadenas multi-turno
│       ├── memory_episodic.json       # 6 preguntas: 3 pares cross-session
│       ├── guardrails_input.json      # 9 preguntas: injection, jailbreak, extraction
│       ├── topic_classification.json  # 8 preguntas: on/off topic, saludos
│       ├── guardrails_output.json     # 6 preguntas: PII detection, false positives
│       └── system_prompt_behavior.json # 6 preguntas: idioma, fallback, smuggling
├── runner/
│   ├── __init__.py
│   ├── api_client.py                  # Auth, session, SSE parsing
│   ├── evaluator.py                   # Logica de evaluacion por expected_behavior
│   ├── reporter.py                    # Generacion reportes JSON + Markdown
│   └── langfuse_reporter.py           # Envio de scores a Langfuse (opcional)
├── metrics/
│   ├── __init__.py
│   └── custom_metrics.py             # context_retention_rate, topic_boundary_accuracy, etc.
├── experiments/                       # .gitignore: resultados timestamped
├── test_retrieval.py                  # Evalua retrieval accuracy y citaciones
├── test_guardrails.py                 # Evalua input/output guardrails
├── test_topic_boundary.py            # Evalua clasificacion de dominio
├── test_memory.py                    # Evalua short-term y episodic
└── test_system_prompt.py             # Evalua comportamiento del prompt
```

### manifest.json

El manifest es el punto de entrada del dataset. Contiene:

- `version`: Versionado semantico del dataset (1.0.0)
- `status`: `silver` (en revision) o `gold` (validado)
- `reviewer`: Quien valido el dataset
- `categories`: Mapa de categoria → archivo + conteo
- `total_samples`: Total de muestras (62)

### experiments/

Directorio gitignored donde se guardan los resultados de cada corrida de evaluacion con timestamp. Permite comparar resultados entre corridas sin contaminar el repositorio.

---

## 5. Formato de datos por categoria

### Single-turn (retrieval, guardrails output, system prompt)

```json
{
  "id": "RA-001",
  "input": "¿Pregunta del usuario?",
  "expected_output": "Respuesta esperada",
  "expected_behavior": "exact_match|contains_all|semantic_match|negation",
  "source_document": "Documento fuente.pdf",
  "difficulty": "easy|medium|hard",
  "tags": ["categoria", "subcategoria"]
}
```

### Multi-turn (memoria short-term)

```json
{
  "id": "MS-001",
  "chain": 1,
  "scenario": "Descripcion del escenario",
  "turns": [
    {"role": "user", "content": "Mensaje del usuario"},
    {"role": "assistant", "expected_behavior": "acknowledge_context"},
    {"role": "user", "content": "Siguiente mensaje"},
    {"role": "assistant", "expected_contains": ["termino1", "termino2"]}
  ]
}
```

### Cross-session (memoria episodica)

```json
{
  "id": "ME-001",
  "pair": 1,
  "session": "S1",
  "phase": "store",
  "input": "Instruccion o dato del usuario",
  "expected_behavior": "store_preference",
  "memory_type": "instruccion_explicita"
}
```

### Adversarial (guardrails input)

```json
{
  "id": "GI-001",
  "input": "Texto adversarial",
  "expected_behavior": "block|deflect",
  "expected_category": "PROMPT_INJECTION|JAILBREAK|QUERY_TOO_LONG|CONFIG_EXTRACTION",
  "should_not_contain": ["texto", "que", "no", "debe", "aparecer"]
}
```

---

## 6. Ciclo de vida del dataset

### Creacion

1. Identificar gap de cobertura (nueva funcionalidad, regresion detectada, edge case)
2. Escribir sample siguiendo el formato de la categoria
3. Asignar ID siguiendo la convencion (ver seccion 7)
4. Agregar al archivo JSON correspondiente

### Revision

1. Domain expert valida `expected_output` contra documentacion fuente
2. Verificar que `source_document` existe en `tests/data/demo/`
3. Ejecutar eval para confirmar que el sample es evaluable

### Promocion

1. Actualizar `manifest.json`: incrementar `version` y `count`
2. Cambiar `status` de `silver` a `gold` tras aprobacion
3. Registrar `reviewer` y `last_reviewed`

### Mantenimiento

- Cuando cambian documentos fuente → actualizar `expected_output` correspondientes
- Cuando se modifican guardrails → verificar alineacion de `expected_category`
- Cuando se recalibran thresholds → revisar `expected_behavior`

### Expansion

- Agregar samples cuando se identifican nuevos edge cases
- Agregar samples post-regresion para evitar recurrencia
- Mantener balance entre categorias

---

## 7. Como agregar nuevas preguntas

### Convencion de IDs

| Prefijo | Categoria | Rango actual |
|---------|-----------|-------------|
| `RA-` | Retrieval Accuracy | RA-001 a RA-018 |
| `MS-` | Memory Short-term | MS-001 a MS-009 |
| `ME-` | Memory Episodic | ME-001 a ME-006 |
| `GI-` | Guardrails Input | GI-001 a GI-009 |
| `TC-` | Topic Classification | TC-001 a TC-008 |
| `GO-` | Guardrails Output | GO-001 a GO-006 |
| `SP-` | System Prompt | SP-001 a SP-006 |

### Paso a paso

1. **Elegir categoria**: Determinar a que dimension de evaluacion pertenece
2. **Asignar ID**: Usar el siguiente numero disponible (e.g., `RA-019`)
3. **Completar campos**: Seguir el formato de la categoria (ver seccion 5)
4. **Actualizar manifest**: Incrementar `count` de la categoria y `total_samples`
5. **Ejecutar eval**: `pytest evals/test_{categoria}.py -v` para verificar estructura
6. **Revisar resultado**: Confirmar que el test pasa sin errores

### Ejemplo: agregar pregunta de retrieval

```json
{
  "id": "RA-019",
  "input": "¿Que documentacion necesito para solicitar una cuenta sueldo?",
  "expected_output": null,
  "expected_behavior": "semantic_match",
  "source_document": "CS001 - Manual del producto.docx",
  "difficulty": "medium",
  "tags": ["cuenta_sueldo", "documentacion"]
}
```

Luego actualizar `manifest.json`:
```json
"retrieval_accuracy": { "file": "retrieval_accuracy.json", "count": 19, "id_prefix": "RA" }
```
Y `"total_samples": 63`.

---

## 8. Metricas y thresholds

### Por categoria

| Categoria | Metricas | Threshold target |
|-----------|----------|-----------------|
| Retrieval accuracy | context_precision, context_recall, answer_relevancy (RAGAS) | > 0.8 |
| Faithfulness | faithfulness (RAGAS), hallucination_rate (custom) | > 0.8 |
| Memory short-term | context_retention_rate, anaphora_resolution (custom) | > 0.7 |
| Memory episodic | preference_recall, pii_sanitization_rate (custom) | 100% PII sanitized |
| Guardrails input | Precision, recall por categoria de amenaza | > 0.95 |
| Topic classification | Accuracy, false_positive_rate, false_negative_rate | > 0.90 accuracy |
| Guardrails output | PII detection precision/recall, false_positive_rate | > 0.95 precision |
| System prompt | Compliance rate por regla | 100% |

### Metricas RAGAS vs custom

- **RAGAS estandar**: faithfulness, answer_relevancy, context_precision, context_recall — cubren retrieval + generacion
- **Custom**: context_retention_rate, anaphora_resolution, topic_boundary_accuracy, memory_recall, pii_sanitization_rate — cubren memoria, clasificacion y guardrails

### Interpretacion de scores

| Score | Significado | Accion |
|-------|------------|--------|
| > 0.9 | Excelente | Monitorear, no requiere accion |
| 0.8 - 0.9 | Bueno | Aceptable, revisar outliers |
| 0.7 - 0.8 | Aceptable | Investigar samples fallidos |
| < 0.7 | Requiere atencion | Diagnosticar causa raiz, recalibrar |

---

## 9. Como ejecutar evaluaciones

### Prerequisitos

- Variables de entorno configuradas (`.env`): `GOOGLE_API_KEY`, `DATABASE_URL`, `LANGFUSE_*`
- Servicios activos: PostgreSQL con pgvector, Redis
- Datos demo indexados: documentos de `tests/data/demo/` cargados en vector store

### Comandos

```bash
# Suite completa de evaluacion
pytest evals/ -m eval --timeout=120

# Por categoria
pytest evals/test_retrieval.py -v
pytest evals/test_guardrails.py -v
pytest evals/test_topic_boundary.py -v
pytest evals/test_memory.py -v
pytest evals/test_system_prompt.py -v

# Sample especifico por ID
pytest evals/test_retrieval.py -k "RA_001" -v

# Tests normales (CI, sin cambios)
pytest tests/ -m "not slow"
```

### Interpretacion de resultados

- **PASSED**: El sample cumple con la estructura y validacion esperada
- **FAILED**: Revisar el assertion que fallo — puede ser un cambio en el pipeline o un sample desactualizado
- Los resultados detallados se guardan en `evals/experiments/` con timestamp

### Ejecucion contra API desplegada (T6-S7-02b)

El runner `evals/runner/` ejecuta las preguntas del golden dataset contra la API real:

```bash
# Ejecutar TODO (70 preguntas, incluyendo multi-turn y cache)
# Por defecto asume API en http://localhost:8000 con credenciales locales
uv run python -m evals.run_eval

# Con API remota 
EVAL_API_URL=https://api.example.com EVAL_USER_EMAIL=admin@banco.com EVAL_USER_PASSWORD=secret uv run python -m evals.run_eval

# Ejecutar categorias especificas
EVAL_CATEGORIES=retrieval_accuracy,guardrails_input python -m evals.run_eval

# Con timeout personalizado (segundos por pregunta)
EVAL_TIMEOUT=90 python -m evals.run_eval

# Con Langfuse (opcional)
export LANGFUSE_PUBLIC_KEY=pk-...
export LANGFUSE_SECRET_KEY=sk-...
export LANGFUSE_HOST=https://langfuse.example.com
python -m evals.run_eval
```

Los reportes se guardan en `evals/experiments/{run_id}/`:
- `results.json` — reporte JSON detallado con resultados por sample
- `report.md` — reporte Markdown con tablas comparativas y seccion de failures

Variables de entorno:

| Variable | Requerida | Default | Descripcion |
|----------|-----------|---------|-------------|
| `EVAL_API_URL` | No | `http://localhost:8000` | URL base del backend |
| `EVAL_USER_EMAIL` | No | `admin@banco.com` | Email para autenticacion |
| `EVAL_USER_PASSWORD` | No | `admin123!` | Password para autenticacion |
| `EVAL_CATEGORIES` | No | `all` | Categorias separadas por coma |
| `EVAL_TIMEOUT` | No | `60` | Timeout en segundos por pregunta |
| `LANGFUSE_PUBLIC_KEY` | No | — | Activa integracion Langfuse |
| `LANGFUSE_SECRET_KEY` | No | — | Activa integracion Langfuse |
| `LANGFUSE_HOST` | No | — | Host de Langfuse |

---

## 10. Integracion con el proyecto

### T3-S5-01 (RAGAS DAG)

El golden dataset `retrieval_accuracy.json` puede ser referenciado desde el DAG de evaluacion programada como source de pares question/ground_truth.

### T4-S9-02 (Faithfulness Scoring)

Las metricas de faithfulness del dataset se comparan contra el scoring en runtime del `faithfulness_judge.py` para detectar divergencias.

### Langfuse

Los resultados de cada corrida de evaluacion se envian como scores al trace correspondiente, permitiendo tracking historico de calidad.

### Cuando ejecutar

- **Pre-release**: Antes de cada release para detectar regresiones
- **Post-calibracion**: Despues de ajustar parametros RAG (top-k, thresholds, system prompt)
- **Post-guardrail changes**: Despues de modificar patrones de `input_validator.py` o `pii_detector.py`
- **Post-document update**: Cuando cambian los documentos fuente en `tests/data/demo/`
