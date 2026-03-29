# T6-S8-08: Respuesta natural a saludos y eliminación de warning de cuota GCP

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco) |
| Prioridad | Media |
| Estado | done |
| Bloqueante para | — |
| Depende de | T6-S8-07 (pendiente) — ambas specs modifican `rag_graph.py` y `classify_intent.py`; implementar en secuencia para evitar conflictos |
| Skill | `langgraph/SKILL.md`, `prompt-engineering/SKILL.md`, `docker-deployment/SKILL.md` |
| Estimacion | S (2-4h) |

> Reemplazar la respuesta estática hardcodeada para saludos por una generación conversacional con LLM, ampliar la detección de saludos para cubrir variantes conversacionales ("¿Cómo estás?", "¿Qué tal?"), y eliminar el `UserWarning` de cuota de GCP que aparece en cada inicialización del sistema.

## Contexto

### Problema 1: Respuesta hardcodeada y detección limitada de saludos

El sistema actual detecta saludos en `classify_intent_node` usando un set fijo de keywords (`_GREETING_KEYWORDS`). Cuando una query consiste **exclusivamente** en palabras de ese set, se clasifica como `saludo` y se enruta a `respond_blocked_node`, que retorna siempre la misma cadena estática:

```
¡Hola! Soy el asistente de documentación bancaria interna. ¿En qué puedo ayudarte hoy?
```

**Dos síntomas observados:**

#### Síntoma 1A — Respuesta inmutable ante cualquier saludo reconocido
El usuario diga "Hola", "Buenos días" o "Saludos", siempre recibe exactamente la misma frase. El sistema no distingue si el usuario pregunta "¿Cómo estás?" (espera respuesta conversacional) o simplemente saluda "Hola" (espera bienvenida). La frase fija degrada la percepción de naturalidad del asistente.

#### Síntoma 1B — Saludos conversacionales no son detectados y caen al pipeline RAG
Expresiones como "¿Cómo estás?", "¿Qué tal?", "¿Cómo te va?", "Buenas", "¿Todo bien?" **no contienen palabras del `_GREETING_KEYWORDS` set** (los tokens "como", "estas", "tal", "bien" no están incluidos). Estas queries pasan como `consulta`, entran al pipeline de retrieval, no recuperan documentos relevantes y retornan el mensaje de fallback genérico ("No encontré información suficiente…"), lo cual es una experiencia de usuario incorrecta para un saludo cordial.

**Flujo actual de "¿Cómo estás?":**
```
classify_intent ("consulta") → guardrail_input (SAFE) → retrieve (0 docs relevantes)
→ rerank → score_gate ("insuficiente") → respond_blocked (fallback genérico)
```

**Flujo actual de "Hola":**
```
classify_intent ("saludo") → guardrail_input (skip) → respond_blocked (string estática hardcodeada)
```

**Flujo esperado para ambos:**
```
classify_intent ("saludo") → respond_greeting (LLM genera respuesta natural y contextual)
```

El log del sistema evidencia el comportamiento actual:
```
guardrail_input: saludo, skipping validation
respond_blocked: query_type=saludo
chunk: {"content": "¡Hola! Soy el asistente de documentación bancaria interna. ¿En qué puedo ayudarte hoy?"}
```

### Problema 2: `UserWarning` de cuota de GCP en cada inicialización

Al inicializar cualquier cliente de Google Cloud (Gemini, Vertex AI, GCS), la librería `google.auth` emite una advertencia:

```
UserWarning: Your application has authenticated using end user credentials from
Google Cloud SDK without a quota project. You might receive a "quota exceeded"
or "API not enabled" error.
  warnings.warn(_CLOUD_SDK_CREDENTIALS_WARNING)
```

**Causa:** El proyecto usa **Application Default Credentials (ADC)** mediante credenciales de usuario de `gcloud auth application-default login` (política organizacional: no se permiten service account keys). Las credenciales ADC de usuario no tienen un `quota_project_id` asignado por defecto. La librería `google.auth` detecta esta ausencia y lanza el warning.

**Impacto:**
- Contamina los logs del sistema en cada arranque con warnings innecesarios.
- Puede confundir al equipo sobre el estado de la autenticación.
- El warning aparece en todos los entornos (dev, Docker) que usen ADC de usuario.

