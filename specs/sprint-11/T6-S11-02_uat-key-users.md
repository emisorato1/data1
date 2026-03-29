# IA-30: UAT con key users y ajustes

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco, team) |
| Prioridad | Critica |
| Estado | pending |
| Bloqueante para | T6-S11-03, T6-S11-04 |
| Depende de | T6-S11-01 |
| Skill | - |
| Estimacion | L (4-8h) |

## Contexto

Key users (trained in Sprint 9) perform User Acceptance Testing on the production environment. Their feedback determines if the system is ready for go-live.

## Spec

Coordinate and execute UAT sessions with key users from CAT and RRHH, documenting findings and implementing critical adjustments.

## Acceptance Criteria

- [ ] Sesiones UAT con key users CAT (al menos 2 sesiones)
- [ ] Sesiones UAT con key users RRHH (al menos 2 sesiones)
- [ ] Key users ejecutan script de pruebas (de Sprint 9 T6-S9-02)
- [ ] Feedback documentado: observaciones, sugerencias, issues
- [ ] Issues criticos resueltos antes de go-live
- [ ] Observaciones no criticas documentadas para post-go-live
- [ ] Sign-off de key users en resultados UAT
- [ ] Reporte UAT formal

## Archivos a crear/modificar

- `docs/testing/uat-results.md` (crear)
- `docs/testing/uat-feedback.md` (crear)

## Decisiones de diseno

- **Produccion real**: UAT en el ambiente final, no en QAS.
- **Sign-off de key users**: Stakeholders del banco aprueban.

## Out of scope

- UAT con usuarios finales (eso es post go-live), cambios mayores de funcionalidad
