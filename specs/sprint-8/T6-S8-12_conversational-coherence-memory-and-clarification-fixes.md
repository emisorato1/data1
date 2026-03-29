# T6-S8-12: Coherencia conversacional — ambigüedad en contexto, formato de clarificación y memoria episódica

## Meta

| Campo           | Valor                                                                                                       |
| --------------- | ----------------------------------------------------------------------------------------------------------- |
| Track           | T6 (Franco)                                                                                                 |
| Prioridad       | Alta                                                                                                        |
| Estado          | done                                                                                                        |
| Bloqueante para | —                                                                                                           |
| Depende de      | T6-S8-11 (done)                                                                                             |
| Skill           | `langgraph/SKILL.md`, `rag-retrieval/SKILL.md`, `prompt-engineering/SKILL.md`, `testing-strategy/SKILL.md` |
| Estimacion      | L (8-16h)                                                                                                   |
| Diagnosticado   | 2026-03-29 via pruebas manuales + análisis de logs_backend.log + report04.md                                |

> Corregir cinco bugs identificados en el ciclo de diagnóstico post-report04 que degradan la coherencia conversacional del asistente: (1) el prompt de clarificación genera opciones en prosa que el evaluador no detecta como lista; (2) el detector de ambigüedad no respeta el historial conversacional y rompe el hilo en cualquier pregunta corta de seguimiento; (3) el retrieval usa la query cruda del turno actual ignorando el contexto de turnos previos; (4) las declaraciones de contexto del usuario ("trabajo en RRHH", "respondeme con viñetas") pasan por el pipeline RAG y reciben fallback en lugar de acuse de recibo; (5) queries fuera de dominio son clasificadas como AMBIGUOUS en lugar de CLEAR, recibiendo una pregunta de clarificación en vez del mensaje de rechazo correspondiente.

## Relación con T6-S8-10 y T6-S8-11

T6-S8-10 reordenó el routing del grafo para que todas las queries pasen por `ambiguity_detector`. T6-S8-11 conectó la entrega de clarificaciones al orquestador SSE y amplió los patrones de verbos intermedios. Ambas specs corrigieron el pipeline de detección y entrega.

Esta spec aborda la capa superior: **la calidad y coherencia de la experiencia conversacional**. Los nodos funcionan correctamente en aislamiento pero no coordinan el contexto de la conversación entre sí: el detector de ambigüedad trata cada turno como independiente, el retrieval no enriquece la query con el historial, y el sistema no tiene un modo para recibir contexto del usuario sin intentar buscarlo en la documentación.

## Contexto

### Evidencia de report04 — categorías con degradación post-T6-S8-11

| Categoría           | report03 | report04 | Delta  | Bugs responsables |
| ------------------- | -------- | -------- | ------ | ----------------- |
| `ambiguous_queries` | 30%      | 50%      | +20%   | Bug 1             |
| `memory_shortterm`  | —        | 41.7%    | nuevo  | Bug 2, Bug 3      |
| `memory_episodic`   | —        | 30%      | nuevo  | Bug 4             |

### Evidencia de pruebas manuales — 29 marzo 2026

Las pruebas manuales cubren 5 bloques de escenarios sobre la API en vivo (Docker local, `admin@banco.com`). Los logs del backend correspondientes están en `evals/reports/logs_backend.log`.

#### Bug 1 — Clarificaciones en prosa, evaluador espera lista

Los queries genuinamente ambiguos (AQ-001, AQ-009, AQ-010) reciben respuestas como:

```
"Entiendo. Para poder ayudarte mejor, ¿a qué te refieres con 'eso'?
¿Necesitas información general sobre el tema o estás buscando información
sobre algún proceso o trámite en particular?"
```

La respuesta tiene "?" pero cero opciones detectadas por `_OPTIONS_RE = re.compile(r"^[ \t]*(?:[-•*]|\d+[.)]) ", re.MULTILINE)`. El evaluador falla en el paso 2 con `"expected >= 2 options, found 0"`.

AQ-004 y AQ-005 a veces generan bullets (no-determinístico). AQ-005 generó 2 bullets pero el LLM terminó el listado con ":" en lugar de "?", fallando el paso 1 del evaluador.

