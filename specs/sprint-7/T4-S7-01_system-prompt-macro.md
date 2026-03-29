# T4-S7-01: Incorporar lineamientos UX Macro en el System Prompt

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Prompt Engineering / LLM) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | N/A |
| Depende de | T4-S1-02 (System Prompt inicial) |
| Skill | `prompt-engineering/SKILL.md` |
| Estimacion | M (4-6h) |

## Contexto

El equipo de UX de Banco Macro ha provisto una guía detallada de "Directivas para Límites y Restricciones" (Pampa IA, Versión 1.0). Estas directivas incluyen elementos cross-plataforma (límites obligatorios, contextuales y fuera de límite), así como lineamientos específicos para flujos (tarjetas, información bancaria, pagos, etc.) y reglas estrictas de formato para fechas, horas y monedas. 
Actualmente, el sistema usa un prompt base (definido en `src/infrastructure/llm/prompts/system_prompt.py`), el cual debe ser expandido y ajustado para incorporar y respetar todas estas directivas.

## Spec

Actualizar `src/infrastructure/llm/prompts/system_prompt.py` para incluir las restricciones de UX Macro. 
**Regla crítica:** Se debe tener especial cuidado de **no romper las 6 secciones existentes** (Identidad, Reglas, Formato, Citaciones, Restricciones y Fallback) y mantener estricto el sistema de citaciones del RAG.

1.  **Límites Obligatorios y Fuera de Límite:** 
    *   Añadir a la sección `_RESTRICTIONS` o crear una nueva subsección `_UX_GUIDELINES` para forzar que el modelo no hable de inversiones, competencia, política, religión, etc.
    *   Forzar que no invente valores ni asuma datos de contexto no entregados por el usuario.
2.  **Formatos:** 
    *   Incorporar de manera clara a `_RESPONSE_FORMAT` los lineamientos sobre:
        *   **Fechas:** dd/mm/aaaa, dd/MMM/aa, o "d de [mes] de aaaa".
        *   **Moneda:** USD 650, $ 5.000 (con espacio luego del signo, coma para decimales).
        *   **Horas:** Formato 24h con " h" (ej: 8 h, 17:30 h).
3.  **Identidad/Rol:** 
    *   Refinar `_IDENTITY` para que refleje la regla de UX: saludar con el nombre completo sin apellido (si estuviera en el historial o contexto) y no inventar un nombre si no está registrado.
    *   Adoptar la política de identificarse siempre como asistente/bot y no simular ser un humano.

## Acceptance Criteria

- [x] Se guardan los lineamientos originales de UX en `docs/prompts/system-prompt-ux-macro.md` como referencia y fuente de verdad.
- [x] Se actualiza `src/infrastructure/llm/prompts/system_prompt.py` incorporando todas las reglas de negocio, limites y formatos de UX Macro.
- [x] La actualizacion del prompt no sobrepasa el limite razonable de tokens y no diluye las instrucciones criticas de RAG (citaciones y prevencion de alucinacion).
- [x] Se anaden/modifican tests en `tests/unit/test_prompts.py` (o similar) para verificar el ensamblado correcto de las nuevas secciones en el prompt final.
- [x] No se rompen los flujos de RAG existentes; las respuestas siguen usando los documentos recuperados de forma exclusiva.
- [x] Las memorias episódicas recuperadas en `retrieve_node` se inyectan efectivamente en el prompt vía `build_rag_prompt(user_memories=...)` en `stream_response.py`.

## Spec Alignment
- **IMPLEMENTADO**: Se creó/guardó la referencia `docs/prompts/system-prompt-ux-macro.md`.
- **IMPLEMENTADO**: Modificado `system_prompt.py` añadiendo reglas estrictas sobre saludos, identificación de bot, formato de fechas, moneda y temas fuera del límite (inversiones, competencia, política).
- **IMPLEMENTADO**: Modificado `test_prompts.py` cubriendo cada una de las nuevas adiciones de UX para el system prompt. Las pruebas pasan al 100%. Mantenimiento del tono RAG intacto.
- **IMPLEMENTADO**: Se respeta estructura del prompt, no se diluyen instrucciones anti-hallucination.
- **IMPLEMENTADO (bugfix)**: Corregida la inyección de memorias episódicas en `stream_response.py`. Las memorias recuperadas por `retrieve_node` ahora se formatean con `format_user_memories()` (respetando `memory_max_chars`) y se pasan a `build_rag_prompt(user_memories=...)` para inyección en el bloque `<user_memories>` del prompt. Tests añadidos para verificar inyección y omisión correcta.

## Archivos a crear/modificar

- `docs/prompts/system-prompt-ux-macro.md` (crear)
- `src/infrastructure/llm/prompts/system_prompt.py` (modificar)
- `src/application/use_cases/rag/stream_response.py` (modificar — inyección de memorias en prompt)
- `tests/unit/test_prompts.py` (modificar)

## Notas de Implementación

Al implementar, se debe tener sumo cuidado de que el prompt no sufra del fenómeno *"lost in the middle"* por volverse excesivamente largo. Se sugiere sintetizar las reglas de UX Macro y enfocarse en las que aplican exclusivamente a la **generación de texto** (formatos, tono, temas prohibidos). 
Es importante entender que reglas de UX como "confirmar acciones con botonera previamente" son responsabilidades de orquestación en el Frontend / LangGraph, y el rol del prompt aquí es simplemente *no ofrecer o dar por confirmadas esas acciones textualmente* sin delegar a la UI.