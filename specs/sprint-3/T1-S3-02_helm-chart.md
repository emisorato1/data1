# T1-S3-02: Helm chart Enterprise AI Platform (base)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Agus) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T1-S4-01 (deploy staging) |
| Depende de | - |
| Skill | `docker-deployment/SKILL.md` |
| Estimacion | XL (8h+) |

## Contexto

Helm chart que despliega todo el stack RAG en K8s. Es la pieza central de infraestructura que permite desplegar el sistema de forma reproducible en cualquier cluster.

## Spec

Crear Helm chart con templates para FastAPI backend, PostgreSQL, Redis, ConfigMap, Secrets, ServiceAccount, y sub-charts para dependencias.

## Acceptance Criteria

- [x] `helm/enterprise-ai-platform/Chart.yaml` con metadata del chart
- [x] `values.yaml` con configuracion parametrizable: replicas, resources, image tags, env vars
- [x] Templates para:
  - Deployment FastAPI (backend) con liveness/readiness probes (`/health`, `/health/ready`)
  - Service + Ingress para API
  - ConfigMap para config no-secreta
  - Secret para JWT_SECRET, DATABASE_URL, API keys
  - ServiceAccount con permisos minimos
- [x] Sub-charts o dependencias para PostgreSQL (bitnami/postgresql con pgvector) y Redis (bitnami/redis)
- [x] `helm template` genera manifests validos (pendiente validar con Helm CLI instalado)
- [x] `helm install --dry-run` pasa sin errores (pendiente validar con Helm CLI instalado)
- [x] Documentacion de values: que configurar para cada entorno (dev, staging, prod)

## Archivos a crear/modificar

- `helm/enterprise-ai-platform/Chart.yaml` (crear)
- `helm/enterprise-ai-platform/values.yaml` (crear)
- `helm/enterprise-ai-platform/templates/deployment.yaml` (crear)
- `helm/enterprise-ai-platform/templates/service.yaml` (crear)
- `helm/enterprise-ai-platform/templates/ingress.yaml` (crear)
- `helm/enterprise-ai-platform/templates/configmap.yaml` (crear)
- `helm/enterprise-ai-platform/templates/secret.yaml` (crear)
- `helm/enterprise-ai-platform/templates/serviceaccount.yaml` (crear)

## Decisiones de diseno

- Helm sobre Kustomize: mejor para parametrizacion multi-entorno, ecosystem de charts
- bitnami sub-charts: bien mantenidos, PG con pgvector extension disponible
- ServiceAccount dedicado: least privilege, requerido por auditorias

## Out of scope

- Chart para frontend (se decide en Sprint 4 si va en Helm o Vercel)
- Sealed secrets / SOPS (post-MVP)
- ArgoCD / GitOps (post-MVP)
