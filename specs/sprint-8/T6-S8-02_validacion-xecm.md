# T6-S8-02: Validacion con datos reales xECM

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco, Gaston) |
| Prioridad | Alta |
| Estado | pending |
| Bloqueante para | T6-S8-03 |
| Depende de | T6-S6-02, [Entregable #1: OpenText CS operativo] |
| Skill | `security-mirror/SKILL.md` |
| Estimacion | L (4-8h) — IA-20 |

## Contexto

Up to this point, all testing used synthetic data. With OpenText Content Server operational (Entregable #1), we validate against real xECM documents and permissions.

## Spec

Execute validation tests using real documents from OpenText Content Server, verifying RAG quality, permission enforcement, and response accuracy.

## Acceptance Criteria

- [ ] Consultas ejecutadas con documentos reales del Content Server
- [ ] Respuestas verificadas por stakeholders del banco (CAT y RRHH)
- [ ] Permisos xECM correctamente reflejados: usuario CAT ve solo docs CAT
- [ ] Calidad respuestas con datos reales evaluada vs escenarios Sprint 6
- [ ] Al menos 10 consultas reales ejecutadas y documentadas
- [ ] Ajustes parametros RAG si calidad difiere de sinteticos
- [ ] Documento validacion con resultados y observaciones

## Archivos a crear/modificar

- `docs/testing/xecm-validation-results.md` (crear)
- `docs/calibration/real-data-adjustments.md` (crear si hay ajustes)

## Decisiones de diseno

- **Validacion con stakeholders**: Usuarios del banco validan respuestas.
- **Comparacion sintetico vs real**: Identificar gaps.

## Out of scope

- Carga masiva documentos reales
- Optimizacion performance con datos reales
