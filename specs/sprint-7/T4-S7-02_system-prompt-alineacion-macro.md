# T4-S7-02: Alineación del System Prompt interno con directivas Macro

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Prompt Engineering / LLM) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T6-S7-01 (testing interno) |
| Depende de | T4-S7-01 (system prompt macro — done) |
| Skill | `prompt-engineering/SKILL.md` |
| Estimacion | M (4-6h) |

## Contexto

La spec T4-S7-01 incorporó las directivas base de UX Macro (`system-prompt-ux-macro.md`), pero el prompt actual (`system_prompt.py`) quedó con gaps respecto al **system prompt macro genérico** provisto por el banco (`docs/prompts/system-prompt-macro.md`).

El macro está diseñado para **clientes externos + usuarios internos**, mientras que nuestro sistema es exclusivamente para **empleados internos del banco**. Esto significa que no todo aplica, pero hay patrones de calidad conversacional que debemos incorporar para lograr una experiencia profesional comparable a la de un asistente Gemini Pro.

### Gaps identificados (análisis completo en `analisis_alineacion_prompts.md`):

1. **Identidad genérica** — El prompt dice "asistente virtual experto del banco" sin propósito claro para empleados
2. **Sin estilo adaptivo** — Solo dice "tono profesional", el macro define 3 registros según situación
3. **Sin reglas de cierre** — Se ofrece "¿algo más?" incluso cuando no se resolvió la consulta
4. **Sin manejo de consultas ambiguas** — No hay protocolo para pedir aclaración con opciones concretas
5. **Fallback frío** — Mensaje mecánico sin empatía
6. **Sin regla de frustración** — No se detecta ni se maneja al usuario frustrado

### Lo que NO se debe copiar del macro:

| Elemento del macro | Razón |
|---|---|
| Nombre "Eme" | Identidad del chatbot para clientes |
| Emojis | Para empleados internos, no aplica |
| `activate_menu` | Específico de la plataforma de clientes |
| Verificación DNI | Solo para clientes no autenticados |
| "No sos asistente de redacción" | Empleados podrían necesitar resumir procedimientos |
| Derivar a "canales oficiales" | Los empleados YA están dentro del banco |
| Saludos con template Jinja | Nuestro sistema maneja el saludo de forma diferente |

## Spec

Refactorizar `system_prompt.py` para incorporar las directivas del macro que aplican a usuarios internos (empleados), elevando la calidad conversacional a nivel profesional sin romper las secciones existentes de seguridad y RAG.

**Principio guía:** El chat debe sentirse como hablar con un asistente Gemini Pro especializado — respuestas naturales, adaptivas al contexto emocional, con cierre inteligente y manejo elegante de la ambigüedad.

### 1. Identidad clara para empleados (refactorizar `_IDENTITY`)

Reescribir `_IDENTITY` para que refleje:
- Rol específico: asistente interno para **empleados** de Banco Macro
- Propósito: documentación interna, procedimientos, políticas, normativas
- Si el contexto incluye el nombre del usuario: saludar con nombre (sin apellido)
- Auto-identificación explícita como bot
- **NO** usar nombre propio ("Eme" es para clientes)

### 2. Estilo y trato adaptivo (nueva sección `_STYLE`)

Crear una nueva sección `_STYLE` con 3 registros de tono:

| Contexto | Tono |
|---|---|
| Consultas operativas / procedimientos | Claro, directo, eficiente |
| Dudas complejas / normativas | Detallado, paciente, preciso |
| Temas regulatorios / compliance | Formal, riguroso, respetuoso |

Incluir regla de frustración: si el usuario muestra frustración (≥2 intentos fallidos), sugerir contactar al área correspondiente de forma empática.

### 3. Reglas de cierre de mensajes (nueva sección `_MESSAGE_CLOSING`)