**Causa raíz:** `CLARIFICATION_SYSTEM_PROMPT` en `clarification_prompt.py:18` dice explícitamente _"Evita los menús numéricos robóticos, prefiere incluirlas fluidamente en el texto o como pequeñas viñetas orgánicas"_, y los cuatro ejemplos few-shot muestran opciones inline en prosa. El LLM obedece el prompt y genera prosa. El formato requerido por el evaluador no está expresado en ninguna parte del prompt.

#### Bug 2 — Ambiguity detector rompe conversaciones multi-turno

Cadena de 2 turnos en misma conversación:

```
T1 >>> "Necesito informacion sobre el blanqueo de PIN de tarjeta de debito"
     <<< (respuesta completa correcta — 2459 chars, 18 bullets)

T2 >>> "¿Y cuanto tarda?"
     <<< "Entiendo tu consulta. Para poder darte una respuesta precisa, ¿a qué
          te refieres con 'cuánto tarda'? ¿Estás consultando sobre el tiempo de
          espera para un trámite en particular?"
```

El mismo patrón se repite en todas las cadenas multi-turno probadas: cualquier pregunta corta o implícita activa la detección de ambigüedad e interrumpe el hilo, ignorando que el turno anterior ya estableció el contexto.

**Causa raíz:** `_GENERIC_PATTERN_RE` en `ambiguity_detector.py:40-50` incluye el patrón `cu[aá]nto\s+(?:me\s+)?(?:sale|cuesta|cobra|tarda)` que matchea `"cuánto tarda"` **sin verificar si hay historial de conversación**. La heurística 3 del nodo no consulta `has_history` (a diferencia de la heurística 1 que sí lo hace para pronombres). La consecuencia es que preguntas de seguimiento legítimas como `"¿Y cuánto tarda?"`, `"¿Y el plazo máximo?"`, `"¿Cuántas veces puedo ir?"` se tratan como ambigüedades absolutas.

El mismo efecto ocurre con la heurística 6 (`low_score_generic`): queries cortas de seguimiento tienen scores de retrieval bajos porque el embedding no tiene contexto del turno previo, lo cual activa una segunda heurística de ambigüedad.

**Efecto secundario:** El feedback loop implementado en `classify_intent_node` funciona para resolver la clarificación en el siguiente turno, pero una vez resuelta, la tercera pregunta de la cadena vuelve a triggear ambigüedad:

```
T1: "¿Como pido un prestamo?"            → clarificación (correcto)
T2: "Un prestamo personal"               → respuesta completa (feedback loop OK)
T3: "¿Cuales son los requisitos?"        → clarificación de nuevo (Bug 2 reaparece)
```

#### Bug 3 — Retrieval no usa el contexto de turnos previos

```
T1: "Soy oficial de cuentas en la sucursal de Rosario"
     → El bot no reconoce el contexto, responde "¿En qué puedo ayudarte?"

T2: "¿Cual es el consultorio medico mas cercano a mi ubicacion?"
     → Retrieval query: "consultorio médico cercano a mi ubicación"
     → No encuentra "San Lorenzo 1338, Rosario" porque "Rosario" no está en la query
```

El sistema de retrieval (`retrieve_node`) genera el embedding de `state["query"]`, que es siempre el texto crudo del turno actual. El historial de conversación llega al LLM de generación via el system prompt (campo `conversation_history`) pero **nunca al paso de retrieval**. Queries con referencias anafóricas ("¿Y el de Córdoba?", "¿Y cuánto tarda?") o que dependen de contexto establecido en turnos previos no pueden recuperar los documentos correctos.

#### Bug 4 — Declaraciones de contexto del usuario pasan por el pipeline RAG

```
"Siempre respondeme con vinetas, no parrafos largos"
→ "No encontre informacion suficiente en la documentacion disponible."

"Trabajo en el area de RRHH y me encargo de onboarding"
→ "No encontre informacion suficiente en la documentacion disponible."

"Trabajo en la sucursal de Cordoba, soy gerente regional"
→ "¿En qué puedo ayudarte hoy? ¿Tienes alguna consulta sobre ausentismo..."
  (ignora el contexto, responde genérico)
```

El clasificador de intención (`classify_intent_node`) distingue únicamente `saludo` vs `consulta`. Cualquier mensaje que no sea un saludo puro pasa por retrieval completo. Las declaraciones de contexto del usuario — preferencias de formato, rol laboral, ubicación — no tienen documentación en la base de conocimiento y reciben el fallback genérico. Como consecuencia, el nodo `extract_memories` recibe una conversación con una respuesta de fallback y no extrae nada significativo para la memoria episódica.

