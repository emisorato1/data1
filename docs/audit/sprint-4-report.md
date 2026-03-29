# Reporte de Auditoria de Sprint 4

**Fecha**: 2026-03-12
**Estado General**: APROBADO CON DEUDA

## Resumen Ejecutivo

| # | Punto de Auditoria | Estado | Severidad | Hallazgos |
|---|---|---|---|---|
| 1 | Suite de Tests | TECH-DEBT | HIGH | 476 unit + 195 integration PASS. 2 e2e FAIL por Gemini API deshabilitada (PATRON 3). Cobertura 84% PASS |
| 2 | Ruff & Mypy | PASS | - | ruff check, ruff format y mypy sin errores |
| 3 | Seguridad y Cumplimiento | TECH-DEBT | HIGH | CVE-2025-69872 diskcache (PATRON 3). Revision manual PASS con observacion menor en regex CUIT |

Todos los FAILs corresponden a deuda tecnica previamente documentada (Gemini API, diskcache CVE). No hay FAILs CRITICAL nuevos. Sprint 4 introduce rate limiting, output guardrail, deploy staging y dataset demo sin regresiones.

---

## Detalle por Punto

### Punto 1: Suite de Tests

- **Estado**: TECH-DEBT HIGH
- **Resultados**:

| Sub-check | Estado | Detalle |
|-----------|--------|---------|
| Tests unitarios | PASS | 476 passed, 29 skipped en 59.40s |
| Tests integracion | PASS | 195 passed, 3 skipped en 28.50s |
| Tests e2e | FAIL → TECH-DEBT | 8 passed, 2 failed, 3 skipped en 21.70s |
| Cobertura >= 80% | PASS | 84.00% (umbral: 80%) |

- **Evidencia e2e**: Los 2 tests que fallan son `test_full_pipeline_pdf` y `test_duplicate_detection_e2e` en `tests/e2e/test_indexing_e2e.py`. Ambos requieren embeddings reales de Gemini y fallan con `403 PERMISSION_DENIED: Generative Language API has not been used in project 840903651879`.
- **Clasificacion**: TECH-DEBT PATRON 3 (gap con bloqueante externo). Esta deuda esta documentada desde Sprint 3 en `docs/audit/deuda-tecnica.md`.
- **Impacto**: No es un defecto de codigo. Los 8 e2e restantes pasan correctamente, incluyendo el test de error handling del pipeline.

### Punto 2: Linting y Type Checking

- **Estado**: PASS
- **Resultados**:

| Sub-check | Estado |
|-----------|--------|
| `ruff check src/` | PASS |
| `ruff format --check .` | PASS |
| `mypy src/` | PASS |

- Sin hallazgos. Codigo limpio.

### Punto 3: Seguridad y Cumplimiento

#### Parte Automatizada

| Sub-check | Estado | Detalle |
|-----------|--------|---------|
| Secretos hardcodeados | PASS | Sin secretos en src/, docker/, scripts/, dags/ |
| Archivos .env en git | PASS | Solo .env.example y .env.test (permitidos) |
| CVEs en dependencias | FAIL → TECH-DEBT | CVE-2025-69872 en diskcache 5.6.3 |
| detect-secrets | PASS | Sin hallazgos |

- **CVE-2025-69872**: Dependencia transitiva de ragas/instructor. Usa pickle para serializacion. Sin version parcheada disponible (5.6.3 es la ultima). Mitigado por entorno containerizado. TECH-DEBT PATRON 3 documentado desde Sprint 1.

#### Parte Manual — Revision de Seguridad Sprint 4

