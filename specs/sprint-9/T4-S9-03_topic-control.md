# T4-S9-03: Topic control (solo dominio bancario)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Emi) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T6-S10-02 |
| Depende de | T4-S3-01 (done) |
| Skill | `guardrails/SKILL.md` + `prompt-engineering/SKILL.md` |
| Estimacion | M (2-4h) |

## Contexto

Banking assistant should only answer questions related to its domain (CAT procedures, RRHH policies, banking products). Off-topic queries must be deflected politely.

## Spec

Implement topic classification guardrail that detects off-topic queries and provides domain-appropriate deflection.

## Acceptance Criteria

- [x] Nodo `topic_classifier` en grafo LangGraph (post-input-guardrail, pre-retrieve)
- [x] Clasificacion: on-topic (banking), off-topic, ambiguous
- [x] Gemini Flash para clasificacion con few-shot examples
- [x] Lista configurable de topicos permitidos y prohibidos
- [x] On-topic: continua pipeline
- [x] Off-topic: corto-circuito con respuesta amable
- [x] Ambiguous: continua con flag para logging
- [x] Tests con queries on-topic, off-topic y ambiguas

## Archivos a crear/modificar

- `src/application/graphs/nodes/topic_classifier.py` (crear)
- `src/infrastructure/security/guardrails/topic_guard.py` (crear)
- `src/config/topic_config.py` (crear)
- `tests/security/test_topic_control.py` (crear)

## Decisiones de diseno

- **LLM classifier sobre keyword matching**: Entiende contexto.
- **Few-shot prompt**: Ejemplos del dominio bancario mejoran precision.
- **Configurable**: Ajustar sin codigo.

## Out of scope

- Multi-domain support
- Topic routing
