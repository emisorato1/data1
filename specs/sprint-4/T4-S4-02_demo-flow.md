# T4-S4-02: Demo flow completo + edge cases

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Emi, Lautaro) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | Demo MVP |
| Depende de | T4-S3-02, T3-S4-01, T4-S4-01 |
| Skill | `langgraph/SKILL.md` + `langgraph/references/anti-patterns.md` |
| Estimacion | L (4-8h) |

## Contexto

Pulir el flujo para demo: manejar edge cases y mejorar UX. Esta es la ultima spec antes de la demo. Todo debe funcionar de forma fluida con el dataset de demo cargado.

## Spec

Validar y pulir el flujo completo para los escenarios de demo, manejar edge cases gracefully, y documentar los escenarios de demo con queries y respuestas esperadas.

## Acceptance Criteria

- [ ] Query sin documentos relevantes -> respuesta graceful ("No tengo informacion...")
- [ ] Query fuera de dominio bancario -> respuesta adecuada
- [ ] Conversacion multi-turno funcional (el contexto se mantiene)
- [ ] Citaciones correctas y verificables
- [ ] Latencia E2E < 3 segundos (p95) para queries tipicas
- [ ] 5 escenarios de demo documentados con queries y respuestas esperadas

## Archivos a crear/modificar

- `docs/demo-scenarios.md` (crear)
- Ajustes en nodos del grafo segun sea necesario

## Decisiones de diseno

- 5 escenarios curados: cubren los casos mas comunes y demuestran las capacidades clave
- Latencia 3s target: ajuste desde 5s de Sprint 3 con datos reales y tuning

## Out of scope

- Demo automatizada/scripted (se hace manual)
- Load testing (post-MVP)
- Soporte multi-idioma (post-MVP)