Crear sección `_MESSAGE_CLOSING` con lógica condicional:
- **SÍ** ofrecer más ayuda cuando se dio una respuesta útil o se resolvió la consulta
- **NO** ofrecer más ayuda cuando:
  - Se informó que no se puede ayudar
  - Se pidieron aclaraciones
  - Se derivó a otra área

### 4. Manejo de consultas ambiguas (nueva sección `_AMBIGUOUS_QUERIES`)

Crear sección `_AMBIGUOUS_QUERIES`:
- No asumir información ni adivinar contexto
- Identificar qué dato clave falta
- Hacer entre 1 y 3 preguntas claras
- Ofrecer opciones concretas cuando sea posible
- Incluir ejemplo contextualizado al dominio bancario interno

### 5. Fallback más natural (ajustar `_FALLBACK` y `RAG_FALLBACK_MESSAGE`)

Ajustar el tono del fallback:
```diff
- "No tengo informacion suficiente en la documentacion disponible
-  para responder esta consulta. Te sugiero contactar al area correspondiente."
+ "No encontre informacion suficiente en la documentacion disponible
+  para responder esta consulta. Te sugiero contactar al area
+  correspondiente para obtener una respuesta precisa."
```

### 6. Ensamblado y orden en `SYSTEM_PROMPT_RAG`

Agregar las nuevas secciones al ensamblado en un orden lógico:
```
ROL (_IDENTITY)
REGLAS (_BEHAVIOR_RULES)
ESTILO (_STYLE)                    ← NUEVO
FORMATO (_RESPONSE_FORMAT)
CITACIONES (_CITATIONS)
RESTRICCIONES (_RESTRICTIONS)
CONSULTAS AMBIGUAS (_AMBIGUOUS_QUERIES)  ← NUEVO
FALLBACK (_FALLBACK)
CIERRE DE MENSAJES (_MESSAGE_CLOSING)    ← NUEVO
ANTI-INJECTION (_ANTI_INJECTION)
TOKEN SMUGGLING (_TOKEN_SMUGGLING)
CONFIG PROTECTION (_CONFIG_PROTECTION)
LONG TEXT (_LONG_TEXT_HANDLING)
IDIOMA (_LANGUAGE)
MULTI-REQUEST (_MULTI_REQUEST)
```

## Acceptance Criteria

- [ ] `_IDENTITY` reescrito con identidad clara de asistente para empleados internos de Banco Macro.
- [ ] Nueva sección `_STYLE` con 3 registros de tono adaptivo + regla de frustración.
- [ ] Nueva sección `_MESSAGE_CLOSING` con lógica condicional de cierre.
- [ ] Nueva sección `_AMBIGUOUS_QUERIES` con protocolo de desambiguación.
- [ ] `RAG_FALLBACK_MESSAGE` y `_FALLBACK` actualizados con tono más natural.
- [ ] `SYSTEM_PROMPT_RAG` ensamblado con las 15 secciones en orden correcto.
- [ ] Tests existentes en `test_prompts.py` para secciones 2-5 y 7-12 siguen pasando sin cambios. Tests de secciones 1 y 6 se actualizan acorde a los cambios del spec.
- [ ] Nuevos tests para las secciones `_STYLE`, `_MESSAGE_CLOSING` y `_AMBIGUOUS_QUERIES`.
- [ ] El prompt ensamblado no supera un tamaño razonable (~4000 palabras máximo) para evitar "lost in the middle".
- [ ] Las instrucciones de citaciones RAG y anti-alucinación siguen intactas y priorizadas.

## Archivos a crear/modificar

| Archivo | Acción |
|---|---|
| `src/infrastructure/llm/prompts/system_prompt.py` | Modificar |
| `tests/unit/test_prompts.py` | Modificar (agregar tests nuevas secciones) |

## Verificación

### Tests automatizados

```bash
# Ejecutar tests unitarios del prompt
uv run pytest tests/unit/test_prompts.py -v

# Ejecutar con coverage para verificar que cubren las nuevas secciones
uv run pytest tests/unit/test_prompts.py -v --cov=src.infrastructure.llm.prompts --cov-report=term-missing
```

