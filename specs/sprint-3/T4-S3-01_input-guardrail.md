# T4-S3-01: Guardrail de entrada (input validation)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Lautaro) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T4-S3-02 (integracion E2E) |
| Depende de | T4-S1-01 |
| Skill | `guardrails/SKILL.md` + `prompt-engineering/references/prompt-injection-defense.md` |
| Estimacion | L (4-8h) |

## Contexto

Primera capa de seguridad IA: validar la pregunta del usuario antes de procesarla. Esencial para prevenir prompt injection y jailbreak attempts que podrian hacer que el sistema revele informacion sensible o actue fuera de su dominio.

## Spec

Implementar nodo `guardrail_input` en el grafo LangGraph que detecte prompt injection, jailbreak, y valide longitud antes de pasar la query al pipeline de retrieval.

## Acceptance Criteria

- [x] Nodo `guardrail_input` en el grafo LangGraph (antes de retrieve)
- [x] Deteccion de prompt injection basica (patron matching + LLM classifier)
- [x] Deteccion de jailbreak attempts
- [x] Validacion de longitud (max 2000 caracteres)
- [x] Si se detecta amenaza: corto-circuito con mensaje seguro predefinido
- [x] Logging de intentos bloqueados en Langfuse (para analisis posterior)
- [x] Tests con ejemplos conocidos de prompt injection

## Archivos a crear/modificar

- `src/application/graphs/nodes/validate_input.py` (crear — reemplazar placeholder)
- `src/infrastructure/security/guardrails/input_validator.py` (crear)
- `tests/security/test_input_guardrail.py` (crear)
- `tests/fixtures/prompt_injection_examples.json` (crear)

## Decisiones de diseno

- Doble capa (pattern + LLM): patterns son rapidos pero evadibles, LLM es mas robusto pero costoso
- LLM classifier con Gemini Flash Lite: ultra-baja latencia, costo minimo
- Corto-circuito (no excepcion): el usuario recibe respuesta amable, no un error

## Out of scope

- Guardrail de salida (spec T4-S4-01)
- PII detection en input (post-MVP)
- Rate limiting por tipo de query (post-MVP)
- Adversarial testing completo (post-MVP, spec POST-27)
