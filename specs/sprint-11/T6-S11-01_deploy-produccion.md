# IA-29: Deploy produccion, migracion y verificacion

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco, Agus) |
| Prioridad | Critica |
| Estado | pending |
| Bloqueante para | T6-S11-02 |
| Depende de | T6-S10-04, T1-S10-01 |
| Skill | `docker-deployment/SKILL.md` |
| Estimacion | XL (8+h) |

## Contexto

The final deployment to production. All testing is complete, infrastructure is ready, and approvals are in place. This includes Helm deploy, database migration, data migration, and post-deploy verification.

## Spec

Execute production deployment of the Enterprise AI Platform including Helm install, database migration, vector store data migration, and comprehensive post-deploy verification.

## Acceptance Criteria

- [ ] Deploy Helm en produccion con values-prod.yaml
- [ ] Migraciones Alembic ejecutadas en Cloud SQL produccion
- [ ] VectorDB datos migrados (embeddings de documentos aprobados)
- [ ] Platform DB datos migrados (usuarios, configuracion)
- [ ] Smoke test post-deploy: health checks, login, query basica
- [ ] Monitoring y alertas verificados (metricas fluyen)
- [ ] Rollback plan documentado y testeado
- [ ] Deploy log documentado con timestamps

## Archivos a crear/modificar

- `docs/deployment/production-deploy-log.md` (crear)
- `docs/deployment/rollback-plan.md` (crear)

## Decisiones de diseno

- **Blue-green conceptual**: El deploy a produccion es nuevo (no hay version anterior).
- **Rollback plan**: Siempre tener plan B documentado.

## Out of scope

- Canary deployment, feature flags, A/B testing