### Verificación manual

1. Inspeccionar el prompt ensamblado completo imprimiendo `SYSTEM_PROMPT_RAG` y verificar:
   - Orden de secciones correcto (15 secciones)
   - No hay secciones duplicadas
   - No se cortaron secciones existentes
2. Contar palabras del prompt ensamblado para validar que no supera ~4000 palabras
3. Buscar las keywords clave en el prompt: "empleados", "operativas", "ambigua", "cierre", "frustración"

### Prueba funcional (post-implementación, con el sistema corriendo)

Probar el chat con estos escenarios:
- **Consulta operativa:** "¿Cuál es el procedimiento para aprobar un crédito?" → Respuesta directa, eficiente
- **Consulta ambigua:** "¿Cómo proceso esto?" → Debe pedir aclaración con opciones
- **Fuera de scope:** "¿Quién ganó el partido ayer?" → Rechazo SIN "¿algo más?"
- **Fallback:** Consulta sobre algo no documentado → Mensaje natural, no robótico

## Out of scope

- Cambiar el nombre del bot (no se usa nombre propio para el chat interno)
- Agregar emojis (el macro los usa para clientes, no aplica para empleados)
- Modificar `build_rag_prompt()` ni los delimitadores XML
- Cambios en el frontend o en el flujo LangGraph
- Template de saludo con Jinja (se maneja en otro componente)
- Integración con `activate_menu` u otras funciones de UI del macro

## Notas de implementación

- **Lost in the middle:** Mantener las secciones de seguridad (anti-injection, token smuggling) y RAG (citaciones, anti-alucinación) en posiciones prominentes del prompt. Las nuevas secciones de UX van en el medio.
- **Consistencia de voseo:** El macro usa voseo argentino ("actuás", "brindás"). Nuestro prompt actual usa "tú" formal. **Decisión: mantener el estilo actual** (sin voseo) ya que el sistema usa "tú" consistentemente.
- **Docstring del módulo:** Actualizar el docstring del archivo para reflejar las 15 secciones (actualmente documenta 12).

## Registro de Implementacion
**Fecha**: 2026-03-19 | **Rama**: 52-T4-S7-02_system-prompt-alineacion-macro

| Archivo | Accion | Motivo |
|---------|--------|--------|
| `src/infrastructure/llm/prompts/system_prompt.py` | Modificado | AC 1-6: nueva identidad empleados, 3 secciones nuevas (_STYLE, _AMBIGUOUS_QUERIES, _MESSAGE_CLOSING), fallback natural, ensamblado 15 secciones |
| `tests/unit/test_prompts.py` | Modificado | AC 7-8: tests actualizados secciones 1/6, 7 tests nuevos para secciones 3/7/9, validacion de orden y word count |
| `specs/sprint-7/T4-S7-02_system-prompt-alineacion-macro.md` | Modificado | Correccion AC7 (inconsistencia secciones 1/6 vs "no se rompen 1-12"), cierre spec |

### Notas de Implementacion
- **AC7 corregido en spec**: El AC original decia "no se rompen secciones 1-12" pero las secciones 1 (_IDENTITY) y 6 (_FALLBACK) se modifican explicitamente en ACs 1 y 5. Se corrigio a "secciones 2-5 y 7-12 siguen pasando sin cambios".
- **Renumeracion de secciones**: Las secciones existentes 7-12 se renumeraron a 10-15 para acomodar las 3 nuevas (3, 7, 9). Los tests se actualizaron con la nueva numeracion.
- **Consistencia de tono**: Nuevas secciones usan tuteo consistente con el prompt existente, sin voseo.
- **Word count**: 1532 palabras (38% del limite de 4000), sin riesgo de "lost in the middle".
- **Tests adicionales**: Se agregaron `test_identity_no_name_eme`, `test_no_emojis_in_prompt`, `test_sections_order`, `test_prompt_word_count_within_limit` como validaciones extra del spec.
