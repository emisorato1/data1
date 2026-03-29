# T6-S8-13: Ambigüedad borderline sin contexto conversacional y gap en detección de declaraciones

## Meta

| Campo           | Valor                                                                                                       |
| --------------- | ----------------------------------------------------------------------------------------------------------- |
| Track           | T6 (Franco)                                                                                                 |
| Prioridad       | Alta                                                                                                        |
| Estado          | done                                                                                                        |
| Bloqueante para | —                                                                                                           |
| Depende de      | T6-S8-12 (done)                                                                                             |
| Skill           | `langgraph/SKILL.md`, `prompt-engineering/SKILL.md`, `testing-strategy/SKILL.md`                            |
| Estimacion      | S (2-4h)                                                                                                    |
| Diagnosticado   | 2026-03-29 via pruebas manuales post-T6-S8-12 contra API en Docker local                                   |

> Corregir dos bugs residuales identificados en la validación post-T6-S8-12: (1) el LLM borderline del ambiguity detector no recibe contexto conversacional, causando que queries de seguimiento legítimas que atraviesan todas las heurísticas deterministas sean clasificadas como AMBIGUOUS por el LLM; (2) el regex de detección de declaraciones de contexto (`_CONTEXT_STATEMENT_RE`) no cubre frases que comienzan con posesivos ("Mi DNI es…", "Mi área es…"), causando que entren al pipeline RAG y reciban fallback.

## Relación con T6-S8-12

T6-S8-12 propagó `has_history` a las heurísticas 3 y 6 del ambiguity detector, y documentó explícitamente la decisión de **no** agregar `has_history` a la heurística 4, delegando esos casos al LLM borderline. La premisa era que el LLM podría "resolver" las queries de seguimiento ambiguas. Las pruebas manuales post-implementación demuestran que esta premisa era incorrecta: el LLM borderline clasifica como AMBIGUOUS porque su prompt solo recibe la query aislada y los topics de los chunks — sin información de que existe un hilo de conversación activo.

Para la detección de declaraciones de contexto, T6-S8-12 implementó `_CONTEXT_STATEMENT_RE` con prefijos conservadores (`soy`, `trabajo en`, `estoy en`, `me llamo`, `prefiero`, `siempre`). La prueba manual reveló que la frase `"Mi DNI es 32.456.789 y trabajo en compliance"` no matchea porque comienza con `"Mi"`, que no está en la lista de prefijos.

## Contexto

### Evidencia de pruebas manuales — 29 marzo 2026

Script de prueba: `evals/manual_test_t6s8_12.py`, ejecutado contra Docker local (`localhost:8000`, `admin@banco.com`).

#### Bug 1 — LLM borderline clasifica follow-ups como AMBIGUOUS

**Escenario A — Cadena "blanqueo de PIN":**

```
T1 >>> "Necesito informacion sobre el blanqueo de PIN de tarjeta de debito"
     <<< (respuesta completa correcta con canales: IVR, Banca Internet, App)

T2 >>> "¿Y cuanto tarda?"
     <<< "Para poder brindarte la información correcta, necesito saber a qué
          te referís con '¿Y cuánto tarda?':
          - En un trámite específico
          - En recibir un producto o servicio
          - En la resolución de un problema
          ¿Cuál de estas opciones se ajusta a tu consulta?"
```

**Traza de heurísticas para T2 con `has_history=True`:**

| Heurística | Resultado | Razón |
| --- | --- | --- |
| H1 (pronombre) | Skip | No matchea `_PRONOUN_RE` |
| H2 (short/no-domain) | Skip | 3 tokens > umbral de 2 |
| H3 (generic_pattern) | Skip | Matchea `_GENERIC_PATTERN_RE` **pero** `has_history=True` → condición `not has_history` es False |
| H4 (generic_verb_noun) | Skip | No matchea `_GENERIC_VERB_NOUN_RE` (no hay verbo+sustantivo genérico) |
| H5 (multi-area) | Skip | Depende de chunks, probablemente no aplica |
| H6 (low_score) | Skip | `has_history=True` → condición `not has_history` es False |
| H7 (domain-specific) | Skip | No hay término de dominio en la query |
| **LLM borderline** | **AMBIGUOUS** | **El prompt no tiene información de que T1 discutía blanqueo de PIN** |

**Escenario B — Cadena "caja de seguridad":**

