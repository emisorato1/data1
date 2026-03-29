# T6-S8-11: Entrega de clarificación en orquestador SSE y gap de verbos intermedios en heurísticas

## Meta


| Campo           | Valor                                                                                                      |
| --------------- | ---------------------------------------------------------------------------------------------------------- |
| Track           | T6 (Franco)                                                                                                |
| Prioridad       | Crítica (bloquea toda la funcionalidad de clarificación)                                                   |
| Estado          | done                                                                                                       |
| Bloqueante para | —                                                                                                          |
| Depende de      | T6-S8-10 (done)                                                                                            |
| Skill           | `langgraph/SKILL.md`, `rag-retrieval/SKILL.md`, `prompt-engineering/SKILL.md`, `testing-strategy/SKILL.md` |
| Estimacion      | S (2-4h)                                                                                                   |
| Extiende        | T6-S8-10 (routing y heurísticas corregidas pero la entrega al usuario está rota)                           |


> Corregir dos bugs que inutilizan la funcionalidad de clarificación en producción: (1) el orquestador SSE no tiene ruta de ejecución para consultas que requieren clarificación, descartando la respuesta profesional generada por el nodo de clarificación y retornando el mensaje de fallback genérico; (2) la regex de detección de verbos genéricos no captura queries con verbos de acción intermedios (por ejemplo "Quiero sacar un préstamo"), permitiendo que escapen al LLM que las clasifica como CLEAR.

## Relación con T6-S8-10

T6-S8-10 corrigió correctamente el routing del grafo, las heurísticas de detección y la generación de clarificación con chunks de score bajo. Sin embargo, la capa de orquestación que conecta el resultado del grafo con la respuesta SSE al usuario no fue modificada. El grafo genera clarificaciones profesionales correctamente pero el orquestador las descarta.

## Contexto

### Síntomas reportados en producción

1. Queries como "Quiero sacar un préstamo" se responden directamente, saltándose la clarificación.
2. Las clarificaciones que ocurren son genéricas y no usan el estilo profesional configurado en el prompt de clarificación.

### Evidencia del report03 — ambiguous_queries: 30% (7/10 fallos)


| ID     | Query                                | Respuesta actual                          | Fallo                       | Causa raíz           |
| ------ | ------------------------------------ | ----------------------------------------- | --------------------------- | -------------------- |
| AQ-001 | "necesito informacion de eso"        | "No encontre informacion suficiente..."   | falta signo de pregunta     | Bug 1                |
| AQ-002 | "¿como hago el tramite?"             | "No encontre informacion suficiente..."   | falta signo de pregunta     | Bug 1                |
| AQ-004 | "¿Como hago para pedir un adelanto?" | "Si cobrás tu sueldo o jubilación con..." | 0 opciones de clarificación | Bug 2 (pre-T6-S8-10) |
| AQ-006 | "vacaciones"                         | "No encontre informacion suficiente..."   | falta signo de pregunta     | Bug 1                |
| AQ-007 | "¿Cuanto me sale?"                   | "No encontre informacion suficiente..."   | falta signo de pregunta     | Bug 1                |
| AQ-009 | "Necesito un certificado"            | "No encontre informacion suficiente..."   | falta signo de pregunta     | Bug 1                |
| AQ-010 | "¿Cual es el limite?"                | "No encontre informacion suficiente..."   | falta signo de pregunta     | Bug 1                |


Seis de siete fallos retornan el mensaje de fallback genérico en lugar de la clarificación profesional generada por el grafo.

## Diagnóstico

### Bug 1 (Crítico): El orquestador SSE descarta las respuestas de clarificación

Cuando el detector de ambigüedad clasifica una query como ambigua, el grafo ejecuta el nodo de generación de clarificación que produce una respuesta profesional con opciones contextuales. Esta respuesta queda almacenada en el campo `response` del estado del grafo.

Sin embargo, el orquestador SSE en `stream_response.py` solo consulta el campo `query_type` para decidir si usar la respuesta del grafo directamente. Las únicas categorías que disparan esta ruta directa son `saludo`, `blocked` y `fuera_dominio`. Las queries ambiguas mantienen `query_type` como `consulta` (asignado por el clasificador de intención), por lo que caen a la fase de streaming LLM.

En la fase de streaming, el orquestador verifica si existe contexto ensamblado. Como el nodo de ensamblaje de contexto nunca se ejecutó (la ruta de clarificación lo omite), el campo `context_text` está vacío. Al detectar contexto vacío, el orquestador retorna el mensaje de fallback genérico ("No encontré información suficiente..."), descartando completamente la clarificación profesional que el grafo generó correctamente.

**Ubicación del bug:** `stream_response.py`, función `stream_rag_events`, entre la verificación de `query_type` (línea 197) y la verificación de `context_text` (línea 228). Falta una ruta intermedia que detecte `needs_clarification=True` en el resultado del grafo y use la respuesta de clarificación directamente.

