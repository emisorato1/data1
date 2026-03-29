# T6-S9-01: Pruebas QAS funcionales y no funcionales

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco, team) |
| Prioridad | Critica |
| Estado | pending |
| Bloqueante para | T6-S10-01 |
| Depende de | T6-S8-03 |
| Skill | `testing-strategy/SKILL.md` |
| Estimacion | XL (8+h) |

## Contexto

QAS environment provisioned. Formal QAS testing covers functional (all features), non-functional (performance, security), and acceptance criteria.

## Spec

Execute comprehensive QAS testing covering all functional and non-functional requirements.

## Acceptance Criteria

- [ ] Pruebas funcionales E2E en QAS: todos los flujos principales
- [ ] Pruebas no funcionales: rendimiento bajo carga esperada
- [ ] Pruebas seguridad basica: auth, permisos, input validation
- [ ] Matriz pruebas con resultados (pass/fail) por caso
- [ ] Bugs documentados con severidad
- [ ] Bugs criticos y altos corregidos
- [ ] Sign-off del equipo en resultados QAS
- [ ] Reporte QAS formal entregado

## Archivos a crear/modificar

- `docs/testing/qas-test-plan.md` (crear)
- `docs/testing/qas-test-results.md` (crear)
- `docs/testing/qas-bug-report.md` (crear)

## Decisiones de diseno

- **QAS como pre-produccion**: Ambiente identico a prod en configuracion.
- **Sign-off requerido**: No se avanza sin aprobacion.

## Out of scope

- UAT con usuarios finales (Sprint 11)
- Testing produccion