```
T1 >>> "Quiero contratar una caja de seguridad, ¿que necesito?"
     <<< (respuesta correcta con requisitos: cuenta corriente, 18 meses)

T2 >>> "¿Que tamanos hay disponibles?"
     <<< (respuesta correcta con tamaños: 10x10, 10x15...)

T3 >>> "¿Cuantas veces puedo ir al mes sin cargo?"
     <<< "Para brindarte la información correcta, necesito saber a qué te referís
          con 'ir':
          - Retiros de efectivo
          - Consultas en sucursal
          - Transferencias
          ¿En cuál de estas opciones estás interesado/a?"
```

En T3, "ir" se refiere claramente a visitas a la caja de seguridad (discutida en T1 y T2). El LLM borderline no puede saberlo porque no tiene acceso al historial.

**Causa raíz:** La función `_classify_with_llm()` en `ambiguity_detector.py` construye el prompt con `{query}` y `{topics}` (topics extraídos de chunks), pero **no incluye historial de conversación**. El campo `messages` existe en el `GraphState` y llega al nodo, pero nunca se pasa al prompt del LLM borderline.

#### Bug 2 — Declaración con posesivo no reconocida como contexto

```
>>> "Mi DNI es 32.456.789 y trabajo en compliance"
<<< "No encontre informacion suficiente en la documentacion disponible para
     responder esta consulta. Te sugiero contactar al area correspondiente
     para obtener una respuesta precisa."
```

El regex `_CONTEXT_STATEMENT_RE` en `classify_intent.py` está anclado con `^` y solo matchea los siguientes prefijos:
```
soy\s | trabajo\s+en\s | estoy\s+en\s | me\s+llamo\s | prefiero\s | siempre\s+respond | siempre\s+us
```

La frase empieza con `"Mi DNI es..."` → ningún prefijo matchea → clasificada como `consulta` → pipeline RAG completo → score_gate la rechaza → fallback genérico.

**Efecto en memoria episódica:** ME-005 espera un acuse de recibo que contenga `["compliance", "entendido", "cuenta", "registrado"]`. Sin acuse, `extract_memories` no tiene un par conversacional útil y no almacena memoria episódica.

### Impacto en métricas de evaluación

| Categoría          | Afectada | Tests impactados | Impacto esperado |
| ---------------    | -------- | ---------------- | ---------------- |
| `memory_shortterm` | Sí       | MS-005 (PIN tarda), MS-012 (caja visitas) | ≥ +2 tests recuperados |
| `memory_episodic`  | Sí       | ME-005 (DNI + compliance) | +1 test recuperado |

## Diagnóstico — Causa raíz unificada

Ambos bugs son **gaps de completitud** en los fixes de T6-S8-12:

1. T6-S8-12 propagó `has_history` a las heurísticas deterministas pero no al LLM borderline. Cuando las heurísticas dicen "inconclusas" y delegan al LLM, el LLM opera en el mismo vacío contextual que las heurísticas corrigieron.

2. T6-S8-12 implementó `_CONTEXT_STATEMENT_RE` con prefijos conservadores pero no cubrió la estructura posesiva `"Mi X es Y"` que es una forma natural de declarar datos personales.

## Spec

### Parte A — Inyectar resumen de historial en el prompt del LLM borderline

**Archivo:** `src/application/graphs/nodes/ambiguity_detector.py`

#### A1. Pasar historial de conversación a `_classify_with_llm()`

La función `_classify_with_llm()` actualmente recibe `query` y `reranked_chunks`. Agregar un parámetro `messages: list[BaseMessage]` con el historial de conversación del estado del grafo.

En `ambiguity_detector_node`, el historial ya está disponible en `state["messages"]`. Pasarlo al llamar `_classify_with_llm()`.

#### A2. Construir resumen de historial para el prompt

No pasar el historial completo al prompt (demasiados tokens, alto costo). En su lugar, construir un resumen breve:

```python
def _build_history_summary(messages: list[BaseMessage], max_turns: int = 2) -> str:
    """Extrae las últimas N preguntas del usuario del historial."""
    if not messages:
        return ""
    human_msgs = [m for m in messages if isinstance(m, HumanMessage)]
    recent = human_msgs[-max_turns:]
    if not recent:
        return ""
    summary = "; ".join(m.content[:80] for m in recent if isinstance(m.content, str))
    return f"Historial reciente del usuario: {summary}"
```

El resumen debe ser lo mínimo necesario para que el LLM entienda que hay un hilo de conversación en curso — no necesita la respuesta completa del asistente, solo las últimas preguntas del usuario.

#### A3. Modificar `_AMBIGUITY_LLM_PROMPT` para incorporar historial

Agregar un bloque condicional al prompt:

```
{history_context}

Dado el historial (si existe), evalúa si la query es una pregunta de seguimiento
sobre el tema ya discutido. Si el usuario claramente continúa un tema previo,
clasifica como CLEAR — no es ambigua, solo es corta o implícita.
```

