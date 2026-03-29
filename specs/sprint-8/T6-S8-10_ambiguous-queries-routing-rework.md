# T6-S8-10: Rediseño arquitectónico del routing de detección de queries ambiguas

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | — |
| Depende de | T6-S8-09 (pending) |
| Skill | `langgraph/SKILL.md`, `rag-retrieval/SKILL.md`, `prompt-engineering/SKILL.md`, `testing-strategy/SKILL.md` |
| Estimacion | M (4-8h) |
| Extiende | T6-S8-07 Parte A (parcialmente incompleta — ver sección Relación) |

> Corregir la categoría `ambiguous_queries` de 30% a ≥90% (objetivo: 100%) mediante rediseño del routing del grafo RAG: mover `ambiguity_detector` ANTES de `score_gate` para que TODAS las queries que completen retrieval pasen por detección de ambigüedad, independientemente de sus scores de reranking. Mejorar heurísticas de detección y robustez de generación de clarificación.

## Relación con T6-S8-07

La spec T6-S8-07 implementó correctamente los nodos `ambiguity_detector` y `generate_clarification`, junto con detección de token smuggling en el guardrail de entrada. Sin embargo, la ubicación arquitectónica del `ambiguity_detector` en el grafo fue insuficiente: solo es alcanzable cuando `score_gate` retorna `"suficiente"` (max_score ≥ 0.85).

**Estado de T6-S8-07:**
- **Parte A (ambiguous queries):** Parcialmente incompleta — los nodos funcionan correctamente cuando se alcanzan, pero el routing impide que la mayoría de queries ambiguas lleguen al detector. Esta spec (T6-S8-10) corrige el routing.
- **Parte B (token smuggling):** Completa — funciona correctamente y no requiere cambios.

**Acción requerida:** Marcar T6-S8-07 como `done (Parte A parcial — routing corregido en T6-S8-10)` para reflejar que la implementación fue correcta pero el routing fue insuficiente.

## Contexto

### Resultados de report03 — ambiguous_queries: 30% (3/10 pass, sin mejora respecto a report02)