**Archivos revisados** (13 archivos, ~2500 lineas):
- `src/infrastructure/api/middleware/rate_limiter.py` — Rate limiting ASGI
- `src/infrastructure/cache/token_bucket.py` — Token bucket Redis Lua
- `src/infrastructure/security/guardrails/output_validator.py` — Output guardrail
- `src/application/graphs/nodes/validate_output.py` — Nodo de validacion
- `src/infrastructure/api/main.py` — Stack de middleware
- `docker/Dockerfile` — Build multi-stage
- `helm/enterprise-ai-platform/values.yaml` — Configuracion Helm
- `helm/enterprise-ai-platform/values-staging.yaml` — Staging overrides
- `helm/enterprise-ai-platform/templates/deployment.yaml` — Deployment K8s
- `helm/enterprise-ai-platform/templates/ingress.yaml` — TLS/Ingress
- `src/infrastructure/security/jwt.py` — Autenticacion JWT
- `src/config/settings.py` — Configuracion

##### A. Cifrado (at-rest e in-transit)

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| TLS en ingress | PASS | cert-manager con letsencrypt-prod (`values.yaml:166`), staging usa letsencrypt-staging (`values-staging.yaml:78`) |
| Cloud SQL Auth Proxy | PASS | mTLS sidecar en `deployment.yaml:124-151` |
| Cloud SQL encryption at-rest | PASS | GCP Cloud SQL cifra por defecto |
| Redis auth | PASS | Password habilitado (`values-staging.yaml:143`) |
| Redis TLS | OBSERVACION | Comunicacion in-cluster sin TLS. Aceptable en red privada de cluster |
| APIs externas | PASS | Vertex AI/Gemini usan HTTPS |

##### B. Control de Acceso (RBAC)

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| Rate limiting por rol | PASS | JWT role extraction (`rate_limiter.py:89`). Admin: 100 cap/10 rate. User: 20 cap/2 rate |
| Workload Identity | PASS | GKE WI configurado (`values-staging.yaml:34-36`), sin JSON keys |
| Pod Security Context | PASS | Non-root UID 1000, readOnlyRootFilesystem, drop ALL caps (`values.yaml:60-75`) |
| Cloud SQL Proxy hardening | PASS | Non-root UID 65532, readonly root, drop ALL (`deployment.yaml:127-150`) |
| Middleware stack | PASS | TrustedHost + CORS + SecurityHeaders + RateLimit (`main.py:167-197`) |

##### C. OWASP Top 10

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| A01 Broken Access Control | PASS | JWT + RBAC + rate limiting con diferenciacion por rol |
| A02 Cryptographic Failures | PASS | TLS, Cloud SQL Auth Proxy, SecretStr para credenciales |
| A03 Injection | PASS | Output guardrail detecta PII (DNI, CUIT, CBU). Input guardrail con 47 regex |
| A04 Insecure Design | PASS | Rate limiting fail-open con logging (disponibilidad > enforcement) |
| A05 Security Misconfiguration | PASS | Docker non-root, Helm security contexts, no caps |
| A07 XSS | PASS | TrustedHostMiddleware, CORS configurado, SecurityHeaders |
| A09 Logging/Monitoring | PASS | Langfuse observability decorators, structlog, rate limit logging |

##### D. Docker/K8s Hardening

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| Multi-stage build | PASS | Builder stage descartado en imagen final (`Dockerfile:6-89`) |
| Non-root user | PASS | appuser UID 1000, /sbin/nologin (`Dockerfile:48-49`) |
| Read-only root fs | PASS | Helm `readOnlyRootFilesystem: true` (`values.yaml:72`) |
| Resource limits | PASS | CPU/memory requests y limits (`values.yaml:78-84`) |
| Health probes | PASS | Liveness + readiness + startup probes (`values.yaml:87-122`) |
| PDB | PASS | minAvailable: 1 (`values.yaml:145-147`) |
| seccomp | PASS | RuntimeDefault (`values.yaml:65`) |
| Network policies | OBSERVACION | Definidas pero deshabilitadas (`values.yaml:401`). Habilitar en produccion |

##### E. Hallazgo en Output Guardrail

