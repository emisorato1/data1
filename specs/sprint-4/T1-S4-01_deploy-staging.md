# T1-S4-01: Deploy completo a K8s staging via Helm

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Franco, Agus) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | Demo MVP |
| Depende de | T1-S3-01, T1-S3-02 |
| Skill | `docker-deployment/SKILL.md` |
| Estimacion | XL (8h+) |

## Contexto

El sistema completo corriendo en K8s accesible para demo. Es el momento de verdad: todo lo construido en Sprint 1-3 se despliega en un entorno real accesible para stakeholders.

## Spec

Desplegar todo el stack via Helm chart en K8s staging: backend, PostgreSQL, Redis, Airflow, Langfuse, y opcionalmente frontend. HTTPS habilitado. Smoke test exitoso.

## Acceptance Criteria

- [x] `helm install enterprise-ai-platform ./helm/enterprise-ai-platform` funcional en staging
- [x] Backend (FastAPI) desplegado con al menos 2 replicas
- [x] PostgreSQL + pgvector operativo contra cloudSQL
- [x] Redis operativo dentro del cluster
- [x] Airflow con DAGs sincronizados y operativos
- [x] Langfuse accesible para el equipo
- [x] Frontend servido (puede ser via Nginx container dentro del chart o Vercel preview)
- [ ] HTTPS configurado (cert-manager o similar) -- ESTO FALTA
- [ ] Smoke test: login + preguntar + respuesta con streaming funciona en staging -- ESTO HABIAN ERRORES

## Archivos a crear/modificar

- `helm/enterprise-ai-platform/values-staging.yaml` (crear)
- Scripts de deploy si necesario

## Decisiones de diseno

- Staging como entorno dedicado (no compartido con dev): aislamiento para demo
- 2 replicas backend: validar que el sistema funciona con multiples instancias
- cert-manager para HTTPS: automatiza renovacion de certificados

## Out of scope

- Entorno de produccion (post-MVP)
- CD automatico (post-MVP)
- Escalado automatico / HPA (post-MVP)