**Efecto en cadena sobre memory_episodic:** La fase "store" falla porque el sistema no acusa recibo del contexto. Sin un turno de confirmación significativo ("Entendido, recordaré que trabajas en RRHH"), el LLM de extracción de memorias no tiene conversación útil de la cual extraer un recuerdo. Los 4 casos de store que fallan en report04 (ME-001, ME-003, ME-005, ME-007) tienen este patrón.

#### Bug 5 — Queries fuera de dominio reciben clarificación en lugar de rechazo

```
"¿Quien gano el partido de River ayer?"
→ "Comprendo tu interés. Para asistirte de la mejor manera, ¿necesitas información
   sobre el resultado del partido de River, o te refieres a algún trámite o proceso
   relacionado con el club?"
```

El LLM del `ambiguity_detector` (Gemini Flash Lite) ve una query sin entidad de dominio bancario en los chunks recuperados y la clasifica como AMBIGUOUS, al no poder identificar un tema claro. El `score_gate` nunca llega a evaluar la relevancia porque el path de `needs_clarification=True` cortocircuita antes.

Este comportamiento es inconsistente: "Dame una receta de milanesas" funciona correctamente (LLM dice CLEAR → score_gate rechaza → fuera_dominio). La inconsistencia depende de cómo el LLM borderline interpreta cada query fuera de dominio.

## Diagnóstico — Causa raíz unificada

Los cinco bugs comparten un problema estructural: **el sistema procesa cada turno de la conversación en aislamiento**. Ningún nodo del grafo reformula, enriquece ni filtra la query actual usando el historial previo antes de tomar decisiones. El historial existe en el estado del grafo (`messages`) pero solo es consumido por el LLM de generación al final del pipeline, cuando ya es tarde para corregir el retrieval o la detección de ambigüedad.

## Spec

### Parte A — Formato de opciones en clarificaciones

**Archivo:** `src/infrastructure/llm/prompts/clarification_prompt.py`

Modificar `CLARIFICATION_SYSTEM_PROMPT` para que las instrucciones de formato y los ejemplos few-shot sean consistentes con el formato de lista que el evaluador detecta: ítems precedidos de `*`, `-` o `número.` al inicio de línea, con la pregunta de cierre conteniendo "?".

Las instrucciones actuales dicen "evita menús numéricos robóticos". Esta restricción debe eliminarse o invertirse: el formato de lista es el comportamiento requerido. Los ejemplos few-shot deben mostrar opciones en formato de lista, no en prosa inline.

La pregunta de cierre ("¿cuál de estas opciones te interesa?") debe aparecer explícitamente después del listado para garantizar que el evaluador encuentre al menos un "?" en la respuesta. Cuando el LLM genera el listado sin pregunta de cierre, el evaluador falla en el paso 1 antes de contar opciones.

No se requiere cambiar la lógica del nodo `generate_clarification_node` ni el evaluador — solo el prompt que guía el formato de salida del LLM.

### Parte B — Detección de ambigüedad con conciencia del historial conversacional

**Archivo:** `src/application/graphs/nodes/ambiguity_detector.py`

#### B1. Extender `has_history` a las heurísticas que lo necesitan

La heurística 1 del nodo ya hace `if _PRONOUN_RE.search(...) and not has_history`. El mismo patrón debe aplicarse a las heurísticas 3 y 6, que actualmente ignoran el historial:

- **Heurística 3 (`_GENERIC_PATTERN_RE`):** Si la query matchea un patrón genérico corto (como `cuánto tarda`, `cuánto me sale`) **y hay historial de conversación**, clasificar como CLEAR en lugar de AMBIGUOUS. El contexto previo desambigua implícitamente: el usuario pregunta sobre el trámite/proceso que ya se está discutiendo.

- **Heurística 6 (`low_score_generic`):** El score bajo combinado con query corta puede deberse a que la query es una referencia implícita, no una pregunta genérica. Si `has_history` es verdadero, no activar esta heurística — dejar que el LLM decida.

