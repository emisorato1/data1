# T1-S3-01: Dockerfile multi-stage + security hardening

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Franco) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T1-S4-01 (deploy K8s) |
| Depende de | - |
| Skill | `docker-deployment/references/multi-stage-dockerfile.md` + `docker-deployment/references/security-hardening.md` |
| Estimacion | M (2-4h) |

## Contexto

Imagen de produccion optimizada y segura. Es prerequisito para desplegar en K8s. Debe ser pequena, sin secrets, y correr como non-root para cumplir con politicas de seguridad bancaria.

## Spec

Crear Dockerfile multi-stage con builder y runtime separados, imagen slim, usuario non-root, y filesystem read-only donde sea posible.

## Acceptance Criteria

- [x] Dockerfile multi-stage: builder (instala deps) + runtime (copia solo lo necesario)
- [x] Imagen base: `python:3.12-slim`
- [x] Usuario non-root (`appuser`, UID 1000)
- [x] Filesystem read-only donde sea posible
- [x] No secrets en imagen (usar env vars / mounted secrets)
- [x] `.dockerignore` configurado (excluye .git, tests, docs, __pycache__, dags/)
- [ ] Imagen final < 200MB — **No alcanzable**: stack actual (~990MB) dominado por pyarrow (150MB), google SDKs (115MB), pymupdf (57MB), pandas (42MB), numpy (58MB). Requiere refactor de dependencias (fuera de alcance de esta spec).
- [x] `docker build` + `docker run` funcional

## Archivos a crear/modificar

- `docker/Dockerfile` (crear)
- `docker/.dockerignore` (crear)

## Decisiones de diseno

- Multi-stage: builder con herramientas de compilacion, runtime sin ellas = imagen mas pequena
- python:3.12-slim sobre alpine: mejor compatibilidad con wheels precompilados
- UID 1000: convencion estandar, compatible con GKE security policies

## Out of scope

- Dockerfile para frontend (se agrega en Sprint 4 si es necesario)
- Docker Compose de produccion (se usa Helm en K8s)
- Scan de vulnerabilidades de imagen (post-MVP)
