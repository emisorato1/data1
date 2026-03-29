# T4-S1-01: LangGraph state machine design

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Emi, Lautaro) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T4-S2-03, T4-S3-02 |
| Depende de | T1-S1-02 |
| Skill | `langgraph/SKILL.md` + `langgraph/references/rag-nodes.md` |
| Estimacion | L (4-8h) |

## Contexto

El grafo LangGraph es el corazon del sistema RAG. Orquesta todo el flujo: clasificacion de intent -> retrieval -> reranking -> generacion -> guardrails. Disenar bien el state y los nodos en Sprint 1 evita refactors costosos despues.

## Spec

Disenar e implementar el esqueleto del grafo RAG con `RAGState`, nodos basicos y routing condicional. El grafo debe compilar y ser ejecutable con mocks.

## Acceptance Criteria

- [x] `RAGState` definido en `src/application/graphs/state.py` como TypedDict:
  ```python
  class RAGState(TypedDict):
      query: str
      query_type: str  # "saludo", "consulta", "fuera_dominio"
      query_embedding: list[float]
      messages: Annotated[list[BaseMessage], add_messages]
      retrieved_chunks: list[dict]
      reranked_chunks: list[dict]
      context_text: str
      response: str
      sources: list[dict]
      user_id: int
      permissions: list[str]
      guardrail_passed: bool
      retry_count: int
  ```
- [x] Grafo en `src/application/graphs/rag_graph.py` con funcion `build_rag_graph()`
- [x] Nodos basicos (skeleton, logica se completa en Sprint 2):
  - `classify_intent` -> determina tipo de query
  - `retrieve` -> placeholder que retorna chunks mock
  - `generate` -> placeholder que retorna respuesta mock
  - `guardrail_output` -> placeholder que pasa siempre
- [x] Routing condicional:
  - intent "saludo" -> directo a `generate` (sin retrieval)
  - intent "consulta" -> pasa por `retrieve`
  - intent "fuera_dominio" -> respuesta predefinida
- [x] `PostgresSaver` configurado como checkpointer (thread_id para persistencia de conversacion)
- [x] El grafo compila sin errores: `graph.compile()`
- [x] Test unitario que ejecuta el grafo con mocks en retrieve y generate

## Archivos a crear/modificar

- `src/application/graphs/state.py` (crear)
- `src/application/graphs/rag_graph.py` (crear)
- `src/application/graphs/nodes/classify_intent.py` (crear)
- `src/application/graphs/nodes/retrieve.py` (crear — placeholder)
- `src/application/graphs/nodes/generate.py` (crear — placeholder)
- `src/application/graphs/nodes/validate_output.py` (crear — placeholder)
- `src/application/graphs/nodes/respond_blocked.py` (crear)
- `tests/unit/test_rag_graph.py` (crear)

## Decisiones de diseno

- `add_messages` reducer para `messages`: permite append automatico sin reemplazar historial
- Nodos como funciones puras `(state: RAGState) -> dict`: facil de testear, sin side effects
- PostgresSaver sobre MemorySaver: persistencia real de conversaciones entre sesiones
- Routing basado en intent: evita queries costosas al LLM para saludos simples

## Out of scope

- Logica real de retrieval (spec T4-S2-01)
- Logica real de generacion (spec T4-S2-03)
- Reranking (spec T4-S2-02)
- Guardrail de entrada (spec T4-S3-01)
- Memoria episodica (post-MVP)
- Streaming (se agrega en Sprint 2-3)
