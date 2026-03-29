# IA-32: Go-Live componente IA en produccion

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco) |
| Prioridad | Critica |
| Estado | pending |
| Bloqueante para | T6-S11-05 |
| Depende de | T6-S11-02, T6-S11-03, [Aprobacion banco] |
| Skill | - |
| Estimacion | M (2-4h) |

## Contexto

The formal go-live moment: the AI component is made available to all end users in production. Requires bank approval, communication plan, and coordinated activation.

## Spec

Execute the go-live of the Enterprise AI Platform, including final bank approval, user access activation, communication, and initial monitoring.

## Acceptance Criteria

- [ ] Aprobacion formal del banco para go-live obtenida
- [ ] Comunicacion go-live enviada a usuarios (email, intranet)
- [ ] Accesos usuarios finales activados
- [ ] Monitoreo intensivo primeras 4 horas post-go-live
- [ ] Canal de soporte activo para incidencias inmediatas
- [ ] Rollback ejecutable en < 30 minutos si es necesario
- [ ] Log de go-live documentado con timestamps

## Archivos a crear/modificar

- `docs/deployment/go-live-log.md` (crear)
- `docs/deployment/go-live-communication.md` (crear)

## Decisiones de diseno

- **Aprobacion formal**: No se activa sin sign-off del banco.
- **Monitoreo intensivo**: Primeras horas son criticas.

## Out of scope

- Feature rollout gradual (all-at-once), marketing/communications internas del banco
