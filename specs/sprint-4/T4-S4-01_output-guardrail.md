# T4-S4-01: Guardrail de salida basico

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Lautaro) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T4-S4-02 (demo flow) |
| Depende de | T4-S3-02 |
| Skill | `guardrails/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

Validacion de la respuesta generada antes de enviarla al usuario. En el contexto bancario, es critico que el sistema no alucine datos financieros ni exponga informacion sensible como numeros de cuenta o documentos de identidad.

## Spec

Implementar nodo `guardrail_output` en el grafo que verifique faithfulness basica y detecte datos sensibles en la respuesta antes de enviarla al usuario.

## Acceptance Criteria

- [x] Nodo `guardrail_output` en el grafo (despues de generate)
- [x] Verificacion basica de faithfulness: la respuesta no contradice el contexto
- [x] Deteccion de datos sensibles en respuesta (numeros de cuenta, DNI/CUIT patterns)
- [x] Si guardrail bloquea: fallback message predefinido
- [x] Logging del resultado del guardrail en Langfuse
- [x] Tests con respuestas alucinadas vs fieles

## Archivos a crear/modificar

- `src/application/graphs/nodes/validate_output.py` (modificar — reemplazar placeholder)
- `src/infrastructure/security/guardrails/output_validator.py` (crear)
- `tests/security/test_output_guardrail.py` (crear)

## Decisiones de diseno

- Faithfulness basica con heuristica (no LLM-as-judge): latencia baja para MVP, se mejora post-MVP
- Regex para datos sensibles argentinos: DNI (XX.XXX.XXX), CUIT (XX-XXXXXXXX-X), CBU (22 digitos)
- Fallback message: "No puedo proporcionar esa informacion. Consulte con su oficial de cuenta."

## Out of scope

- LLM-as-judge para faithfulness (post-MVP, spec POST-15)
- PII detection avanzada con NER (post-MVP, spec POST-14)
- Topic control (post-MVP, spec POST-16)