El razonamiento: una pregunta que es genuinamente ambigua en una conversación nueva ("¿cuánto tarda?" de entrada) puede ser perfectamente clara en el contexto de un turno previo ("cuánto tarda el blanqueo de PIN que acabas de describir"). La variable `has_history` ya existe y es correcta — solo falta propagarla a estas heurísticas.

#### B2. Mejorar el prompt LLM para queries fuera de dominio

El prompt `_AMBIGUITY_LLM_PROMPT` actualmente pide clasificar entre CLEAR y AMBIGUOUS. El LLM clasifica queries fuera de dominio como AMBIGUOUS porque no puede identificar un tema bancario claro.

Agregar una instrucción al prompt que establezca que si la query está claramente fuera del dominio bancario (deportes, recetas, tecnología, política, etc.) debe clasificarse como CLEAR — el sistema tiene otros mecanismos para manejar el rechazo por dominio. AMBIGUOUS es exclusivamente para queries bancarias vagas donde el usuario necesita especificar más detalles.

Esto alinea el comportamiento del LLM con la arquitectura real: el `score_gate` es quien rechaza queries fuera de dominio, no el `ambiguity_detector`.

### Parte C — Enriquecimiento de query con contexto conversacional

**Archivo:** `src/application/use_cases/rag/stream_response.py` (o `src/application/graphs/nodes/retrieve.py`)

Antes de invocar el grafo RAG, construir una query enriquecida que combine la query actual del usuario con el contexto relevante del historial de conversación. Este enriquecimiento debe ocurrir en la capa de orquestación, antes de que la query llegue al nodo de retrieval.

La query enriquecida no reemplaza la query original para el LLM de generación (que tiene acceso al historial completo vía `conversation_history`). Solo se usa para el paso de retrieval (embedding + búsqueda híbrida) y para la detección de ambigüedad.

**Criterios para el enriquecimiento:**

- Si el historial tiene mensajes previos, extraer las entidades principales del último turno asistente (o de los últimos N turnos) y agregarlas como contexto a la query actual.
- El enriquecimiento debe ser determinista y liviano — no usar un LLM adicional. Una heurística simple (las primeras N palabras del último turno asistente, o las entidades nombradas con mayúscula) es suficiente.
- Cuando la query actual ya tiene suficiente especificidad (token_count > umbral o contiene entidad de dominio), no enriquecer — evitar ruido en el embedding.
- El enriquecimiento puede ser tan simple como: `query_enriquecida = f"{query_actual} (contexto: {tema_previo})"` donde `tema_previo` se extrae del historial.

Este cambio también mejora la heurística 6 del detector de ambigüedad: si la query enriquecida produce scores más altos, la heurística `low_score_generic` ya no dispara erróneamente.

**Alcance acotado:** No implementar un nodo completo de "query rewriting" con LLM — eso es complejidad innecesaria para el sprint. El enriquecimiento determinista resuelve los casos principales de los fallos de `memory_shortterm` (referencias a ubicaciones y temas del turno anterior).

### Parte D — Modo acuse de contexto del usuario

**Archivos:** `src/application/graphs/nodes/classify_intent.py`, `src/application/use_cases/rag/stream_response.py`

Agregar una tercera categoría de clasificación de intención para mensajes que son **declaraciones de contexto** en lugar de consultas o saludos. Estos mensajes tienen la forma "soy/trabajo en/prefiero/mi X es Y" y su propósito es proveer contexto al asistente, no obtener información de la documentación.

#### D1. Detectar declaraciones de contexto en `classify_intent_node`

Agregar un nuevo `query_type`: `"contexto_usuario"`. El clasificador debe reconocer mensajes que:

- Comienzan con "soy", "trabajo en", "mi", "prefiero", "siempre", "me llamo", "estoy en"
- Son declaraciones sobre el usuario mismo (su rol, ubicación, preferencias, instrucciones)
- No contienen pregunta ("?") ni solicitud de acción

La detección debe ser heurística simple (regex + keywords). No usar LLM para esto — el costo no justifica la precisión marginal para este tipo de mensajes.

#### D2. Responder con acuse de recibo en el orquestador

Cuando `query_type == "contexto_usuario"`, el orquestador (`stream_response.py`) debe:

- No ejecutar el pipeline RAG (sin retrieval, sin ambiguity_detector, sin LLM de generación)
- Emitir un mensaje de acuse de recibo conciso: "Entendido, [paráfrasis del contexto]. ¿En qué puedo ayudarte?"
- Persistir el turno como mensaje del asistente (para que `extract_memories` pueda procesarlo en el paso de post-generación)
- Emitir evento `done` con fuentes vacías

El objetivo es que `extract_memories` reciba una conversación con estructura significativa: el usuario declara contexto y el asistente lo confirma. Este par (declaración + confirmación) es exactamente lo que el LLM de extracción necesita para generar un recuerdo episódico útil.

#### D3. El acuse de recibo no activa el pipeline RAG pero sí activa `extract_memories`

El nodo `extract_memories` se ejecuta post-generación. Para `query_type == "contexto_usuario"`, asegurarse de que el flujo de post-procesamiento ejecute `extract_memories` con la conversación actualizada (incluyendo el acuse de recibo).

Este es el mecanismo que cierra el ciclo de memoria episódica: declaración → acuse → extracción → almacenamiento → recuperación futura.

## Acceptance Criteria

### Parte A — Formato de clarificación

- **AC-1**: La respuesta de clarificación para AQ-001 ("necesito informacion de eso") contiene "?" y ≥ 2 opciones detectadas por `_OPTIONS_RE = re.compile(r"^[ \t]*(?:[-•*]|\d+[.)]) ", re.MULTILINE)`.
- **AC-2**: La respuesta de clarificación siempre termina con una pregunta explícita (tiene "?" después del listado de opciones).
- **AC-3**: El formato de opciones es determinista — la variabilidad del LLM no debe cambiar si la respuesta tiene bullets o prosa. El prompt debe ser suficientemente prescriptivo para que el formato sea consistente entre llamadas.
- **AC-4**: `ambiguous_queries` pass rate ≥ 80% en el eval runner (mejora desde 50%). Las 5 queries que fallaban en report04 (AQ-001, AQ-004, AQ-005, AQ-009, AQ-010) deben pasar o reducirse a ≤ 2 fallos.

### Parte B — Ambigüedad con historial

- **AC-5**: En una conversación donde T1 responde sobre blanqueo de PIN, T2 = "¿Y cuánto tarda?" recibe una respuesta sobre el tiempo de procesamiento del blanqueo de PIN — no una pregunta de clarificación.
- **AC-6**: En una conversación donde T1 responde sobre préstamo personal, T2 = "¿Y el plazo máximo?" recibe información sobre el plazo del préstamo personal.
- **AC-7**: "¿Y cuánto tarda?" SIN historial previo sigue siendo AMBIGUOUS (la heurística aplica solo cuando `has_history` es verdadero).
- **AC-8**: "¿Quien gano el partido de River ayer?" recibe la respuesta de fuera de dominio ("Lamento no poder ayudarte..."), no una pregunta de clarificación.
- **AC-9**: `memory_shortterm` pass rate ≥ 60% (mejora desde 41.7%). Las cadenas de continuidad temática (MS-004, MS-005, MS-006) y de caja de seguridad (MS-010, MS-011, MS-012) deben mejorar.

### Parte C — Retrieval con contexto

- **AC-10**: En una conversación donde T1 = "Soy oficial en la sucursal de Rosario", T2 = "¿Cual es el consultorio medico mas cercano?" recupera el documento de consultorios de Rosario y menciona "San Lorenzo 1338".
- **AC-11**: T3 = "¿Y el de Córdoba?" (después de T2 sobre Rosario) recupera el consultorio de Córdoba ("25 de Mayo 160").
- **AC-12**: El enriquecimiento no degrada `retrieval_accuracy` — los 16 test cases que pasaban en report04 siguen pasando.

### Parte D — Acuse de contexto y memoria episódica

- **AC-13**: "Siempre respondeme con vinetas, no parrafos largos" recibe un acuse de recibo ("Entendido, voy a responderte con viñetas") en lugar de "No encontré información suficiente".
- **AC-14**: "Trabajo en el area de RRHH y me encargo de onboarding" recibe un acuse de recibo que confirma el contexto laboral.
- **AC-15**: Tras el acuse de recibo, si el usuario pregunta en una nueva sesión algo relacionado a su contexto, el sistema personaliza la respuesta usando la memoria almacenada.
- **AC-16**: `memory_episodic` pass rate ≥ 50% (mejora desde 30%). Las 4 fases de store que fallaban (ME-001, ME-003, ME-005, ME-007) deben pasar con el nuevo acuse de recibo.