**Clientes GCP afectados** (todos utilizan ADC):
- `ChatGoogleGenerativeAI` / `GoogleGenerativeAIEmbeddings` — `src/infrastructure/llm/client.py`
- `genai.Client` (Vertex AI mode) — `src/infrastructure/rag/embeddings/gemini_embeddings.py` y `src/infrastructure/rag/retrieval/gemini_reranker.py`
- `storage.Client` (GCS) — `src/infrastructure/storage/gcs_client.py`
- `RankServiceClient` (Discovery Engine) — `src/infrastructure/rag/retrieval/reranker.py`
- `DlpServiceClient` — `src/infrastructure/security/dlp_client.py`

## Diagnóstico

### Diagnóstico 1 — Arquitectura del flujo de saludos

**Nodo `classify_intent_node`** (`src/application/graphs/nodes/classify_intent.py`):
- Normaliza la query (minúsculas, sin tildes).
- Si **todos** los tokens de la query están en `_GREETING_KEYWORDS` → `query_type = "saludo"`.
- `_GREETING_KEYWORDS` cubre: `{hola, buenos, dias, buenas, tardes, noches, hey, saludos, buen, dia, hi, hello}`.
- La condición `all(w in _GREETING_KEYWORDS for w in words)` es muy restrictiva: falla para "¿Cómo estás?" porque "como" y "estas" no están en el set.

**Nodo `respond_blocked_node`** (`src/application/graphs/nodes/respond_blocked.py`):
- Cuando `query_type == "saludo"`, retorna la constante hardcodeada `_GREETING_RESPONSE`.
- No llama al LLM ni tiene variación alguna.

**Grafo** (`src/application/graphs/rag_graph.py`):
- `_route_after_guardrail` enruta `"saludo"` directamente a `respond_blocked` (sin retrieval).
- No existe ruta diferenciada para saludos conversacionales.

**Consecuencia directa:**
1. El set de keywords no cubre saludos conversacionales → caen al RAG → fallback incorrecto.
2. Los saludos detectados siempre reciben la misma respuesta estática → experiencia robótica.

### Diagnóstico 2 — Causa del warning de cuota GCP

La advertencia proviene de `google/auth/_default.py:114`. Se emite cuando:
- Las credenciales son de tipo `google.oauth2.credentials.Credentials` (usuario via gcloud).
- No se ha establecido el atributo `quota_project_id` en las credenciales ni en el cliente.

**Solución estándar**: Pasar `quota_project_id` al inicializar cada cliente GCP, usando el mismo `GCP_PROJECT_ID` ya configurado en settings. Esto le indica a la librería `google.auth` cuál proyecto usar para la cuota, eliminando el warning.

**Alternativa CLI (no modifica código):** `gcloud auth application-default set-quota-project PROJECT_ID` actualiza el archivo ADC con el `quota_project_id`. Sin embargo, esta solución es frágil (depende de la acción manual de cada desarrollador, no se aplica en Docker) y no es la correcta.

**Solución correcta:** Configurar `quota_project_id` programáticamente en cada cliente, derivándolo del `gcp_project_id` ya existente en settings.

## Spec

### Parte A: Detección y respuesta natural de saludos

#### A1. Ampliar la detección de saludos en `classify_intent_node`

Ampliar el set `_GREETING_KEYWORDS` y/o agregar patrones adicionales para cubrir saludos conversacionales frecuentes en español:

**Estrategia de detección en dos niveles:**

**Nivel 1 — Keywords ampliadas (heurística rápida, O(1)):**
Agregar al set existente tokens que aparecen en saludos conversacionales: `como`, `estas`, `tal`, `bien`, `que`, `va`, `anda`, `todo`, `hay`, `ahi`, `genial`, `excelente`.

La condición `all(w in _GREETING_KEYWORDS for w in words)` seguirá siendo la lógica de clasificación, pero con el set ampliado cubrirá más combinaciones de saludo puro.

**Nivel 2 — Patrones regex para saludos conversacionales (complemento):**
Agregar un conjunto reducido de patrones regex específicos para saludos de pregunta que no pueden resolverse solo con keywords:
- `¿cómo estás?` / `como estas`
- `¿qué tal?` / `que tal`
- `¿cómo te va?` / `como te va`
- `¿cómo andás?` / `como andas`
- `¿todo bien?` / `todo bien`
- Variantes con signos de interrogación opcionales y tildes normalizadas.

Si la query normalizada matchea algún patrón de saludo conversacional → `query_type = "saludo"`.

