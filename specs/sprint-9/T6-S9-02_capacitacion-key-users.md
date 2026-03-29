# T6-S9-02: Capacitacion key users y material soporte

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco) |
| Prioridad | Alta |
| Estado | pending |
| Bloqueante para | T6-S11-02 |
| Depende de | T6-S8-03 |
| Skill | - |
| Estimacion | L (4-8h) |

## Contexto

Key users from CAT and RRHH need training before UAT. Training covers chat interface, citations, document management, issue reporting.

## Spec

Prepare and deliver training sessions for key users with materials and support documentation.

## Acceptance Criteria

- [ ] Material capacitacion: guia uso con screenshots
- [ ] Script pruebas para key users (escenarios a validar)
- [ ] Al menos 2 sesiones capacitacion (CAT + RRHH)
- [ ] Registro asistencia y feedback
- [ ] FAQ basico con preguntas frecuentes
- [ ] Canal soporte definido para reportar incidencias
- [ ] Material entregado en formato accesible (PDF + web)

## Archivos a crear/modificar

- `docs/training/user-guide-v1.md` (crear)
- `docs/training/test-script-key-users.md` (crear)
- `docs/training/faq.md` (crear)

## Decisiones de diseno

- **Key users primero**: Parte del UAT, necesitan entender antes de evaluar.
- **Material iterativo**: v1 ahora, v2 post-UAT.

## Out of scope

- Capacitacion usuarios finales (Sprint 11)
- Video/screencast
- Capacitacion IT banco
