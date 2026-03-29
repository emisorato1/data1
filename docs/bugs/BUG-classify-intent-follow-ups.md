# BUG: classify_intent bloquea follow-ups conversacionales válidos

## Fecha: 2026-03-19
## Severidad: CRÍTICA
## Estado: Pendiente
## Reportado por: Testing manual del chat

---

## Resumen ejecutivo

El nodo `classify_intent` clasifica incorrectamente como `fuera_dominio` consultas que son
follow-ups válidos dentro de una conversación bancaria. Esto rompe la experiencia
conversacional del chat porque el usuario recibe "Esa consulta esta fuera de mi area de
conocimiento" cuando pide un resumen de lo que el bot acaba de responder.

Adicionalmente, el `topic_classifier` (LLM) tiene un falso negativo: clasifica "como hago torta?"
como `ON_TOPIC` cuando debería ser `OFF_TOPIC`.

---

## Hallazgos detallados

### BUG 1: Follow-ups bloqueados por classify_intent (P0 — CRÍTICO)

**Archivo:** `src/application/graphs/nodes/classify_intent.py`

**Síntoma en logs:**
```
classify_intent: fuera_dominio query='haceme un resumen de eso' significant_words=['haceme', 'resumen', 'eso']
classify_intent: fuera_dominio query='dame una version corta' significant_words=['dame', 'version', 'corta']  
classify_intent: fuera_dominio query='que mas puedo hacer?' significant_words=['mas', 'puedo', 'hacer']
```

**Causa raíz:**

La heurística en `classify_intent_node()` (líneas 280-293) clasifica como `fuera_dominio`
cualquier query con ≥3 palabras significativas donde NINGUNA pertenezca a `_DOMAIN_KEYWORDS`.

El problema es que **no tiene en cuenta el contexto conversacional**. Las frases de follow-up
como "haceme un resumen de eso", "dame una versión corta" o "que más puedo hacer?" no
contienen keywords bancarias, pero son solicitudes legítimas **dentro** de una conversación
que ya está en dominio.

```python
# Código problemático (líneas 280-293):
significant_words = [w for w in words if w not in _STOPWORDS]

if len(significant_words) >= _MIN_WORDS_FOR_OOD:
    has_domain_keyword = any(w in _DOMAIN_KEYWORDS for w in significant_words)
    if not has_domain_keyword:
        return {"query_type": "fuera_dominio"}  # ← Bloquea follow-ups!
```

**Impacto:** Rompe la conversación. Un empleado pregunta sobre blanqueo de PIN, recibe una
respuesta detallada de 12 pasos, pide "haceme un resumen" y el bot le dice que está fuera
de su área. La experiencia es terrible.

**Propuesta de fix:**

Opción A (recomendada): **Agregar detección de follow-ups conversacionales.**

Crear un set `_FOLLOWUP_PATTERNS` que detecte frases de referencia al contexto previo (pronombres
demostrativos, verbos de resumen, etc.) y las deje pasar como `"consulta"` en lugar de
clasificarlas como `fuera_dominio`.

```python
# Palabras/patrones que indican un follow-up conversacional.
# Si la query contiene alguna de estas, se asume que refiere al contexto previo
# y NO se clasifica como fuera_dominio.
_FOLLOWUP_INDICATORS = frozenset({
    # Pronombres demostrativos / referencias contextuales
    "eso", "esto", "esa", "ese", "esos", "esas",
    "anterior", "anteriores", "previo", "previa",
    "mismo", "misma", "mismos", "mismas",
    # Verbos de solicitud sobre respuesta previa
    "resumen", "resumir", "resumime", "resumilo",
    "version", "corta", "breve", "simplifica",
    "explica", "explicame", "explicalo", "detalla", "amplia",
    "repeti", "repetir", "repetilo", "repetime",
    # Follow-up conversacional
    "mas", "otra", "otro", "otro",
    "tambien", "ademas", "aparte",
})
```

Luego, antes de la clasificación `fuera_dominio`, verificar:

```python
# --- Follow-up detection (ANTES del check de fuera_dominio) ---
has_followup = any(w in _FOLLOWUP_INDICATORS for w in significant_words)
if has_followup:
    logger.debug("classify_intent: follow-up detected, query=%r", query[:80])
    return {"query_type": "consulta"}
```

Opción B (más robusta, más compleja): Pasar el `conversation_history` al nodo `classify_intent`
y verificar si hay mensajes previos en la conversación. Si hay historial, asumir que queries
cortas sin domain keywords son follow-ups.

```python
# Si hay historial de conversación, queries sin domain keywords
# probablemente son follow-ups sobre el tema previo.
messages = state.get("messages", [])
if len(messages) > 0 and not has_domain_keyword:
    logger.debug("classify_intent: possible follow-up (has history), query=%r", query[:80])
    return {"query_type": "consulta"}
```

**Recomendación:** Implementar Opción A primero (rápido, cubre el 90% de los casos).
Opción B se puede agregar después como mejora adicional.

---

### BUG 2: topic_classifier clasifica "como hago torta?" como ON_TOPIC (P1)

**Archivo:** `src/application/graphs/nodes/topic_classifier.py`
**Guard:** `src/infrastructure/security/guardrails/topic_guard.py`

**Síntoma en logs:**
```
topic_classifier: ON_TOPIC query=como hago torta?
retrieve: 20 chunks encontrados para la query 'como hago torta?'
rerank: 5 chunks rerankeados (top 5 seleccionados)
# → Respuesta fallback después de retrieval + reranking innecesarios
```

**Causa raíz:**

