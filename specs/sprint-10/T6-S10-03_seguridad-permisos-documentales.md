# IA-27: Seguridad pre-produccion — permisos documentales

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Gaston, Emi) |
| Prioridad | Critica |
| Estado | pending |
| Bloqueante para | T6-S10-04 |
| Depende de | T4-S6-01, T3-S7-01, [Entregable #6: Permisos documentales xECM] |
| Skill | `security-mirror/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

Document permissions are a critical security feature in banking. Before production, the complete permission chain (OpenText sync -> permission mirror -> late binding search filter) must be validated with real permission data from the bank.

## Spec

Validate document permission enforcement end-to-end with real xECM permission data (Entregable #6), ensuring no unauthorized document access.

## Acceptance Criteria

- [ ] Permisos xECM reales sincronizados via CDC DAG
- [ ] Al menos 5 usuarios de prueba con permisos distintos (CAT, RRHH, mixto, admin, sin permisos)
- [ ] Cada usuario ve SOLO documentos a los que tiene acceso
- [ ] Cross-area isolation verificado: CAT no ve RRHH y viceversa
- [ ] Escalacion de privilegios testeada y bloqueada
- [ ] Sync de permisos verificado: cambio en OpenText reflejado en < 6 horas
- [ ] Reporte de seguridad permisos con matriz de acceso

## Archivos a crear/modificar

- `docs/security/permissions-validation-report.md` (crear)

## Decisiones de diseno

- **Real permission data**: Datos sinteticos no son suficientes para validar produccion.
- **Matriz de acceso**: Documento formal de quien accede a que.

## Out of scope

- Fine-grained permissions (field-level), real-time permission sync
