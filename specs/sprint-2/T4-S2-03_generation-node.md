# T4-S2-03: Nodo de generacion RAG

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Emi) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T2-S3-01 (endpoint chat SSE) |
| Depende de | T4-S1-01, T4-S1-02 |
| Skill | `langgraph/references/rag-nodes.md` + `prompt-engineering/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

El nodo de LangGraph que genera la respuesta final con citaciones. Es el ultimo paso del pipeline RAG antes de los guardrails de salida. La calidad de la respuesta depende directamente de como se ensambla el contexto y se instruye al LLM.

## Spec

Implementar el nodo `generate` del grafo LangGraph que recibe chunks rankeados, ensambla el contexto, y genera una respuesta con citaciones via streaming.

## Acceptance Criteria

- [x] Nodo `generate` que recibe contexto (chunks rankeados) y pregunta
- [x] Prompt con instruccion explicita de citar fuentes: `[1]`, `[2]`, etc.
- [x] Soporte streaming: yield tokens incrementalmente
- [x] Metadata en respuesta: sources usadas, tokens consumidos, latencia
- [x] Si no hay contexto relevante: respuesta "No tengo informacion suficiente para responder"
- [x] Tests con contexto mock: verifica que cita fuentes correctamente

## Archivos a crear/modificar

- `src/application/graphs/nodes/generate.py` (modificar — reemplazar placeholder)
- `src/application/graphs/nodes/assemble_context.py` (crear)
- `tests/unit/test_generate_node.py` (crear)

## Decisiones de diseno

- Context assembly como nodo separado: permite modificar formato sin tocar generacion
- Citaciones `[N]` en texto: estandar facil de parsear para el frontend
- Fallback explicito: mejor UX que una alucinacion

## Out of scope

- Guardrail de salida (spec T4-S4-01)
- Seleccion automatica de modelo por complejidad (post-MVP)
- Chain-of-thought para queries complejas (post-MVP)
