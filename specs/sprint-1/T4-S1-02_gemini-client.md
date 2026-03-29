# T4-S1-02: Gemini client wrapper y prompt templates

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Emi, Lautaro) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T4-S2-03 (generacion), T3-S2-01 (embeddings) |
| Depende de | T1-S1-02 |
| Skill | `prompt-engineering/SKILL.md` + `prompt-engineering/references/few-shot-banking.md` |
| Estimacion | L (4-8h) |

## Contexto

Client unificado para interactuar con Google Vertex AI (Gemini). Centraliza configuracion, retry logic y prompts del sistema. Todos los componentes que usen LLM deben pasar por este wrapper — no se permite instanciar clientes Gemini directamente.

## Spec

Implementar un wrapper para Vertex AI Gemini que soporte generacion (con streaming) y embeddings, junto con los templates de system prompt bancario.

## Acceptance Criteria

- [x] Wrapper en `src/infrastructure/llm/client.py`:
  - Soporte Gemini 2.0 Flash (consultas complejas)
  - Soporte Gemini 2.0 Flash Lite (consultas simples, guardrails)
  - Modelo seleccionable via parametro
- [x] Soporte para streaming: `async def generate_stream(prompt, **kwargs) -> AsyncIterator[str]`
- [x] Soporte para generacion sincrona: `async def generate(prompt, **kwargs) -> str`
- [x] Soporte para embeddings: `async def embed(texts: list[str], task_type: str) -> list[list[float]]`
  - task_type: `RETRIEVAL_DOCUMENT` o `RETRIEVAL_QUERY`
- [x] Configuracion parametrizable: temperature, max_tokens, safety_settings
- [x] Retry con backoff exponencial para errores transitorios de API (429, 500, 503)
- [x] System prompt bancario en `src/infrastructure/llm/prompts/system_prompt.py` con 6 secciones:
  1. Identidad del asistente
  2. Reglas de comportamiento
  3. Formato de respuesta
  4. Reglas de citacion (`[Fuente N]`)
  5. Restricciones (que NO hacer)
  6. Fallback (sin informacion suficiente)
- [x] Template few-shot con 2-3 ejemplos bancarios en `src/infrastructure/llm/prompts/templates/few_shot.py`
- [x] Tests con mock de Vertex AI

## Archivos a crear/modificar

- `src/infrastructure/llm/client.py` (crear)
- `src/infrastructure/llm/prompts/system_prompt.py` (crear)
- `src/infrastructure/llm/prompts/templates/few_shot.py` (crear)
- `src/infrastructure/llm/prompts/templates/zero_shot.py` (crear)
- `src/infrastructure/llm/__init__.py` (modificar — exports)
- `tests/unit/test_llm_client.py` (crear)
- `tests/unit/test_prompts.py` (crear)

## Decisiones de diseno

- Wrapper propio sobre usar LangChain ChatVertexAI directamente: mas control sobre retry, streaming, metricas
- Ecosistema Google unificado: PROHIBIDO OpenAI y Cohere (decision de arquitectura ADR-008)
- System prompt en Python (no en archivos .txt): permite interpolacion de variables y versionado con tipo

## Out of scope

- Integracion con LangGraph (spec T4-S2-03)
- Cache semantico de queries (post-MVP)
- Seleccion automatica de modelo por complejidad de query (se agrega en Sprint 2)
- Cost tracking por query (spec T1-S2-03)
