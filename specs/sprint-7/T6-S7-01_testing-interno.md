# T6-S7-01: Testing interno plataforma

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco, team) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T6-S8-01 |
| Depende de | T6-S6-01, T4-S6-01 |
| Skill | `testing-strategy/SKILL.md` |
| Estimacion | L (4-8h) |

> N/A (maps to IA-07 from roadmap)

## Contexto

After calibration (Sprint 6), the platform needs comprehensive internal testing before advancing to integration testing. This covers functional testing of all features, auth flows, error handling, and edge cases.

## Spec

Execute systematic internal testing of the entire platform, documenting issues found and verifying fixes before proceeding to integration testing in DEV environment.

## Acceptance Criteria

- [x] Plan de testing interno documentado con casos de prueba por area
- [x] Pruebas funcionales: login, chat, streaming, citaciones, conversaciones, feedback
- [x] Pruebas de upload y gestion de documentos (si disponible)
- [x] Pruebas de auth: login, logout, token refresh, sesion expirada
- [x] Pruebas de error handling: inputs invalidos, server errors, timeouts
- [x] Pruebas de permisos: usuario ve solo sus documentos/conversaciones
- [x] Al menos 30 casos de prueba ejecutados y documentados
- [x] Bugs encontrados registrados con severidad y pasos para reproducir
- [x] Bugs criticos corregidos antes de cerrar el sprint
- [x] Reporte de testing con resultados y coverage

## Archivos a crear/modificar

- `docs/testing/internal-test-plan.md` (crear)
- `docs/testing/internal-test-results.md` (crear)
- `docs/testing/bug-report-sprint7.md` (crear)

## Decisiones de diseno

- **Testing manual + automatizado**: Los tests automatizados existentes cubren unitarios, el testing manual cubre UX y flujos E2E
- **Severidad clasificada**: Critico (bloqueante), Alto (afecta funcionalidad core), Medio (degraded experience), Bajo (cosmetico)
- **Fix antes de avanzar**: Bugs criticos se corrigen en el sprint, no se acumulan

## Out of scope

- Testing de performance/carga (spec T1-S9-01)
- Testing de seguridad/pentesting (spec T2-S9-01)
- Testing con datos de produccion
