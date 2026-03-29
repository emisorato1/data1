# T1-S8-02: Helm chart valores multi-entorno (dev, staging, prod)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Agus) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T1-S10-01 |
| Depende de | T1-S3-02 (done) |
| Skill | `docker-deployment/SKILL.md` |
| Estimacion | L (4-8h) — POST-32 |

## Contexto

The Helm chart has a single values.yaml for dev. Production requires different resource limits, replicas, secrets. Multi-environment support enables consistent deployments across dev, staging, prod.

## Spec

Create environment-specific Helm values files and configure the chart for multi-environment deployment with sealed-secrets support.

## Acceptance Criteria

- [x] `charts/enterprise-ai/values-dev.yaml` con configuracion desarrollo
- [x] `charts/enterprise-ai/values-staging.yaml` con configuracion staging
- [x] `charts/enterprise-ai/values-prod.yaml` con configuracion produccion
- [x] Recursos diferenciados: dev (minimos), staging (medio), prod (full)
- [x] Replicas: dev (1), staging (2), prod (3+)
- [x] Secrets referenciados via sealed-secrets o External Secrets Operator
- [x] Ingress configurado per-environment (distintos dominios)
- [x] HPA solo en staging y prod
- [x] Tests: `helm template` renderiza correctamente para cada environment

## Archivos a crear/modificar

- `charts/enterprise-ai/values-dev.yaml` (crear)
- `charts/enterprise-ai/values-staging.yaml` (crear)
- `charts/enterprise-ai/values-prod.yaml` (crear)
- `charts/enterprise-ai/templates/hpa.yaml` (crear)
- `charts/enterprise-ai/values.yaml` (modificar)

## Decisiones de diseno

- **Values file per environment**: Patron estandar Helm, auditable.
- **Base values + overrides**: values.yaml defaults, env files only overrides.
- **Sealed-secrets**: Secrets encriptados en git, desencriptados en cluster.

## Out of scope

- Helmfile o ArgoCD
- Multi-cluster
- Secret rotation automatica
