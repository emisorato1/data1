# IA-25: Configuracion ambiente produccion (GKE, CloudSQL, secrets)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Franco) |
| Prioridad | Critica |
| Estado | pending |
| Bloqueante para | T6-S11-01 |
| Depende de | T1-S8-02 |
| Skill | `docker-deployment/SKILL.md` |
| Estimacion | XL (8+h) |

## Contexto

Production environment requires careful configuration: GKE cluster with production-grade settings, Cloud SQL with HA, secrets management, monitoring, and backup policies. This is the final infrastructure setup before go-live.

## Spec

Configure and validate the production environment for the Enterprise AI Platform, including GKE workloads, Cloud SQL, secrets, monitoring, and backup.

## Acceptance Criteria

- [ ] GKE production namespace configurado con resource quotas y limits
- [ ] Cloud SQL produccion con HA habilitado y backup automatico
- [ ] Secrets produccion configurados via Sealed Secrets o Secret Manager
- [ ] Helm values-prod.yaml validado y aplicado
- [ ] Monitoring y alertas produccion configurados
- [ ] Backup policies para Cloud SQL y GCS documentados
- [ ] Network policies aplicadas (restrict pod-to-pod)
- [ ] SSL/TLS configurado para ingress produccion
- [ ] Smoke test en produccion (pre-datos): deploy funciona, health checks pasan
- [ ] Runbook de operaciones documentado

## Archivos a crear/modificar

- `docs/deployment/production-config.md` (crear)
- `docs/operations/runbook.md` (crear)
- `charts/enterprise-ai/values-prod.yaml` (verificar/actualizar)

## Decisiones de diseno

- **HA para Cloud SQL**: Produccion bancaria requiere alta disponibilidad.
- **Network policies**: Zero-trust networking dentro del cluster.
- **Runbook**: Equipo de operaciones necesita documentacion.

## Out of scope

- Automatizacion DR (disaster recovery), multi-region, performance tuning produccion
