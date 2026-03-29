# T6-S6-02: Configuracion escenarios prueba xECM

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco, Gaston) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T6-S8-02 |
| Depende de | [Entregable #2: xECM config], [Entregable #5: Escenarios de prueba] |
| Skill | `security-mirror/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

Before validating with real xECM data, test scenarios must be configured: CAT documents with specific permissions, RRHH documents restricted to RRHH team, cross-department scenarios, and edge cases.

## Spec

Configure and document test scenarios using xECM folder structures, roles, and document types provided by the bank (Entregable #2).

## Acceptance Criteria

- [x] Escenarios CAT configurados: documentos por tipo (normativas, procedimientos, circulares)
- [x] Escenarios RRHH configurados: documentos por tipo (politicas, convenios, beneficios)
- [x] Escenarios cross-area: documentos compartidos entre CAT y RRHH
- [x] Escenarios de permisos: usuario CAT no ve docs RRHH y viceversa
- [x] Al menos 10 escenarios documentados con query esperada y respuesta esperada
- [x] Datos sinteticos actualizados para reflejar estructura xECM real
- [x] Documento de escenarios aprobado por stakeholders del banco

## Archivos a crear/modificar

- `docs/testing/xecm-test-scenarios.md` (crear)
- `scripts/seed_xecm_scenarios.py` (crear — extiende `scripts/seed_data.py` de T3-S3-01 con escenarios xECM reales)

## Decisiones de diseno

- **Escenarios por area funcional**: Refleja la organizacion real del banco.
- **Aprobacion del banco**: Los escenarios deben ser relevantes para el negocio.
- **Aprobacion stakeholders**: Escenarios revisados y aprobados por equipo del banco (Sprint 6 review).

## Out of scope

- Testing automatizado de escenarios (manual en esta fase)
- Validacion con datos reales (Sprint 8)