### No-Regresión

- **AC-17**: Suite completa de tests unitarios pasa sin fallos.
- **AC-18**: Las categorías en 100% en report04 (`guardrails_input`, `topic_classification`, `guardrails_output`, `system_prompt_behavior`) no regresan.
- **AC-19**: `retrieval_accuracy` no disminuye (≥ 88.9% — igual que report04).
- **AC-20**: Queries claramente ambiguas en conversación nueva siguen recibiendo clarificación (las heurísticas con historial no rompen la detección en primer turno).
- **AC-21**: `cache_behavior` no disminuye (≥ 87.5%).

## Archivos a modificar

| Archivo                                                 | Acción    | Descripción                                                                    |
| ------------------------------------------------------- | --------- | ------------------------------------------------------------------------------ |
| `src/infrastructure/llm/prompts/clarification_prompt.py` | Modificar | Reescribir instrucciones de formato y ejemplos few-shot para generar listas     |
| `src/application/graphs/nodes/ambiguity_detector.py`   | Modificar | Propagar `has_history` a heurísticas 3 y 6. Mejorar prompt LLM para OOD        |
| `src/application/graphs/nodes/classify_intent.py`      | Modificar | Agregar detección de `query_type = "contexto_usuario"`                          |
| `src/application/use_cases/rag/stream_response.py`     | Modificar | Handler para `"contexto_usuario"`: acuse de recibo sin RAG + trigger de memoria |
| `src/application/use_cases/rag/stream_response.py`     | Modificar | Enriquecimiento de query con contexto conversacional antes del grafo            |
| `tests/unit/test_ambiguity_detector.py`                | Modificar | Tests de heurísticas con `has_history=True/False`. Tests de prompt OOD          |
| `tests/unit/test_stream_response.py`                   | Modificar | Tests para handler `contexto_usuario` y enriquecimiento de query                |
| `tests/unit/test_classify_intent.py`                   | Modificar | Tests para detección de declaraciones de contexto                               |

## Decisiones de diseño

1. **Formato de lista sobre prosa en clarificaciones:** La decisión de usar prosa fue estética (evitar interfaces "robóticas"). Los datos muestran que la prosa es inconsistente en la práctica — el LLM no siempre la usa, y cuando lo hace el evaluador no la detecta. La consistencia mecánica de una lista es más valiosa que la naturalidad percibida. El prompt puede seguir siendo conversacional en el texto introductorio; solo las opciones deben estar en lista.

2. **Heurísticas con historial en lugar de desactivar heurísticas:** La alternativa era desactivar las heurísticas de seguimiento completamente cuando hay historial. Esto fue descartado porque `has_history` solo indica que el asistente respondió al menos una vez — no garantiza que el usuario esté siguiendo el mismo tema. La condición más segura es modificar heurísticas individuales que tienen claro sesgo (como `cuánto tarda`) y dejar el LLM decidir para casos menos claros.

3. **Enriquecimiento determinista en lugar de LLM de query rewriting:** La alternativa "gold standard" es un nodo LLM que reformula la query usando el historial ("¿cuánto tarda?" → "¿cuánto tarda el blanqueo de PIN de tarjeta de débito?"). Esto añade latencia (~500ms) y costo por turno. El enriquecimiento determinista con las primeras palabras clave del turno previo resuelve los casos principales a costo cero, y puede mejorarse en specs futuras si los logs muestran insuficiencia.

4. **`contexto_usuario` como query_type en lugar de nodo separado:** La alternativa era agregar un nodo de grafo `acknowledge_context` con su propia lógica. Esto requiere modificar el grafo y añadir edges. Manejar `"contexto_usuario"` en el orquestador `stream_response.py` es más simple — sigue el mismo patrón que `saludo`, `blocked` y `fuera_dominio`, que tampoco ejecutan el grafo RAG completo.

5. **No cambiar el threshold de memoria episódica (0.7):** El threshold de 0.7 coseno es razonable. El problema no es el threshold — es que los recuerdos a menudo no se extraen (store falla). Bajar el threshold sin resolver el store crearía falsos positivos en el recall. La Parte D ataca la causa raíz.