- **Hallazgo**: Regex de CUIT/CUIL `\b\d{2}-?\d{8}-?\d\b` permite secuencias malformadas como "20-123456789" (9 digitos entre guiones en vez de 8)
- **Severidad**: MEDIUM (puede generar falsos positivos en deteccion PII, no es una vulnerabilidad de seguridad)
- **Archivo**: `src/infrastructure/security/guardrails/output_validator.py:52`
- **Remediacion sugerida**: Reemplazar con `\b(?:\d{2}-\d{8}-\d|\d{11})\b` para forzar "todos los guiones" o "ningun guion"
- **Impacto**: Bajo. El regex actual es mas permisivo (detecta mas patrones de lo necesario), no menos. No hay riesgo de PII no detectado.

---

## Deuda Tecnica

| ID | Hallazgo | Patron | Severidad | Sprint origen | Estado |
|----|----------|--------|-----------|---------------|--------|
| DT-S3-01 | 2 tests e2e requieren Gemini API habilitada en GCP | PATRON 3 | HIGH | S3 | BLOQUEADO |
| DT-S1-01 | CVE-2025-69872 en diskcache 5.6.3 | PATRON 3 | HIGH | S1 | MONITOREO |
| DT-S5-01 | xECM sync bloqueado sin acceso OpenText | PATRON 3 | HIGH | S5 | BLOQUEADO |
| DT-S6-01 | PII Sanitizer modulo standalone pendiente | PATRON 1 | CRITICAL | S6 | PENDIENTE (S7) |
| DT-S4-01 | Regex CUIT permisivo en output guardrail | PATRON 1 | MEDIUM | S4 | RESUELTO (2026-03-12) |
| DT-S4-02 | Network policies deshabilitadas en Helm | PATRON 1 | MEDIUM | S4 | RESUELTO (2026-03-12) |

---

## Verificacion de Specs Sprint 4

| Task ID | Titulo | Estado spec | Verificacion auditoria |
|---------|--------|-------------|----------------------|
| T1-S4-01 | Deploy K8s staging Helm | DONE* | Helm chart funcional, TLS configurado, security contexts correctos. *HTTPS y smoke test pendientes |
| T1-S4-02 | Monitoring y alertas GCP | PENDING | No implementado — no afecta auditoria de codigo |
| T2-S4-01 | Rate limiting basico | DONE | Implementado con Redis token bucket, ASGI middleware, diferenciacion por rol |
| T3-S4-01 | Demo dataset via Airflow | DONE | 18 documentos bancarios, DAG batch loading implementado |
| T3-S4-02 | Retrieval tuning | DONE | Grid search implementado, parametros configurables via settings |
| T4-S4-01 | Output guardrail | DONE | Faithfulness heuristic + PII detection (DNI/CUIT/CBU). Observacion menor en regex |
| T4-S4-02 | Demo flow + edge cases | DONE* | Edge cases cubiertos. *Algunos ACs sin checkmark |
| T5-S4-01 | Conversation sidebar | DONE | Frontend implementado con historial y navegacion |
| T5-S4-02 | Citations + UI polish | DONE | Citation chips y source panel implementados |

---

## Conclusion y Proximos Pasos

**Sprint 4 esta APROBADO CON DEUDA**. No hay FAILs CRITICAL nuevos. Los 3 puntos de auditoria pasan o se clasifican como TECH-DEBT con patrones validos:

- **679 tests pasan** (476 unit + 195 integration + 8 e2e) con **84% cobertura**
- **Linting/typing limpio** — ruff y mypy sin errores
- **Seguridad robusta** — rate limiting, output guardrail, Helm hardening, TLS, RBAC

### Acciones resueltas post-auditoria

1. ~~**MEDIUM**: Corregir regex CUIT en `output_validator.py:52`~~ → RESUELTO: regex cambiado a `(?:\d{2}-\d{8}-\d|\d{11})` + test agregado
2. ~~**MEDIUM**: Habilitar network policies en `values.yaml:401`~~ → RESUELTO: `networkPolicy.enabled: true`

### Acciones pendientes (bloqueantes externos)

3. **HIGH (externo)**: Habilitar Generative Language API en proyecto GCP 840903651879 para desbloquear 2 e2e tests
4. **MONITOREO**: Verificar diskcache >= 5.6.4 para CVE-2025-69872