**Principio de diseño:** La expansión debe ser conservadora. Solo agregar patrones con muy alta precisión (es decir, que no puedan ser confundidos con consultas de dominio bancario). No agregar keywords tan genéricas que produzcan falsos positivos (ej: "bien" solo no es suficiente como saludo).

#### A2. Nuevo nodo `respond_greeting_node` — generación de respuesta con LLM

Reemplazar la respuesta hardcodeada de `respond_blocked_node` para saludos por un nodo dedicado que use el LLM para generar una respuesta conversacional y natural.

**Comportamiento esperado del nodo:**
- Recibe la query original del usuario (ej: "¿Cómo estás?", "Buenos días").
- Invoca Gemini Flash Lite con un prompt de sistema minimalista.
- Genera una respuesta breve (≤ 3 oraciones) que:
  - Responde de forma contextual al saludo específico (si preguntó "¿Cómo estás?" → responder cómo está; si dijo "Hola" → dar la bienvenida).
  - Menciona brevemente su función como asistente de documentación bancaria interna.
  - Pregunta en qué puede ayudar.
- No utiliza retrieval de documentos — es una respuesta directa del LLM.

**Consideraciones de performance:**
- Usar **Gemini Flash Lite** (modelo ya disponible en el sistema, mismo que el guardrail LLM) para minimizar latencia.
- El prompt debe ser corto y directo. No enviar system prompt completo de 15 secciones — solo las instrucciones mínimas necesarias para el comportamiento de saludo.
- La respuesta típica de un saludo con Gemini Flash Lite tarda entre 300-800ms — aceptable considerando que la respuesta hardcodeada actual es menos de 1ms pero la experiencia es inferior.
- Agregar un **fallback hardcodeado de seguridad**: si el LLM falla (timeout, error), retornar una respuesta predefinida breve en lugar de propagar el error al usuario.

#### A3. Prompt de saludo — diseño

El prompt para la generación de respuesta a saludos debe:
- Identificar el asistente como asistente virtual de documentación bancaria interna de Banco Macro.
- Instrucción: responder al saludo del usuario de forma natural y breve.
- Si la query incluye una pregunta conversacional (ej: "¿Cómo estás?"), responderla naturalmente antes de preguntar en qué puede ayudar.
- Responder siempre en español.
- No revelar detalles técnicos internos.
- No usar siempre la misma frase — variar la forma de ofrecer ayuda.
- Extensión máxima: 3 oraciones.

Este prompt debe ubicarse en `src/infrastructure/llm/prompts/` como constante separada o como función en el módulo existente `system_prompt.py`.

#### A4. Modificar el grafo para enrutar saludos al nuevo nodo

En `rag_graph.py`:
- Registrar `respond_greeting_node` como nodo del grafo.
- Modificar `_route_after_guardrail` para que `query_type == "saludo"` apunte a `respond_greeting` en lugar de `respond_blocked`.
- `respond_blocked_node` pierde la responsabilidad de manejar saludos — su caso `query_type == "saludo"` puede eliminarse o mantenerse como fallback defensivo.

#### A5. Preservar el comportamiento del guardrail para saludos

El `validate_input_node` actualmente salta la validación cuando `query_type == "saludo"` (optimización correcta: los saludos no son amenazas de seguridad). Este comportamiento debe preservarse — el nuevo nodo `respond_greeting_node` no requiere validación de guardrail.

### Parte B: Eliminación del warning de cuota GCP

#### B1. Agregar configuración `gcp_quota_project_id` a settings

Agregar un campo nuevo `gcp_quota_project_id` en `src/config/settings.py`, con valor por defecto vacío (`""`). Cuando esté vacío, los clientes GCP deben usar `gcp_project_id` como fallback para el `quota_project_id`.

Agregar la variable correspondiente en `.env.example` documentada como opcional.

#### B2. Pasar `quota_project_id` en todos los clientes GCP

En cada punto de inicialización de cliente GCP, pasar el valor efectivo de `quota_project_id` (primero `gcp_quota_project_id` si está definido, sino `gcp_project_id`):

**Clientes a modificar:**

