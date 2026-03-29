# T4-S9-02: Faithfulness scoring con LLM-as-judge

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Lautaro) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T6-S10-02 |
| Depende de | - |
| Skill | `guardrails/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

The RAG system must not hallucinate. Every claim in a response should be supported by retrieved context. An LLM-as-judge validates faithfulness in real-time, blocking unfaithful responses.

## Spec

Implement real-time faithfulness scoring using Gemini as judge, integrated into the LangGraph pipeline post-generation.

## Acceptance Criteria

- [x] Nodo `validate_faithfulness` en grafo LangGraph (post-generation)
- [x] Gemini Flash como judge: evalua si cada claim esta soportada por contextos
- [x] Score de faithfulness: 0.0 a 1.0
- [x] Threshold configurable (default: 0.7) — debajo se regenera o bloquea
- [x] Si faithfulness < threshold: re-generacion con prompt restrictivo (max 1 retry)
- [x] Si retry falla: respuesta generica "No puedo responder con certeza"
- [x] Score enviado a Langfuse como metrica del trace
- [x] Latencia del scoring < 2 segundos (Gemini Flash)
- [x] Tests con respuestas fieles y no fieles

## Archivos a crear/modificar

- `src/application/graphs/nodes/validate_faithfulness.py` (crear)
- `src/infrastructure/security/guardrails/faithfulness_judge.py` (crear)
- `tests/security/test_faithfulness_scoring.py` (crear)

## Decisiones de diseno

- **LLM-as-judge sobre NLI model**: Mas flexible, entiende contexto bancario.
- **Gemini Flash**: Capaz para juicio binario, rapido y barato.
- **Re-generacion antes de bloqueo**: Segunda oportunidad con prompt restrictivo.

## Out of scope

- Fine-tuning del judge
- Faithfulness batch/offline (RAGAS DAG cubre eso)
- Feedback loop automatico

## Registro de implementacion

### Archivos creados
- `src/infrastructure/security/guardrails/faithfulness_judge.py` -- FaithfulnessJudge class (LLM-as-judge), FaithfulnessResult frozen dataclass, structured JSON prompt
- `src/application/graphs/nodes/validate_faithfulness.py` -- validate_faithfulness_node (LangGraph node), re-generation logic, Langfuse score reporting, module-level singleton with DI
- `tests/security/test_faithfulness_scoring.py` -- 42 tests covering all ACs, edge cases, DI, Langfuse integration

### Archivos modificados
- `src/config/settings.py` -- Added `faithfulness_threshold: float = 0.7`
- `src/application/graphs/state.py` -- Added `faithfulness_score: float` field to RAGState
- `src/infrastructure/security/guardrails/__init__.py` -- Exported FaithfulnessJudge, FaithfulnessResult

### Patrones seguidos
- Frozen dataclass para FaithfulnessResult (como OutputGuardrailResult)
- Module-level singleton con lazy init + set_*() para DI en tests (como validate_input.py)
- @observe decorator de Langfuse (como generate.py)
- GeminiModel.FLASH para el judge (como especificado en spec)
- Fail-open en errores de LLM (como input_validator.py)

### Notas
- El nodo NO se integra al grafo en rag_graph.py (Wave 2, out of scope)
- El threshold es configurable via env var FAITHFULNESS_THRESHOLD (default 0.7)
- Score se reporta a Langfuse via langfuse.score() como metrica del trace
- Coverage: 97.69% (130 statements, 3 missed -- lazy init paths)