Cuando no hay historial, `{history_context}` es una cadena vacía y el prompt se comporta igual que antes.

#### A4. Considerar heurística 5 (multi-area) con historial

La heurística 5 (multi-area similar scores) actualmente **no** tiene check de `has_history`. No fue incluida en T6-S8-12 y no ha mostrado falsos positivos en las pruebas manuales. **No modificar en esta spec** — monitorear en el próximo eval run.

### Parte B — Ampliar `_CONTEXT_STATEMENT_RE` para posesivos

**Archivo:** `src/application/graphs/nodes/classify_intent.py`

#### B1. Agregar prefijos posesivos al regex

Agregar al regex existente los siguientes patrones:

```python
r"|mi\s+(?:dni|area|área|puesto|rol|equipo|sucursal|legajo|nombre)\s"
r"|mis\s+(?:datos|preferencias)\s"
```

Estos patrones cubren declaraciones que comienzan con posesivo seguido de un sustantivo de contexto personal/laboral. La lista de sustantivos es restrictiva a propósito — no matchea `"mi tarjeta"` o `"mi préstamo"` que son consultas legítimas.

La condición existente de que la query no contenga `"?"` sigue aplicando para evitar falsos positivos con preguntas como `"¿Mi área tiene acceso a X?"`.

#### B2. Considerar estructura compuesta "Mi X es Y y [declaración]"

El caso `"Mi DNI es 32.456.789 y trabajo en compliance"` tiene dos declaraciones unidas por "y". El segundo fragmento (`"trabajo en compliance"`) ya matchearía si estuviera solo. El patrón propuesto en B1 matchea por el primer fragmento (`"Mi DNI es..."`).

No es necesario implementar parsing multi-cláusula — el regex de prefijo ya resuelve el caso. La extracción de memoria downstream puede manejar el contenido compuesto.

## Acceptance Criteria

### Parte A — LLM borderline con historial

- **AC-1**: En una conversación donde T1 responde sobre blanqueo de PIN, T2 = `"¿Y cuánto tarda?"` recibe respuesta sobre el tiempo del blanqueo de PIN — no clarificación. (MS-005)
- **AC-2**: En una conversación donde T1-T2 discuten caja de seguridad, T3 = `"¿Cuantas veces puedo ir al mes sin cargo?"` responde con "5" visitas gratuitas — no clarificación. (MS-012)
- **AC-3**: `"¿Y cuánto tarda?"` SIN historial previo sigue clasificándose como AMBIGUOUS por la heurística 3 (`_GENERIC_PATTERN_RE`).
- **AC-4**: El resumen de historial no excede 200 caracteres para evitar inflación de tokens en el LLM borderline.

### Parte B — Detección de declaraciones posesivas

- **AC-5**: `"Mi DNI es 32.456.789 y trabajo en compliance"` se clasifica como `contexto_usuario` y recibe acuse de recibo con `"compliance"` o `"entendido"`. (ME-005)
- **AC-6**: `"Mi área es compliance y necesito ayuda"` se clasifica como `contexto_usuario` (contiene `"Mi área es..."`).
- **AC-7**: `"Mi tarjeta no funciona"` NO se clasifica como `contexto_usuario` — es una consulta legítima. El sustantivo `"tarjeta"` no está en la whitelist de B1.
- **AC-8**: `"¿Mi área tiene acceso?"` NO se clasifica como `contexto_usuario` — contiene `"?"`.

### No-Regresión

- **AC-9**: Suite completa de tests unitarios pasa sin fallos (actualmente 174).
- **AC-10**: Los 10 test cases de `ambiguous_queries` que ahora pasan no regresan — queries genuinamente ambiguas en primer turno siguen recibiendo clarificación.
- **AC-11**: `retrieval_accuracy` no disminuye (≥ 88.9%).
- **AC-12**: Queries fuera de dominio siguen siendo clasificadas como CLEAR por el LLM (instrucción OOD del prompt de T6-S8-12 no se ve afectada).

## Archivos a modificar

| Archivo | Acción | Descripción |
| ------- | ------ | ----------- |
| `src/application/graphs/nodes/ambiguity_detector.py` | Modificar | Pasar `messages` a `_classify_with_llm()`, construir resumen de historial, agregar `{history_context}` al prompt |
| `src/application/graphs/nodes/classify_intent.py` | Modificar | Agregar prefijos posesivos `mi\s+(?:dni|area|...)` a `_CONTEXT_STATEMENT_RE` |
| `tests/unit/test_ambiguity_detector.py` | Modificar | Tests para LLM borderline con/sin historial, verificar que resumen no excede 200 chars |
| `tests/unit/test_classify_intent.py` | Modificar | Tests para `"Mi DNI es..."`, `"Mi área es..."`, falsos negativos `"Mi tarjeta no funciona"` |