| Archivo | Cliente | Parámetro |
|---------|---------|-----------|
| `src/infrastructure/llm/client.py` | `ChatGoogleGenerativeAI` | `quota_project_id` en `kwargs` |
| `src/infrastructure/llm/client.py` | `GoogleGenerativeAIEmbeddings` | `quota_project_id` en `emb_kwargs` |
| `src/infrastructure/rag/embeddings/gemini_embeddings.py` | `genai.Client` | `quota_project_id` en kwargs del constructor |
| `src/infrastructure/rag/retrieval/gemini_reranker.py` | `genai.Client` | `quota_project_id` en kwargs del constructor |
| `src/infrastructure/storage/gcs_client.py` | `storage.Client` | `quota_project_id` en kwargs del constructor |

**Nota:** `quota_project_id` solo debe pasarse cuando `use_vertex_ai=True` (modo Vertex AI / ADC). En modo API key (`use_vertex_ai=False`), el parámetro no aplica y no debe incluirse.

#### B3. Actualizar Docker Compose

Agregar `GCP_QUOTA_PROJECT_ID: ${GCP_QUOTA_PROJECT_ID:-}` en las variables de entorno del servicio `backend` en `docker-compose.yml`. Si no se define en el `.env`, se puede hacer que el código use `GCP_PROJECT_ID` como valor por defecto (ver B1).

#### B4. No usar supresión de warnings como solución

**Explícitamente fuera de alcance:** No suprimir el warning con `warnings.filterwarnings()` ni con `PYTHONWARNINGS=ignore`. La supresión enmascara un problema de configuración real. La solución correcta es configurar el `quota_project_id` adecuadamente.

## Acceptance Criteria

### Saludos (Parte A)
- [ ] **AC-1**: "¿Cómo estás?" es detectado como `saludo` por `classify_intent_node` y no pasa al pipeline RAG.
- [ ] **AC-2**: "¿Qué tal?" es detectado como `saludo`.
- [ ] **AC-3**: "¿Cómo te va?" es detectado como `saludo`.
- [ ] **AC-4**: "¿Todo bien?" es detectado como `saludo`.
- [ ] **AC-5**: "Hola, buen día" sigue siendo detectado como `saludo` (sin regresión).
- [ ] **AC-6**: "Buenos días" sigue siendo detectado como `saludo`.
- [ ] **AC-7**: El sistema genera una respuesta diferente para "¿Cómo estás?" vs "Hola" — no usa siempre la misma cadena fija.
- [ ] **AC-8**: La respuesta al saludo "¿Cómo estás?" incluye una respuesta conversacional a la pregunta (no solo la bienvenida estándar).
- [ ] **AC-9**: La respuesta al saludo menciona la función del asistente y ofrece ayuda.
- [ ] **AC-10**: Si el LLM falla, el sistema retorna un fallback hardcodeado sin propagar el error.
- [ ] **AC-11**: Las evaluaciones de `topic_classification` TC-005 ("Hola, buen dia") y TC-006 ("¿Como estas?") siguen pasando.
- [ ] **AC-12**: Queries bancarias cortas no son clasificadas erróneamente como saludos (ej: "préstamo", "tarjeta", "vacaciones" siguen siendo `consulta`).
- [ ] **AC-13**: Tests unitarios cubren: detección de saludos ampliados, generación de respuesta con LLM mock, fallback ante error del LLM.

### GCP warning (Parte B)
- [ ] **AC-14**: Al inicializar el sistema, no aparece el `UserWarning` de cuota de GCP en los logs.
- [ ] **AC-15**: `gcp_quota_project_id` está disponible como setting configurable en `settings.py`.
- [ ] **AC-16**: Si `gcp_quota_project_id` no se define, se usa `gcp_project_id` como fallback (sin romper la inicialización).
- [ ] **AC-17**: El `quota_project_id` solo se aplica cuando `use_vertex_ai=True`.
- [ ] **AC-18**: Tests unitarios validan que los clientes GCP se inicializan con `quota_project_id` cuando corresponde.

### No-regresión
- [ ] **AC-19**: Suite completa de tests unitarios pasa sin fallos.
- [ ] **AC-20**: Ninguna otra categoría de evaluación experimenta regresión.