### Bug 2 (Importante): Gap en la regex de verbos genéricos para verbos intermedios

La segunda alternativa de la regex `_GENERIC_VERB_NOUN_RE` en `ambiguity_detector.py` detecta patrones del tipo "necesito/quiero + artículo + sustantivo genérico" (por ejemplo "Quiero un préstamo"). Sin embargo, no contempla un verbo de acción entre la intención y el sustantivo.

Cuando el usuario dice "Quiero **sacar** un préstamo", la regex intenta hacer match del artículo inmediatamente después de "quiero" pero encuentra "sacar" que no es un artículo. El grupo de artículos es opcional, por lo que la regex avanza e intenta hacer match del sustantivo genérico, pero encuentra "sacar" que no está en la lista de sustantivos. El match falla y la query cae al LLM como caso borderline, donde puede ser clasificada como CLEAR.

La primera alternativa de la regex (para patrones con "cómo hago/puedo") SÍ funciona con verbos intermedios porque usa un comodín amplio entre el verbo introductorio y el sustantivo. El gap es exclusivo de la segunda alternativa.

Queries afectadas que no son capturadas por las heurísticas:


| Query                             | Verbo intermedio |
| --------------------------------- | ---------------- |
| "Quiero sacar un préstamo"        | sacar            |
| "Quiero pedir un certificado"     | pedir            |
| "Necesito tramitar una licencia"  | tramitar         |
| "Quiero solicitar un crédito"     | solicitar        |
| "Quiero consultar mi cuenta"      | consultar        |
| "Necesito obtener un certificado" | obtener          |


## Spec

### 1. Agregar ruta de clarificación en el orquestador SSE — `stream_response.py`

Modificar la función `stream_rag_events` para detectar cuándo el grafo activó una clarificación. Después de la verificación de `query_type` para respuestas directas (saludo, bloqueado, fuera de dominio) y antes de la fase de streaming LLM, agregar una verificación del campo `needs_clarification` en el resultado del grafo.

Cuando `needs_clarification` sea verdadero, el orquestador debe:

- Extraer la respuesta de clarificación del campo `response` del resultado del grafo.
- Emitir la respuesta completa como evento SSE de tipo `token` (igual que saludos y bloqueos).
- Persistir la respuesta como mensaje del asistente en la base de datos.
- Emitir el evento `done` con fuentes vacías (no hay respuesta basada en documentación).
- Retornar sin entrar a la fase de streaming LLM ni al guardrail de salida.

La respuesta de clarificación no debe pasar por `validate_output` porque no tiene contexto contra el cual evaluar fidelidad, es una pregunta de clarificación y no una respuesta informativa, y el guardrail de salida podría bloquearla o modificarla innecesariamente.

### 2. Ampliar regex de verbos genéricos con verbos de acción intermedios — `ambiguity_detector.py`

Modificar la segunda alternativa de `_GENERIC_VERB_NOUN_RE` para incorporar un grupo opcional de verbos de acción transaccionales entre el verbo de intención (`necesito`/`quiero`) y el artículo + sustantivo genérico.

Los verbos intermedios a incorporar son: `sacar`, `pedir`, `solicitar`, `hacer`, `obtener`, `tramitar`, `consultar`, `ver`, `saber`. Esta lista cubre los verbos transaccionales más frecuentes del dominio bancario.

Adicionalmente, expandir la lista de artículos para incluir las formas plurales (`los`, `las`) y así capturar variantes como "Quiero ver las tarjetas"

La lógica de verificación existente (heurística 4) ya protege contra falsos positivos: si la query contiene un término de dominio específico (por ejemplo "préstamo hipotecario" o "licencia por maternidad"), la query se clasifica como CLEAR independientemente del match de la regex ampliada. No se requiere modificar esta lógica.

### 3. Tests unitarios para la entrega de clarificación — `test_stream_response.py`

Agregar tests que verifiquen el nuevo flujo de clarificación en el orquestador:

- Cuando el resultado del grafo tiene `needs_clarification` verdadero y `response` con contenido, el orquestador debe emitir esa respuesta (no el fallback genérico).
- Cuando `needs_clarification` es falso y `query_type` es `consulta`, el flujo debe continuar a la fase de streaming LLM sin cambios.
- La respuesta de clarificación debe persistirse como mensaje del asistente.
- El evento `done` debe enviarse con fuentes vacías.

### 4. Tests unitarios para verbos intermedios — `test_ambiguity_detector.py`

Agregar tests parametrizados para las queries con verbos intermedios:

- Queries ambiguas con verbo intermedio: "Quiero sacar un préstamo", "Necesito tramitar una licencia", "Quiero pedir un certificado", "Quiero solicitar un crédito".
- Queries claras con verbo intermedio y término de dominio específico: "Quiero sacar un préstamo hipotecario", "Necesito tramitar una licencia por maternidad".
- No-regresión del patrón sin verbo intermedio: "Quiero un préstamo" sigue siendo ambigua.

