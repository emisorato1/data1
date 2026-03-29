# T4-S9-03b: System prompt hardening (seguridad y comportamiento)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Emi) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T6-S10-02 |
| Depende de | T4-S7-01 (done), T4-S9-03 (done — misma rama) |
| Skill | `prompt-engineering/SKILL.md` + `guardrails/SKILL.md` |
| Estimacion | M (2-4h) |
| Rama | `23-t4-s9-03-topic-control-solo-dominio-bancario` (misma que T4-S9-03) |

## Contexto

El system prompt actual (`system_prompt.py`) fue creado en T4-S1-02 y expandido en T4-S7-01 con reglas UX Macro (formatos, identidad, citaciones). Sin embargo, carece de defensas criticas de seguridad que si estan presentes en el documento de referencia UX Macro (`docs/prompts/system-prompt-macro.md`).

Esta spec es **bis** de T4-S9-03 (topic control) y se implementa en la misma rama. Actua como spec paraguas que:
1. Hardening del system prompt con reglas de seguridad faltantes.
2. Integracion verificada con el topic_classifier ya implementado.
3. Golden set de tests de comportamiento del agente.

**Fuente de verdad**: Las secciones "AHORA" de `docs/prompts/system-prompt-macro.md`, mergeadas con las reglas existentes de `system_prompt.py`. El prompt sigue orientado a **usuarios internos del banco** (empleados), no clientes finales.

## Gap Analysis

Elementos del `system-prompt-macro.md` ausentes en `system_prompt.py`:

| Gap | Seccion macro.md | Criticidad |
|-----|-------------------|------------|
| Anti-injection defense | PRIORIDAD Y SEGURIDAD GENERAL | Alta |
| Token/credential smuggling | TOKENS, CREDENCIALES Y TOKEN SMUGGLING | Alta |
| Config protection expandida | INFORMACION INTERNA Y CONFIGURACION | Media |
| Manejo de textos largos | TEXTOS LARGOS Y REDACCION | Media |
| Enforcement de idioma (solo espanol) | IDIOMA | Media |
| Manejo de multiples solicitudes | MULTIPLES SOLICITUDES EN UN MENSAJE | Media |

Elementos que **ya estan** y se mantienen intactos:
- Identidad de bot (seccion `_IDENTITY`)
- 6 secciones obligatorias del prompt RAG
- Citaciones `[N]`
- Formatos fecha/moneda/hora
- Restricciones tematicas base
- Fallback message
- XML delimiters y anti-injection en `build_rag_prompt()`

## Spec

Agregar nuevas secciones de seguridad al `system_prompt.py` sin romper la estructura existente de 6 secciones. Las nuevas reglas se anaden como secciones adicionales (`_ANTI_INJECTION`, `_TOKEN_SMUGGLING`, `_CONFIG_PROTECTION`, `_LONG_TEXT_HANDLING`, `_LANGUAGE`, `_MULTI_REQUEST`), ensambladas despues de las 6 originales.

### Reglas de adaptacion al contexto interno

- **Anti-injection**: Aplicar tal cual del macro.md — la defensa contra prompt injection es identica para interno y externo.
- **Token smuggling**: Bloqueo contextual. Bloquear si el usuario INCLUYE un token/credencial literal. Permitir preguntas SOBRE tokens si son sobre procedimientos documentados.
- **Config protection**: Expandir la regla 5 de `_BEHAVIOR_RULES` con handling especifico para preguntas sobre capacidades, memoria y arquitectura.
- **Textos largos**: Aplicar proteccion contra cost attack y context overflow.
- **Idioma**: Solo espanol. Interpretar otros idiomas pero responder siempre en espanol.
- **Multi-request**: Si credencial detectada, solo mensaje de seguridad. Si no, responder solo partes bancarias.

### Golden set de tests

Crear `tests/fixtures/system_prompt_golden_set.json` con pares (input, expected_behavior, category) para validacion. Categorias:

1. `on_topic` — Queries bancarias normales -> respuesta normal
2. `off_topic` — Queries fuera de dominio -> deflexion
3. `prompt_injection` — Intentos de cambiar comportamiento -> rechazo
4. `token_smuggling` — Mensajes con credenciales literales -> bloqueo
5. `token_question` — Preguntas sobre procedimientos de tokens -> permitido
6. `config_leak` — Pedir system prompt/configuracion -> negacion neutra
7. `many_shot` — Multiples ejemplos intentando reprogramar -> resistencia
8. `long_text` — Mensaje excesivamente largo -> pedir reformulacion
9. `language` — Pedido en otro idioma -> respuesta en espanol
10. `identity_change` — Intentar cambiar rol/nombre -> rechazo

## Acceptance Criteria