## Archivos a crear/modificar

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `src/application/graphs/nodes/classify_intent.py` | Modificar | Ampliar `_GREETING_KEYWORDS` y agregar patrones regex para saludos conversacionales |
| `src/application/graphs/nodes/respond_greeting.py` | **Crear** | Nuevo nodo que genera respuesta de saludo con Gemini Flash Lite |
| `src/infrastructure/llm/prompts/system_prompt.py` | Modificar | Agregar constante/función de prompt para respuesta de saludos (o crear `greeting_prompt.py`) |
| `src/application/graphs/rag_graph.py` | Modificar | Registrar `respond_greeting_node`, enrutar `saludo` hacia él en lugar de `respond_blocked` |
| `src/application/graphs/nodes/respond_blocked.py` | Modificar | Eliminar/deprecar el caso `saludo` (ya no llega a este nodo) |
| `src/config/settings.py` | Modificar | Agregar `gcp_quota_project_id: str = ""` |
| `src/infrastructure/llm/client.py` | Modificar | Pasar `quota_project_id` a `ChatGoogleGenerativeAI` y `GoogleGenerativeAIEmbeddings` |
| `src/infrastructure/rag/embeddings/gemini_embeddings.py` | Modificar | Pasar `quota_project_id` a `genai.Client` |
| `src/infrastructure/rag/retrieval/gemini_reranker.py` | Modificar | Pasar `quota_project_id` a `genai.Client` |
| `src/infrastructure/storage/gcs_client.py` | Modificar | Pasar `quota_project_id` a `storage.Client` |
| `.env.example` | Modificar | Documentar variable `GCP_QUOTA_PROJECT_ID` (opcional) |
| `docker-compose.yml` | Modificar | Agregar `GCP_QUOTA_PROJECT_ID` en variables de entorno del backend |
| `tests/unit/test_classify_intent.py` | Modificar | Agregar tests para saludos conversacionales ampliados |
| `tests/unit/test_respond_greeting.py` | **Crear** | Tests del nodo de respuesta de saludo (con mock del LLM y fallback) |
| `tests/unit/test_gcp_quota_config.py` | **Crear** | Tests de configuración de quota_project_id |

## Decisiones de diseño

1. **Nodo separado `respond_greeting_node` en lugar de modificar `respond_blocked_node`**: La responsabilidad de generar saludos es conceptualmente diferente a manejar bloqueos o deflexiones. Un nodo dedicado es más mantenible, testeable y permite evolucionar la lógica de saludos de forma independiente.

2. **Gemini Flash Lite para saludos, no Flash completo**: Los saludos no requieren razonamiento complejo. Flash Lite tiene menor latencia y costo, y es más que suficiente para generar 2-3 oraciones conversacionales. El mismo modelo ya se usa para el clasificador del guardrail.

3. **Prompt de saludo separado del `SYSTEM_PROMPT_RAG`**: El system prompt de RAG tiene 15 secciones diseñadas para respuestas basadas en documentos recuperados. Para un saludo, la mayoría de esas secciones son irrelevantes (citaciones, fallback, retrieval) y agregan tokens innecesarios. Un prompt específico y minimalista mejora la calidad de la respuesta de saludo.

4. **Fallback hardcodeado si el LLM falla**: Los saludos deben ser siempre respondidos, incluso si el LLM no está disponible. Un fallback corto y neutral ("¡Hola! ¿En qué puedo ayudarte?") garantiza que el usuario nunca vea un error en un saludo simple.

5. **`quota_project_id` derivado de `gcp_project_id` por defecto**: En el proyecto actual, el proyecto de cuota y el proyecto de recursos son el mismo (`itmind-macro-ai-dev-0`). Usar `gcp_project_id` como default elimina la necesidad de una variable de entorno adicional en la mayoría de los casos, y solo se externaliza como `gcp_quota_project_id` para entornos donde ambos proyectos difieren.

6. **Dependencia de implementación con T6-S8-07**: Ambas specs modifican `rag_graph.py` y `classify_intent.py`. Para evitar conflictos de merge, T6-S8-08 debe implementarse sobre la base de T6-S8-07 ya mergeada. Funcionalmente son independientes.

## Fuera de alcance

- Persistencia de estado de ánimo del asistente entre conversaciones (ej: "recuerda que está de buen humor").
- Detección de saludos en múltiples idiomas más allá del español (ya cubierto parcialmente con "hi", "hello" en el set actual).
- Supresión del warning con `warnings.filterwarnings()` — no es una solución válida.
- Modificación de `DlpServiceClient` para el warning — el cliente DLP está condicionado a `dlp_enabled=True` que está deshabilitado en producción actual; se puede posponer.
- Cambios en el handling de `cache_behavior`, `memory_episodic` u otras categorías de evaluación.

