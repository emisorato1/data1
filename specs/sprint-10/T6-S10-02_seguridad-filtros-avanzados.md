# IA-26: Seguridad pre-produccion — filtros avanzados

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Emi, Lautaro) |
| Prioridad | Critica |
| Estado | pending |
| Bloqueante para | T6-S10-04 |
| Depende de | T4-S9-01, T4-S9-02, T4-S9-03 |
| Skill | `guardrails/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

Advanced guardrails (PII detection, faithfulness scoring, topic control) were implemented in Sprint 9. Before production, they need to be validated as a complete security layer with production-like scenarios.

## Spec

Validate the complete guardrail chain (input + output) with production-like scenarios, verify PII detection accuracy, faithfulness thresholds, and topic control effectiveness.

## Acceptance Criteria

- [ ] PII detection validado con 50+ escenarios (mix de PII real y false positives)
- [ ] Faithfulness scoring calibrado: threshold final aprobado por equipo
- [ ] Topic control validado con queries bancarias y off-topic
- [ ] Guardrail chain completa testeada E2E: input -> topic -> retrieve -> generate -> faithfulness -> PII -> response
- [ ] False positive rate < 5% para PII detection
- [ ] False positive rate < 10% para topic control
- [ ] Reporte de seguridad filtros con resultados y recomendaciones

## Archivos a crear/modificar

- `docs/security/guardrails-validation-report.md` (crear)

## Decisiones de diseno

- **E2E chain testing**: Los guardrails deben funcionar en conjunto, no solo individualmente.
- **Threshold calibration**: Los defaults pueden no ser optimos para datos reales.

## Out of scope

- Adversarial red-teaming, ML model fine-tuning