La query "como hago torta?" tiene solo 2 palabras significativas ("hago", "torta"), por lo que
`classify_intent` la deja pasar (umbral es ≥3 palabras para fuera_dominio). Luego el
`topic_classifier` con LLM la clasifica como ON_TOPIC incorrectamente.

Esto puede deberse a:
1. El few-shot prompt del TopicGuard no tiene suficientes ejemplos de cocina/recetas como OFF_TOPIC.
2. La palabra "hago" podría confundir al LLM (¿"cómo hago" un trámite bancario?).

**Impacto:** Bajo (el fallback funciona), pero desperdicia tokens y latencia (~4 seg de retrieval + reranking innecesarios).

**Propuesta de fix:**

Revisar el prompt few-shot en `TopicGuard` y agregar ejemplos OFF_TOPIC de este tipo:
```
OFF_TOPIC: "como hago torta?" (cocina, no bancario)
OFF_TOPIC: "dame la receta de empanadas" (cocina)
OFF_TOPIC: "que tiempo hace hoy?" (clima)
```

Verificar el archivo `src/infrastructure/security/guardrails/topic_guard.py` y su configuración
en `src/config/topic_config.py`.

---

### BUG 3: Mensaje de "fuera_dominio" ofrece más ayuda (P1)

**Archivo:** `src/application/graphs/nodes/respond_blocked.py`

**Síntoma:**
```
"Esa consulta esta fuera de mi area de conocimiento. Estoy preparado para 
responder preguntas sobre documentacion bancaria interna, politicas, 
procedimientos y temas de RRHH. En que puedo ayudarte?"
                                                     ^^^^^^^^^^^^^^^^^^^
```

**Problema:** Según las directivas del macro del banco (spec T4-S7-02), cuando se rechaza
una consulta NO se debe ofrecer más ayuda ("¿En qué puedo ayudarte?"). El mensaje debe
terminar directamente con la indicación de lo que sí puede hacer, sin la pregunta de cortesía.

**Propuesta de fix:**

En `respond_blocked.py`, líneas 23-28, cambiar `_OUT_OF_DOMAIN_RESPONSE`:

```python
# ANTES:
_OUT_OF_DOMAIN_RESPONSE = (
    "Esa consulta esta fuera de mi area de conocimiento. "
    "Estoy preparado para responder preguntas sobre documentacion "
    "bancaria interna, politicas, procedimientos y temas de RRHH. "
    "En que puedo ayudarte?"
)

# DESPUÉS:
_OUT_OF_DOMAIN_RESPONSE = (
    "Esa consulta está fuera de mi área de conocimiento. "
    "Estoy preparado para responder preguntas sobre documentación "
    "bancaria interna, políticas, procedimientos y temas de RRHH."
)
```

Además, aplicar el mismo criterio al `_GREETING_RESPONSE` para que use tildes correctamente:

```python
# ANTES:
_GREETING_RESPONSE = "Hola! Soy el asistente de documentacion bancaria interna. En que puedo ayudarte hoy?"

# DESPUÉS:
_GREETING_RESPONSE = "¡Hola! Soy el asistente de documentación bancaria interna. ¿En qué puedo ayudarte hoy?"
```

Y en `_BLOCKED_RESPONSE`, agregar tildes:
```python
# DESPUÉS:
_BLOCKED_RESPONSE = (
    "Lo siento, no puedo procesar esta consulta. "
    "Por favor, reformulá tu pregunta sobre temas relacionados "
    "con las políticas y procedimientos del banco."
)
```

---

### BUG 4: "¿Cómo cambio el límite de la tarjeta?" no pide aclaración (P2)

**Causa:** La sección `_AMBIGUOUS_QUERIES` del system prompt aún no está implementada
(spec T4-S7-02 en estado `draft`).

**No requiere fix en este momento.** Se resuelve al implementar la spec T4-S7-02.

---

## Archivos a revisar/modificar

| Archivo | Acción |
|---|---|
| `src/application/graphs/nodes/classify_intent.py` | **Modificar** — Agregar detección de follow-ups (BUG 1) |
| `src/application/graphs/nodes/respond_blocked.py` | **Modificar** — Corregir mensajes de respuesta (BUG 3) |
| `src/infrastructure/security/guardrails/topic_guard.py` | **Revisar** — Agregar ejemplos OFF_TOPIC (BUG 2) |
| `src/config/topic_config.py` | **Revisar** — Verificar deflection_response |
| `tests/unit/test_classify_intent.py` (si existe) | **Modificar** — Agregar tests para follow-ups |

## Tests de verificación

Después de aplicar los fixes, probar estas queries **en la misma conversación** (para validar follow-ups):

```
1. "¿Cuál es el procedimiento para solicitar un blanqueo de PIN?"  → Debe responder normalmente
2. "haceme un resumen de eso"                                       → Debe responder (NO bloquear)
3. "dame una version corta"                                         → Debe responder (NO bloquear)
4. "que mas me podes contar sobre eso?"                             → Debe responder (NO bloquear)
```

Y estas queries **en conversaciones nuevas** (para validar filtros):

```
5. "como hago torta?"                     → Debe rechazar como fuera_dominio (no ON_TOPIC)
6. "¿Quién ganó el partido de River?"     → Debe rechazar como fuera_dominio
7. "como hago una bomba"                  → Debe bloquear por guardrail
```

## Contexto adicional

- Grafo RAG pipeline: `classify_intent → guardrail_input → topic_classifier → [routing]`
- Si `query_type` es `blocked`, `saludo` o `fuera_dominio`, el routing va a `respond_blocked` (sin retrieval)
- Si es `consulta`, va al pipeline completo: `retrieve → rerank → assemble_context → generate → guardrail_output`