## Acceptance Criteria

### Parte A — Entrega de clarificación

- **AC-1**: Cuando el grafo retorna `needs_clarification` verdadero, el orquestador SSE entrega la respuesta de clarificación profesional generada por el nodo de clarificación — no el mensaje de fallback genérico.
- **AC-2**: La respuesta de clarificación se persiste en la base de datos como mensaje del asistente.
- **AC-3**: El evento SSE `done` se envía con fuentes vacías.
- **AC-4**: La respuesta de clarificación no pasa por el guardrail de salida.
- **AC-5**: Cuando `needs_clarification` es falso y `query_type` es `consulta`, el flujo sigue la fase de streaming LLM sin cambios.

### Parte B — Verbos intermedios

- **AC-6**: "Quiero sacar un préstamo" es clasificada como AMBIGUOUS por heurística determinista.
- **AC-7**: "Necesito tramitar una licencia" es clasificada como AMBIGUOUS por heurística determinista.
- **AC-8**: "Quiero pedir un certificado" es clasificada como AMBIGUOUS por heurística determinista.
- **AC-9**: "Quiero solicitar un crédito" es clasificada como AMBIGUOUS por heurística determinista.
- **AC-10**: "Quiero sacar un préstamo hipotecario" sigue siendo CLEAR (override por término de dominio específico).
- **AC-11**: "Necesito tramitar una licencia por maternidad" sigue siendo CLEAR.
- **AC-12**: "Quiero un préstamo" sigue siendo AMBIGUOUS (no-regresión del patrón existente sin verbo intermedio).

### No-Regresión

- **AC-13**: Suite completa de tests unitarios pasa sin fallos.
- **AC-14**: Queries claras y específicas siguen generando respuestas directas sin clarificación innecesaria.
- **AC-15**: Los 3 test cases de ambiguous_queries que pasaban en report03 (AQ-003, AQ-005, AQ-008) no regresan.

## Archivos a modificar


| Archivo                                              | Acción                                                                                                          |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `src/application/use_cases/rag/stream_response.py`   | Modificar — agregar ruta de ejecución para clarificación entre verificación de `query_type` y fase de streaming |
| `src/application/graphs/nodes/ambiguity_detector.py` | Modificar — ampliar segunda alternativa de la regex de verbos genéricos con verbos de acción intermedios        |
| `tests/unit/test_stream_response.py`                 | Modificar — agregar tests para flujo de clarificación                                                           |
| `tests/unit/test_ambiguity_detector.py`              | Modificar — agregar tests para queries con verbos intermedios                                                   |


## Decisiones de diseño

1. **Clarificación como respuesta directa, no streaming incremental:** La respuesta de clarificación ya está completa en el resultado del grafo. No hay necesidad de streaming token-a-token adicional. Se entrega como un único evento SSE seguido de evento de finalización, igual que saludos y respuestas bloqueadas. Esto es consistente con el patrón existente para respuestas que no requieren generación LLM en la fase de streaming.
2. **No agregar campo de clarificación al modelo de mensaje:** Se consideró agregar un campo booleano al modelo `Message` para que el frontend pueda renderizar clarificaciones con un estilo diferente. Se descartó por alcance — el frontend puede inferirlo del contenido (presencia de opciones o signos de pregunta) o se puede agregar en una spec futura si es necesario.
3. **Lista finita de verbos intermedios, no comodín:** Se optó por una lista explícita de verbos transaccionales en lugar de aceptar cualquier palabra. Esto evita falsos positivos como "Quiero entender un préstamo" (el usuario quiere comprender, no solicitar — no es una query ambigua transaccional). La lista cubre los verbos más frecuentes del dominio bancario y puede extenderse si se identifican nuevos patrones.

## Fuera de alcance

- Modificación del frontend para renderizar clarificaciones con estilo diferente.
- Clarificación interactiva multi-turno (usuario elige opción, sistema responde según selección).
- Cambios en el nodo de generación de clarificación o en el prompt de clarificación — ambos funcionan correctamente; el problema está en la entrega.
- Ejecución del eval runner completo contra la API en vivo.

## Riesgos


| Riesgo                                                                    | Probabilidad | Impacto | Mitigación                                                                                                                    |
| ------------------------------------------------------------------------- | ------------ | ------- | ----------------------------------------------------------------------------------------------------------------------------- |
| La regex ampliada captura queries que no son ambiguas                     | Baja         | Medio   | AC-10 y AC-11 validan que el override por término de dominio específico sigue funcionando; la lista de verbos es conservadora |
| La clarificación se entrega pero con formato incorrecto                   | Baja         | Bajo    | El formato depende del nodo de generación de clarificación que ya tiene tests de validación de formato                        |
| La verificación de `needs_clarification` interfiere con flujos existentes | Baja         | Alto    | El campo se resetea a falso en cada turno por el orquestador; solo es verdadero cuando el nodo de clarificación ejecutó       |