## Registro de Implementación

**Fecha**: 2026-03-28 | **Rama**: 74-t6-s8-08_greeting-natural-response-and-gcp-quota-fix

| Archivo | Acción | Motivo |
|---------|--------|--------|
| `src/application/graphs/nodes/classify_intent.py` | Modificado | Strip `¿¡` de `clean_query`; expandir `_GREETING_KEYWORDS` con 8 tokens conversacionales; agregar `_GREETING_PATTERN_RE` para `como te va` / `como andas` (AC-1 a AC-6) |
| `src/application/graphs/nodes/respond_greeting.py` | Creado | Nodo LLM para saludos con Gemini Flash Lite y fallback hardcodeado (AC-7 a AC-10) |
| `src/infrastructure/llm/prompts/system_prompt.py` | Modificado | Agregar `GREETING_SYSTEM_PROMPT` y `build_greeting_prompt()` separados del RAG prompt (AC-8, AC-9) |
| `src/application/graphs/rag_graph.py` | Modificado | Registrar `respond_greeting_node`; `_route_after_guardrail` enruta `saludo` → `respond_greeting`; edge → END (AC-7) |
| `src/application/graphs/nodes/respond_blocked.py` | Modificado | Eliminar caso `saludo` (ya no llega a este nodo); simplificar a ternario (AC-7) |
| `src/config/settings.py` | Modificado | Agregar `gcp_quota_project_id: str = ""` (AC-15, AC-16) |
| `src/infrastructure/llm/client.py` | Modificado | `_build_chat_model` y `_get_embeddings_model`: cargar ADC con `quota_project_id` vía `google.auth.default()` cuando `use_vertex_ai=True` (AC-14, AC-17) |
| `src/infrastructure/rag/embeddings/gemini_embeddings.py` | Modificado | `genai.Client` recibe `credentials` con quota project en modo Vertex AI (AC-14, AC-17) |
| `src/infrastructure/rag/retrieval/gemini_reranker.py` | Modificado | Ídem: `genai.Client` con `credentials` en modo Vertex AI (AC-14, AC-17) |
| `src/infrastructure/storage/gcs_client.py` | Modificado | `storage.Client` con `credentials` cuando `use_vertex_ai=True`; condicional añadido (AC-14, AC-17) |
| `.env.example` | Modificado | Documentar `GCP_QUOTA_PROJECT_ID` como opcional con comentario (AC-15) |
| `docker-compose.yml` | Modificado | Agregar `GCP_QUOTA_PROJECT_ID: ${GCP_QUOTA_PROJECT_ID:-}` al servicio `backend` (AC-15) |
| `tests/unit/test_classify_intent.py` | Modificado | Agregar `TestConversationalGreetings` (AC-1 a AC-6) y `TestNoBankingFalsePositives` (AC-12) |
| `tests/unit/test_respond_greeting.py` | Creado | 11 tests: happy path LLM, fallback, prompt structure (AC-13) |
| `tests/unit/test_gcp_quota_config.py` | Creado | 10 tests: settings, fallback, Vertex-only, GCS+embeddings clients (AC-18) |

### Notas de Implementación

1. **Fix `¿` en clasificación**: La condición `all(w in keywords for w in words)` fallaba para `"¿Cómo estás?"` porque `_normalize` no elimina `¿`. Solución: `normalized.strip("¿¡!.?,;:")` en lugar de solo `rstrip`. Sin impacto en tests existentes (ningún keyword contiene `¿`).

2. **Patrón regex conservador**: Solo `como te va` y `como andas` se cubren por regex (el resto por keywords). `te`, `va`, `andas` son demasiado genéricos para keywords; el regex es más preciso.

3. **GCP quota via `credentials`**: Ningún cliente GCP acepta `quota_project_id` directamente en el constructor. La solución correcta es `google.auth.default(quota_project_id=...)` que retorna credentials con el quota project configurado. Se eliminó el `UserWarning` en la fuente (`google.auth._default._check_user_creds_with_quota`).

4. **DlpServiceClient excluido**: Según spec, el cliente DLP está fuera de alcance (`dlp_enabled=False` en producción).

5. **Resultado**: 58 tests nuevos. 792 tests pasando (suite non-DAG). 0 regresiones. Coverage: `classify_intent.py` 100%, `respond_greeting.py` 100%, `respond_blocked.py` 100%, `rag_graph.py` 82%.