## Fuera de alcance

- LLM de query rewriting dedicado con reformulación completa de la query (complejidad O(llamada LLM) por turno).
- Clarificación interactiva multi-turno donde el usuario elige una opción numerada y el sistema la resuelve automáticamente (requiere cambios en frontend).
- Cambios en el umbral de coseno para memoria episódica (`memory_retrieval_threshold`).
- Personalización del tono del acuse de recibo por tipo de contexto (rol vs preferencia vs ubicación).
- Indexación de documentos con `area_funcional` y `title` más ricos para mejorar los topics de clarificación — es un problema de ingesta, no de runtime.

## Riesgos

| Riesgo                                                                          | Probabilidad | Impacto | Mitigación                                                                                        |
| ------------------------------------------------------------------------------- | ------------ | ------- | ------------------------------------------------------------------------------------------------- |
| El enriquecimiento de query introduce ruido y baja `retrieval_accuracy`         | Media        | Alto    | AC-12 valida no-regresión; limitar enriquecimiento a cuando el historial tiene contexto relevante |
| Clasificación errónea de consultas como `contexto_usuario` (falsos positivos)   | Baja         | Medio   | Los patrones son conservadores (solo "soy/trabajo en/prefiero"); consultas con "?" no aplican     |
| Heurísticas con `has_history` dejan pasar queries ambiguas en conversación larga | Baja         | Medio   | Solo heurísticas específicas se condicionan; LLM borderline sigue activo                         |
| Cambio de formato del prompt de clarificación rompe tests existentes            | Alta         | Bajo    | Los tests de `test_generate_clarification.py` deben actualizarse junto con el prompt             |

## Registro de implementación

**Fecha:** 2026-03-29
**Branch:** `77-t6-s8-09-10_report03-diagnostic-fixes`

### Archivos modificados

| Archivo | Parte | Cambio |
| ------- | ----- | ------ |
| `src/infrastructure/llm/prompts/clarification_prompt.py` | A | Reescrito `CLARIFICATION_SYSTEM_PROMPT`: elimina "Evita menús numéricos", instrucción explícita de lista obligatoria, 4 ejemplos few-shot con `- opción` y `?` de cierre |
| `src/application/graphs/nodes/ambiguity_detector.py` | B | Heurística 3: `and not has_history`. Heurística 6: `and not has_history`. `_AMBIGUITY_LLM_PROMPT`: instrucción OOD → CLEAR |
| `src/application/graphs/nodes/classify_intent.py` | D1 | `_CONTEXT_STATEMENT_RE` regex + clasificación `contexto_usuario` antes del check de saludo |
| `src/application/graphs/nodes/retrieve.py` | C | `_build_enriched_query()`: queries ≤5 tokens con historial reciben contexto del turno previo en el embedding |
| `src/application/use_cases/rag/stream_response.py` | D2+D3 | Handler `contexto_usuario`: acuse de recibo sin RAG + `extract_memories` con par declaración+acuse |
| `tests/unit/test_ambiguity_detector.py` | Tests B | Tests para has_history en heurísticas 3 y 6, prompt OOD |
| `tests/unit/test_classify_intent.py` | Tests D1 | Tests para detección `contexto_usuario`, falsos positivos |
| `tests/unit/test_stream_response.py` | Tests C+D2+D3 | Tests para handler `contexto_usuario` y `_build_enriched_query` |
| `pyproject.toml` | Config | `E501` per-file-ignore para `clarification_prompt.py` |

### Decisión de implementación relevante

**Heurística 4 no recibe `has_history`:** `_GENERIC_VERB_NOUN_RE` (heurística 4) incluye el patrón `¿cuál es el X genérico?` que también atrapa follow-ups válidos. La spec solo especifica heurísticas 3 y 6. Las queries atrapadas únicamente por heurística 4 pasan al LLM borderline donde el contexto de `has_history` puede resolver. Se documenta en `test_cual_es_el_limite_with_history_still_may_be_ambiguous`.

### Métricas de calidad

- **Tests:** 174/174 passed (48 tests nuevos)
- **Ruff:** 0 errores
- **Mypy:** 0 errores (corregidos 2 type errors en retrieve.py y stream_response.py)
- **ACs unitarios:** 12 IMPLEMENTADO, 9 PARCIAL (requieren eval runner en vivo)