## Decisiones de diseño

1. **Resumen breve vs historial completo en prompt:** Pasar el historial completo al LLM borderline inflaría tokens y costo. Un resumen de las últimas 2 preguntas del usuario (≤200 chars) es suficiente para que el LLM entienda "hay un hilo sobre X". El LLM no necesita la respuesta del asistente — solo necesita saber el tema en curso.

2. **Whitelist de sustantivos en posesivos vs regex abierto:** El patrón `mi\s+\w+\s+es` sería más permisivo pero generaría falsos positivos (`"mi tarjeta es Visa"` → consulta, no declaración). La whitelist restrictiva (`dni`, `area`, `puesto`, `rol`, `equipo`, `sucursal`, `legajo`, `nombre`) cubre los casos de datos personales/laborales sin capturar consultas de productos bancarios.

3. **No modificar heurística 4 ni 5:** T6-S8-12 decidió no propagar `has_history` a la heurística 4 porque sus matches fluyen al LLM borderline. Con este fix, el LLM borderline ahora tendrá contexto para decidir correctamente. La heurística 5 (multi-area) no ha mostrado problemas en pruebas — no tocar.

4. **No agregar `has_history` al LLM — solo contexto:** En lugar de agregar una regla dura ("si `has_history`, siempre CLEAR"), pasamos información al LLM para que decida. Esto preserva la capacidad del LLM de detectar cambios de tema genuinos dentro de una conversación (el usuario empieza con préstamos y salta a vacaciones → eso sí es ambiguo incluso con historial).

## Fuera de alcance

- Modificar la heurística 5 (multi-area similar scores) — sin evidencia de problemas.
- Agregar detección de declaraciones compuestas multi-cláusula con análisis sintáctico.
- Reformular el query rewriting con LLM — el enriquecimiento determinista de T6-S8-12 cubre los casos principales.
- Modificar el eval runner o los datasets golden.

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
| ------ | ------------ | ------- | ---------- |
| Resumen de historial en prompt causa que LLM clasifique como CLEAR queries genuinamente ambiguas en conversación larga | Baja | Medio | El resumen solo incluye preguntas del usuario (no respuestas), limitado a 2 turnos. El LLM puede distinguir "seguimiento" de "cambio de tema" |
| Whitelist de sustantivos posesivos incompleta para futuras declaraciones | Baja | Bajo | Se puede extender en specs futuras si las pruebas revelan gaps adicionales |
| Latencia adicional por construcción de resumen | Muy baja | Bajo | La función de resumen es O(n) sobre messages con cap de 2 turnos — negligible vs llamada LLM |

## Registro de Implementación

**Fecha**: 2026-03-29 | **Rama**: 77-t6-s8-09-10_report03-diagnostic-fixes

| Archivo | Acción | Motivo |
|---------|--------|--------|
| `src/application/graphs/nodes/ambiguity_detector.py` | Modificado | Agregar `_build_history_summary`, extraer `_classify_with_llm`, modificar `_AMBIGUITY_LLM_PROMPT` con `{history_context}` (AC-1, AC-2, AC-3, AC-4, AC-12) |
| `src/application/graphs/nodes/classify_intent.py` | Modificado | Ampliar `_CONTEXT_STATEMENT_RE` con prefijos posesivos `mi\s+(?:dni\|area\|...)` y `mis\s+(?:datos\|preferencias)` (AC-5, AC-6, AC-7, AC-8) |
| `tests/unit/test_ambiguity_detector.py` | Modificado | Agregar `TestBuildHistorySummary` y `TestLLMBorderlineWithHistory` — 19 tests nuevos (AC-1, AC-3, AC-4, AC-12) |
| `tests/unit/test_classify_intent.py` | Modificado | Agregar `TestContextoUsuarioPosesivos` — 20 tests nuevos (AC-5, AC-6, AC-7, AC-8) |

### Notas de Implementación

- La lógica LLM inline en `ambiguity_detector_node` fue extraída a `_classify_with_llm(query, reranked_chunks, messages)` para mejorar testabilidad y separar responsabilidades.
- `_build_history_summary` limita el resumen a max 2 turnos con 80 chars por mensaje → garantiza ≤ 200 chars (AC-4).
- El `{history_context}` vacío cuando no hay historial preserva el comportamiento anterior del prompt (backward-compatible).
- Coverage resultante: `ambiguity_detector.py` 92%, `classify_intent.py` 82%. Suite completa: exit_code 0.