- [x] Seccion `_ANTI_INJECTION` agregada a `system_prompt.py` con reglas de prioridad de sistema, rechazo de cambio de rol, defensa many-shot
- [x] Seccion `_TOKEN_SMUGGLING` con bloqueo contextual (token literal = bloqueo; pregunta sobre token = permitido)
- [x] Seccion `_CONFIG_PROTECTION` expandida con handling de preguntas sobre capacidades, memoria, arquitectura
- [x] Seccion `_LONG_TEXT_HANDLING` con proteccion contra cost attack y context overflow
- [x] Seccion `_LANGUAGE` forzando respuestas solo en espanol
- [x] Seccion `_MULTI_REQUEST` con prioridad de seguridad para mensajes con multiples solicitudes
- [x] `SYSTEM_PROMPT_RAG` ensamblado con las nuevas secciones, sin romper las 6 originales
- [x] Tests unitarios en `test_prompts.py` verificando presencia de cada nueva seccion
- [x] Golden set en `tests/fixtures/system_prompt_golden_set.json` con minimo 30 pares (input, expected_behavior, category) cubriendo las 10 categorias
- [x] Tests en `tests/unit/test_prompt_golden_set.py` que cargan el golden set y verifican que el prompt contiene las reglas necesarias para cada categoria
- [x] Integracion verificada: el topic_classifier existente complementa (no duplica) las reglas del system prompt

## Archivos a crear/modificar

- `src/infrastructure/llm/prompts/system_prompt.py` (modificar — agregar secciones de seguridad)
- `tests/unit/test_prompts.py` (modificar — tests de nuevas secciones)
- `tests/fixtures/system_prompt_golden_set.json` (crear — golden set de comportamiento)
- `tests/unit/test_prompt_golden_set.py` (crear — tests que validan golden set contra prompt)

## Decisiones de diseno

- **Secciones aditivas, no destructivas**: Las 6 secciones originales se mantienen intactas. Las nuevas se anaden como secciones 7-12. Esto evita regresiones y mantiene backward compatibility.
- **Token smuggling contextual**: A diferencia del macro.md (bloqueo total ante keyword "token"), el prompt interno permite preguntas sobre procedimientos documentados que mencionen tokens. Solo bloquea cuando el mensaje incluye un token/credencial literal (patron regex-like).
- **Golden set como fixture JSON**: Permite validacion manual, CI con LLM judge futuro, y documenta el comportamiento esperado. No requiere llamadas LLM en CI — los tests verifican que el prompt tiene las reglas, el golden set documenta el resultado esperado.
- **Complementariedad con topic_classifier**: El topic_classifier (LLM, pre-retrieve) maneja deteccion off-topic con precision contextual. Las reglas del system prompt son la ultima linea de defensa si un query off-topic pasa el classifier.

## Relacion con specs pendientes

| Spec | Relacion |
|------|----------|
| T4-S9-01 PII detection output (pending) | Independiente. Nodo post-generation, no afecta system prompt. |
| T4-S9-02 Faithfulness scoring (pending) | Independiente. LLM-as-judge post-generation. |
| T4-S6-02 PII sanitize memories (done) | Verificar: acceptance criteria sin marcar. No afecta esta spec. |

## Out of scope

- Cambio de audiencia del prompt (sigue siendo interno)
- Identidad "Eme" del macro.md (es para cliente externo)
- Templates Jinja para user.data (es logica de frontend externo)
- Implementacion de LLM judge para evaluar golden set en CI (spec futura)
- Cambios al topic_classifier o topic_guard ya implementados

## Registro de Implementacion
**Fecha**: 2026-03-18 | **Rama**: 23-t4-s9-03-topic-control-solo-dominio-bancario

| Archivo | Accion | Motivo |
|---------|--------|--------|
| `src/infrastructure/llm/prompts/system_prompt.py` | Modificado | 6 secciones de seguridad (AC 1-7) |
| `tests/unit/test_prompts.py` | Modificado | 8 tests nuevos para secciones 7-12 (AC 8) |
| `tests/fixtures/system_prompt_golden_set.json` | Creado | 31 pares en 10 categorias (AC 9) |
| `tests/unit/test_prompt_golden_set.py` | Creado | 37 tests de golden set (AC 10) |
| `pyproject.toml` | Modificado | S105 per-file-ignore para prompt text |

### Notas de Implementacion
- Las secciones nuevas usan line continuations (`\`) para respetar el limite de 120 chars de ruff.
- El golden set tiene 31 entries (minimo spec: 30) cubriendo las 10 categorias.
- Coverage del modulo: 97% (1 linea no cubierta: branch de conversation_history vacio).
- 73 tests pasando (36 existentes + 37 nuevos). 0 regresiones.