| ID | Input | Resultado actual | Motivo de fallo | Ruta en grafo |
|----|-------|------------------|-----------------|---------------|
| AQ-001 | "necesito informacion de eso" | Fallback genérico | missing '?' | score_gate → insuficiente → respond_blocked |
| AQ-002 | "¿como hago el tramite?" | Fallback genérico | missing '?' | score_gate → insuficiente → respond_blocked |
| AQ-003 | "quiero dar de baja" | ✅ 21 opciones | pass | score_gate → suficiente → ambiguity_detector → clarificación |
| AQ-004 | "¿Como hago para pedir un adelanto?" | Respuesta directa sin opciones | 0 options found | score_gate → suficiente → ambiguity_detector → CLEAR (heurística #5) → generate |
| AQ-005 | "¿Como pido un prestamo?" | ✅ 13 opciones | pass | score_gate → suficiente → ambiguity_detector → clarificación |
| AQ-006 | "vacaciones" | Fallback genérico | missing '?' | score_gate → insuficiente → respond_blocked |
| AQ-007 | "¿Cuanto me sale?" | Fallback genérico | missing '?' | score_gate → insuficiente → respond_blocked |
| AQ-008 | "Quiero cambiar mi tarjeta" | ✅ 18 opciones | pass | score_gate → suficiente → ambiguity_detector → clarificación |
| AQ-009 | "Necesito un certificado" | Fallback genérico | missing '?' | score_gate → insuficiente → respond_blocked |
| AQ-010 | "¿Cual es el limite?" | Fallback genérico | missing '?' | score_gate → insuficiente → respond_blocked |

**Patrón claro:** Los 3 que pasan (AQ-003, AQ-005, AQ-008) alcanzan el `ambiguity_detector` porque sus queries tienen suficiente especificidad para producir scores de reranking ≥ 0.85 ("dar de baja", "prestamo", "cambiar tarjeta" son términos con alta presencia en la documentación). Los 6 que fallan con fallback genérico producen scores < 0.78 y van directo a `respond_blocked`. AQ-004 alcanza el detector pero es clasificada erróneamente como CLEAR.

## Diagnóstico

### Causa raíz principal — Paradoja arquitectónica: queries ambiguas producen scores bajos

El flujo actual del grafo:

```
retrieve → rerank → score_gate → [routing]
  ├─ "suficiente" (max_score ≥ 0.85) → ambiguity_detector ✓
  ├─ "ambiguo"    (0.78 ≤ max_score < 0.85) → topic_classifier ✗
  └─ "insuficiente" (max_score < 0.78) → respond_blocked ✗
```

La spec T6-S8-07 ubicó el `ambiguity_detector` en el path `"suficiente"` asumiendo que las queries ambiguas producirían scores altos de retrieval. **Esta suposición es incorrecta:** las queries ambiguas son inherentemente vagas, lo que produce scores de reranking bajos (el reranker no encuentra documentos altamente relevantes porque la query no especifica un tema concreto).

**Resultado:** 6 de 7 queries que fallan nunca alcanzan el `ambiguity_detector` porque van a `"insuficiente"` → `respond_blocked`. El detector de ambigüedad fue correctamente implementado pero es arquitectónicamente inalcanzable para las queries que más lo necesitan.

**Umbrales configurados (settings.py):**
- `similarity_threshold = 0.78` (umbral bajo)
- `reranking_threshold = 0.85` (umbral alto)

### Causa raíz secundaria — Heurística #5 auto-clasifica como CLEAR queries de ≥5 tokens

En `ambiguity_detector.py` (línea 189):

```python
if token_count >= 5 or _DOMAIN_SPECIFIC_RE.search(query_stripped):
    return "CLEAR"
```

Esta heurística clasifica como CLEAR toda query con 5+ tokens, incluso si es ambigua. AQ-004 ("¿Cómo hago para pedir un adelanto?") tiene 8 tokens → auto-clasificada como CLEAR sin considerar que "adelanto" es un término genérico que puede referirse a "adelanto de sueldo" o "adelanto de haberes".

La disyunción `token_count >= 5 OR domain_specific` es demasiado agresiva. Una query larga puede ser ambigua ("¿Cómo hago para pedir un adelanto?" es larga pero vaga). La condición debería requerir AMBAS condiciones (larga Y específica), no solo una.

### Causa raíz terciaria — `generate_clarification` no se testea con chunks de score bajo

El nodo `generate_clarification_node` extrae topics de `reranked_chunks` usando metadata (áreas funcionales y títulos). Cuando los chunks tienen scores bajos, la metadata todavía está disponible y es útil para generar opciones de clarificación. Sin embargo, este path no fue testeado en T6-S8-07 porque el nodo solo era alcanzable con chunks de score alto.

## Spec

### Parte A: Rediseño del routing — mover `ambiguity_detector` antes de `score_gate`

#### A1. Nuevo flujo del grafo

Modificar `rag_graph.py` para reubicar `ambiguity_detector` inmediatamente después de `rerank` y antes de `score_gate`:

**Flujo nuevo:**
```
classify_intent → guardrail_input → [routing]
  ├─ saludo → respond_greeting
  ├─ blocked → respond_blocked
  └─ consulta → retrieve → rerank → ambiguity_detector → [routing]
       ├─ needs_clarification=True → generate_clarification → END
       └─ needs_clarification=False → score_gate → [routing]
            ├─ suficiente → assemble_context → END
            ├─ ambiguo → topic_classifier → [routing]
            │    ├─ consulta → assemble_context → END
            │    └─ fuera_dominio → respond_blocked → END
            └─ insuficiente → respond_blocked → END
```

**Cambios en edges del grafo:**

1. **Eliminar** el edge condicional de `score_gate` → `ambiguity_detector` (ya no es un destino de score_gate).
2. **Cambiar** el edge lineal `rerank → score_gate` por `rerank → ambiguity_detector`.
3. **Agregar** edge condicional de `ambiguity_detector` → `{generate_clarification, score_gate}`.
4. **Actualizar** routing de `score_gate`: las 3 salidas ahora van a `{assemble_context, topic_classifier, respond_blocked}` (ya no incluyen `ambiguity_detector`).
5. Los edges de `topic_classifier` y nodos terminales se mantienen sin cambios.

#### A2. Actualizar función de routing `_route_after_ambiguity_detector`

La función existente ya tiene la lógica correcta:
```python
needs_clarification=True  → "generate_clarification"
needs_clarification=False → siguiente nodo
```

Solo cambiar el destino del path `False` de `"assemble_context"` a `"score_gate"`.

#### A3. Actualizar función de routing `_route_after_score_gate`

Eliminar el destino `"ambiguity_detector"` del routing de score_gate. Los nuevos destinos son:
- `"suficiente"` → `"assemble_context"` (directo, ya no pasa por ambiguity_detector)
- `"ambiguo"` → `"topic_classifier"` (sin cambio)
- `"insuficiente"` → `"respond_blocked"` (sin cambio)

#### A4. Actualizar documentación del grafo

Actualizar el docstring del módulo `rag_graph.py` y el docstring de `build_rag_graph` para reflejar el nuevo flujo.

### Parte B: Mejora de heurísticas de detección de ambigüedad

#### B1. Corregir heurística #5 — no auto-clasificar como CLEAR por longitud

Modificar la heurística #5 en `ambiguity_detector.py` para que NO clasifique como CLEAR solo por tener ≥5 tokens. El cambio debe ser:

- **Antes:** `token_count >= 5 OR domain_specific → CLEAR`
- **Después:** `domain_specific → CLEAR` (solo si hay entidad de dominio específica)

La longitud de la query por sí sola no indica claridad. "¿Cómo hago para pedir un adelanto?" tiene 8 tokens pero es ambigua. Solo la presencia de un término de dominio específico (como "adelanto de sueldo" o "préstamo hipotecario") debería forzar CLEAR.

Si la query tiene ≥5 tokens y no matchea _DOMAIN_SPECIFIC_RE ni _GENERIC_PATTERN_RE, debe caer al LLM como caso borderline (retornar `None`), en lugar de asumir CLEAR.

#### B2. Incorporar score de retrieval como señal de ambigüedad

Agregar una nueva heurística que use el score máximo de reranking como señal complementaria. Si el max_score de los chunks es bajo (< `similarity_threshold`), la query tiene mayor probabilidad de ser ambigua:

- Si `max_score < similarity_threshold` Y (`token_count <= 3` O `_GENERIC_PATTERN_RE` matchea) → AMBIGUOUS con mayor certeza.
- Esta señal refuerza las heurísticas existentes. No debe ser el único factor (un score bajo puede indicar que la pregunta es clara pero no hay documentación sobre el tema).

El nodo debe leer `reranked_chunks` (que ya recibe del estado) y extraer el `max_score` para esta evaluación. No se requieren nuevos campos en el estado.

#### B3. Expandir patrones genéricos para capturar variantes con complemento genérico

La regex `_GENERIC_PATTERN_RE` actualmente requiere que la frase genérica sea el final de la query (`$`). Esto es correcto para "¿Cómo hago?" pero no captura "¿Cómo hago para pedir un adelanto?" donde hay un complemento genérico.

Agregar variantes de patrones que detecten frases genéricas seguidas de un sustantivo genérico del dominio bancario. Definir una lista de sustantivos genéricos que por sí solos son ambiguos (no confundir con `_DOMAIN_SPECIFIC_RE` que son términos compuestos específicos):

Sustantivos genéricos (ambiguos sin calificador): `adelanto`, `certificado`, `límite`, `tarjeta`, `trámite`, `servicio`, `producto`, `paquete`, `seguro`, `cuenta`, `crédito`, `débito`, `préstamo`, `licencia`, `baja`, `alta`.

Crear un patrón que detecte frases como:
- "¿Cómo hago para pedir un **adelanto**?" (genérico + sustantivo genérico)
- "Necesito un **certificado**" (necesito + sustantivo genérico)
- "¿Cuál es el **límite**?" (cuál es + sustantivo genérico)

La detección debe funcionar con cualquier combinación de verbo introductorio + sustantivo genérico, no solo las combinaciones hardcodeadas del golden dataset. El sistema debe ser capaz de detectar ambigüedad en queries futuras que no estén en el dataset actual.

**Importante:** La lista de sustantivos genéricos NO es la solución principal — es un complemento. La solución principal es el cambio de routing (Parte A) que asegura que TODAS las queries pasen por el detector. Los sustantivos genéricos mejoran la precisión del detector para casos borderline como AQ-004.

### Parte C: Robustez de generación de clarificación con chunks de calidad variable

#### C1. Verificar que `generate_clarification_node` funciona con chunks de score bajo

Con el nuevo routing, `generate_clarification_node` recibirá `reranked_chunks` que pueden tener scores por debajo de `similarity_threshold` (0.78). El nodo ya usa solo metadata (áreas funcionales y títulos), no contenido de chunks, por lo que debería funcionar correctamente independientemente del score.

Verificar que:
1. La extracción de topics (`_extract_topics_from_chunks`) funciona con chunks de score bajo.
2. Si los chunks no tienen metadata de áreas funcionales (campo vacío), el fallback con topics genéricos se activa correctamente.
3. El LLM genera opciones de clarificación coherentes incluso cuando los topics disponibles son limitados o genéricos.

#### C2. Mejorar fallback de topics para queries sin retrieval relevante

Si `reranked_chunks` está vacío o todos los chunks carecen de metadata de área funcional, el fallback actual genera opciones genéricas ("Información general sobre el tema", "Proceso o trámite relacionado"). Estas son poco útiles.

Mejorar el fallback para que use la query del usuario como contexto. En lugar de opciones genéricas estáticas, generar opciones que reflejen las categorías principales del dominio bancario relevantes a la query. Esto puede lograrse incluyendo la query del usuario en el prompt de clarificación del LLM, que ya recibe el parámetro `query`.

El prompt de clarificación existente ya incluye la query. Solo verificar que el prompt instruya al LLM a generar opciones relevantes a la query incluso cuando los topics son limitados.

#### C3. Test de integración para flujo completo con query ambigua

Crear test que simule el flujo completo para una query ambigua que produce scores bajos:
1. Mock de `reranked_chunks` con scores < 0.78 y metadata variada
2. Verificar que `ambiguity_detector_node` clasifica como AMBIGUOUS
3. Verificar que `generate_clarification_node` genera respuesta con ≥2 opciones y `?`
4. Verificar que el formato cumple con el regex del evaluador: `_OPTIONS_RE = re.compile(r"^[ \t]*(?:[-•*]|\d+[.)]) ", re.MULTILINE)`

## Acceptance Criteria

### Parte A — Routing

- [ ] **AC-1**: El edge `rerank → score_gate` ya no existe. `rerank` se conecta a `ambiguity_detector`.
- [ ] **AC-2**: `ambiguity_detector` tiene edge condicional hacia `{generate_clarification, score_gate}` basado en `needs_clarification`.
- [ ] **AC-3**: `score_gate` tiene routing hacia `{assemble_context, topic_classifier, respond_blocked}` — ya no incluye `ambiguity_detector`.
- [ ] **AC-4**: Query `"vacaciones"` (1 palabra, sin dominio específico) alcanza `ambiguity_detector` y es clasificada como AMBIGUOUS.
- [ ] **AC-5**: Query `"¿Cuánto me sale?"` alcanza `ambiguity_detector` y es clasificada como AMBIGUOUS.
- [ ] **AC-6**: Query `"¿Cuántos días de vacaciones tengo por antigüedad?"` (clara y específica) alcanza `ambiguity_detector`, es clasificada como CLEAR, y continúa a `score_gate`.

### Parte B — Heurísticas

- [ ] **AC-7**: Query `"¿Cómo hago para pedir un adelanto?"` es clasificada como AMBIGUOUS (no como CLEAR por heurística #5).
- [ ] **AC-8**: Query `"Necesito un certificado"` es clasificada como AMBIGUOUS.
- [ ] **AC-9**: Query `"¿Cuántos días de licencia por maternidad tengo?"` es clasificada como CLEAR (contiene término de dominio específico).
- [ ] **AC-10**: La heurística de longitud (`token_count >= 5`) ya NO fuerza CLEAR por sí sola — solo `_DOMAIN_SPECIFIC_RE` matcheando fuerza CLEAR.
- [ ] **AC-11**: El score máximo de los chunks se usa como señal complementaria de ambigüedad (no como único factor).

### Parte C — Clarificación

- [ ] **AC-12**: `generate_clarification_node` genera respuesta con `?` y ≥2 opciones numeradas cuando recibe chunks con scores < 0.78.
- [ ] **AC-13**: Respuesta de clarificación cumple formato del evaluador: opciones con patrón `re.compile(r"^[ \t]*(?:[-•*]|\d+[.)]) ", re.MULTILINE)`.
- [ ] **AC-14**: Cuando `reranked_chunks` está vacío, el nodo genera clarificación con opciones genéricas contextualizadas a la query.

### Evaluación end-to-end

- [ ] **AC-15**: Los 10 test cases de `ambiguous_queries` del golden dataset obtienen pass rate ≥ 90% (objetivo: 100%, margen para AQ-004 que depende del LLM).
- [ ] **AC-16**: Los 3 test cases que ya pasaban (AQ-003, AQ-005, AQ-008) siguen pasando sin regresión.

### No-Regresión

- [ ] **AC-17**: Suite completa de tests unitarios pasa sin fallos.
- [ ] **AC-18**: Las categorías que ya estaban en 100% (`topic_classification`, `guardrails_output`, `system_prompt_behavior`) no regresan.
- [ ] **AC-19**: `retrieval_accuracy` no disminuye (≥ 83.3%).
- [ ] **AC-20**: Queries claras y específicas siguen generando respuestas directas (no se fuerza clarificación innecesaria).

## Archivos a modificar

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `src/application/graphs/rag_graph.py` | Modificar | Reubicar ambiguity_detector antes de score_gate, actualizar edges y routing functions |
| `src/application/graphs/nodes/ambiguity_detector.py` | Modificar | Corregir heurística #5, agregar señal de score de retrieval, expandir patrones genéricos |
| `src/application/graphs/nodes/generate_clarification.py` | Modificar (si necesario) | Verificar robustez con chunks de score bajo, mejorar fallback de topics |
| `src/infrastructure/llm/prompts/clarification_prompt.py` | Modificar (si necesario) | Ajustar prompt si el fallback de topics necesita mejora |
| `tests/unit/test_ambiguity_detector.py` | Modificar | Actualizar tests de heurísticas, agregar tests con score de retrieval |
| `tests/unit/test_generate_clarification.py` | Modificar | Agregar tests con chunks de score bajo |
| `tests/unit/test_rag_graph.py` | Modificar (si existe) | Verificar nuevo routing del grafo |
| `specs/sprint-8/T6-S8-07_ambiguous-queries-and-token-smuggling-fix.md` | Modificar | Marcar Parte A como parcialmente incompleta, referencia a T6-S8-10 |

## Decisiones de diseño

1. **Mover ANTES de score_gate, no replicar en cada path:** La alternativa era mantener ambiguity_detector después de score_gate y hacerlo alcanzable desde los 3 paths. Esto fue descartado porque crea routing complejo (cada path post-detector necesita su propio destino) y no aborda la causa raíz. Mover antes de score_gate es un cambio limpio que garantiza que TODAS las queries pasan por detección de ambigüedad.

2. **No implementar detección pre-retrieval:** La alternativa de dos fases (pre + post retrieval) fue descartada por complejidad. La fase pre-retrieval no tiene acceso a metadata de documentos, lo que limita severamente la calidad de las opciones de clarificación. La latencia adicional de ejecutar retrieval para queries ambiguas es aceptable (< 1s) comparada con el beneficio de generar opciones de clarificación informadas por la documentación real.

3. **Heurística de longitud degradada a no-decisión:** Eliminar la auto-clasificación CLEAR por longitud puede causar que más queries pasen al LLM para clasificación borderline. Esto es aceptable: el LLM es Gemini Flash Lite (latencia ~200ms, costo mínimo) y la precisión del LLM es superior a la heurística de longitud. La heurística solo se usaba como optimización de costo, no de precisión.

4. **Sustantivos genéricos como complemento, no solución principal:** La lista de sustantivos genéricos mejora la detección en edge cases pero no es la solución principal. El cambio de routing (Parte A) asegura que las queries lleguen al detector. La mejora de heurísticas (Parte B) mejora la precisión del detector. Ambos cambios son necesarios.

## Fuera de alcance

- Modificación de los umbrales de `score_gate` (`similarity_threshold`, `reranking_threshold`). Estos valores están calibrados para retrieval accuracy y no deben alterarse para resolver ambiguity detection.
- Implementación de clarificación interactiva multi-turno (el usuario elige una opción y el sistema responde). Esto requiere cambios en el frontend y el manejo de estado de conversación.
- Cambios en `topic_classifier` — mantiene su función actual como red de seguridad para queries on-topic/off-topic.
- Optimización de performance del nuevo path (el overhead adicional de ambiguity_detector es < 200ms y aceptable).

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Ambiguity detector clasifica como AMBIGUOUS queries que antes generaban respuesta correcta | Media | Alto | AC-16 y AC-20 validan no-regresión; tests con queries claras |
| LLM genera opciones de clarificación incoherentes con chunks de score bajo | Baja | Medio | Prompt de clarificación usa metadata (no contenido); fallback con topics genéricos |
| Aumento de latencia por paso adicional en el pipeline | Baja | Bajo | Heurísticas son O(1); LLM solo para borderline (~200ms) |
| Cambio de routing causa fallos en nodes downstream que asumen orden anterior | Baja | Alto | Tests de integración del grafo completo; verificar que todos los campos del estado necesarios están disponibles |

## Registro de implementación

| Campo | Valor |
|-------|-------|
| Fecha | 2026-03-28 |
| Branch | `77-t6-s8-09-10_report03-diagnostic-fixes` |
| Commit | `905645a` |
| Tests baseline | 811 passed |
| Tests post-impl (acumulado) | 846 passed (+35 nuevos) |
| Regressions | 0 |

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/application/graphs/rag_graph.py` | Reubicado `ambiguity_detector` antes de `score_gate`. Nuevo flujo: `rerank → ambiguity_detector → score_gate`. Actualizado routing + docstrings. |
| `src/application/graphs/nodes/ambiguity_detector.py` | Eliminada heurística #5 (token_count >= 5 → CLEAR). Agregado `_GENERIC_NOUNS` (20 sustantivos), `_GENERIC_VERB_NOUN_RE`, señal de score bajo. Solo `_DOMAIN_SPECIFIC_RE` fuerza CLEAR. |
| `tests/unit/test_rag_graph.py` | 3 tests nuevos (routing: ambiguous → clarification, clear → score_gate, score_gate destinations) |
| `tests/unit/test_ambiguity_detector.py` | 8 tests nuevos/actualizados (heurísticas, AQ-004, AQ-005, low score, domain-specific) |
| `tests/unit/test_generate_clarification.py` | 4 tests nuevos (low-score chunks, empty chunks, no-metadata chunks) |

### AC verificados

17/20 AC verificados con tests unitarios. AC-15 (end-to-end pass rate), AC-18 (category regression), AC-19 (retrieval_accuracy) requieren ejecución del eval runner contra la API live.

### Notas de implementación

- AQ-005 "¿Como pido un prestamo?" ahora es AMBIGUOUS por heurística (generic verb + generic noun "prestamo"). En report03 ya pasaba con clarificación, por lo que no hay regresión funcional.
- Las queries con domain-specific compounds (e.g. "licencia por maternidad", "adelanto de sueldo") siguen siendo CLEAR — sin riesgo de over-clarification.
