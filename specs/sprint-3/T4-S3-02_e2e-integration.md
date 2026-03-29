# T4-S3-02: Integracion E2E del grafo RAG

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Emi) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T4-S4-02 (demo flow) |
| Depende de | T4-S2-01, T4-S2-02, T4-S2-03 |
| Skill | `langgraph/SKILL.md` + `langgraph/references/conditional-routing.md` |
| Estimacion | L (4-8h) |

## Contexto

Conectar todos los nodos del grafo y verificar el flujo completo. Hasta ahora cada nodo se desarrollo por separado; esta spec los integra y valida que el pipeline E2E funcione con datos reales.

## Spec

Integrar todos los nodos en el grafo LangGraph, verificar streaming E2E, persistencia con PostgresSaver, y latencia dentro de targets.

## Acceptance Criteria

- [ ] Grafo completo: `guardrail_input` -> `classify_intent` -> `retrieve` -> `rerank` -> `generate`
- [ ] Streaming funcional de extremo a extremo
- [ ] Checkpointer PostgresSaver persiste estado entre invocaciones
- [ ] Reactivar conversacion: cargar thread_id existente y continuar
- [ ] Latencia E2E < 5 segundos para query tipica (con documentos indexados)
- [ ] Test E2E: indexar documento -> preguntar -> verificar respuesta cita el documento

## Archivos a crear/modificar

- `src/application/graphs/rag_graph.py` (modificar — conectar todos los nodos reales)
- `tests/e2e/test_rag_pipeline.py` (crear)

## Decisiones de diseno

- Test E2E con documento real indexado: valida todo el pipeline, no solo mocks
- PostgresSaver sobre MemorySaver en test: misma config que produccion
- Latencia 5s como target Sprint 3: se ajusta a 3s en Sprint 4 con tuning

## Out of scope

- Guardrail de salida (spec T4-S4-01)
- Memoria episodica (post-MVP)
- Multi-turno avanzado (se valida basico aqui, avanzado en Sprint 4)
