# Reporte de Auditoria de Sprint 3

**Fecha**: 2026-03-12
**Estado General**: APROBADO CON DEUDA

> Todos los FAILs CRITICAL fueron corregidos. Quedan 2 items TECH-DEBT: CVE diskcache (monitoreo) y 2 tests e2e que requieren Gemini API habilitada en GCP.

## Resumen Ejecutivo

| # | Punto de Auditoria | Estado | Severidad | Hallazgos |
|---|---|---|---|---|
| 1 | Suite de Tests | TECH-DEBT | HIGH | 476 unit + 195 integration pasan. 2 e2e fallan por Gemini API no habilitada en GCP (PATRON 3). Cobertura 83.28%. |
| 2 | Ruff & Mypy | PASS | - | ruff check, ruff format y mypy pasan sin errores. |
| 3 | Seguridad y Cumplimiento | TECH-DEBT | HIGH | CVE-2025-69872 en diskcache sin parche upstream (ya en deuda-tecnica.md). Revision manual PASS para alcance S3. |

## Detalle por Punto

### Punto 1: Suite de Tests

- **Estado**: TECH-DEBT (PATRON 3)
- **Severidad original**: HIGH

#### Sub-checks

| Sub-check | Estado | Detalle |
|-----------|--------|---------|
| Tests unitarios | PASS | 476 passed, 29 skipped |
| Tests integracion | PASS | 195 passed, 3 skipped |
| Tests e2e | FAIL | 8 passed, 2 failed, 3 skipped |
| Cobertura >= 80% | PASS | 83.28% (umbral: 80%) |

#### Evidencia

Los 2 tests e2e que fallan son `test_full_pipeline_pdf` y `test_duplicate_detection_e2e` en `tests/e2e/test_indexing_e2e.py`. Ambos requieren acceso a la Gemini Embedding API para ejecutar el pipeline de indexacion completo y fallan con:

```
403 PERMISSION_DENIED: Generative Language API has not been used in project 840903651879
before or it is disabled.
```

**Causa raiz**: La API de Generative Language no esta habilitada en el proyecto GCP local. Los tests necesitan embeddings reales de Gemini para indexar documentos y validar el pipeline E2E.

#### Clasificacion TECH-DEBT

Aplica **PATRON 3** (gap normativo con bloqueante externo conocido): los tests dependen de un servicio externo (Gemini API) cuya habilitacion en el proyecto GCP esta fuera del control del equipo de desarrollo. El tercer test e2e (`test_pipeline_failure_marks_run_failed`) pasa porque valida el manejo de errores sin necesitar embeddings reales.

#### Historial de correcciones en esta sesion

La regresion SecretStr (12 errors integration + 3 errors e2e) fue corregida agregando `.get_secret_value()` en:
- `tests/integration/test_document_repository.py:34`
- `tests/e2e/test_indexing_e2e.py:53`

Esto recupero 12 tests de integracion (183 → 195 passed) y revelo los 2 FAILs reales de e2e que estaban ocultos detras de los errors de setup.

---

### Punto 2: Ruff & Mypy

- **Estado**: PASS

#### Sub-checks

| Sub-check | Estado | Detalle |
|-----------|--------|---------|
| ruff check src/ | PASS | 0 errores |
| ruff format --check | PASS | 226 archivos formateados correctamente |
| mypy src/ | PASS | 0 errores |

Sin hallazgos. Los 3 sub-checks pasan limpiamente.

---

### Punto 3: Seguridad y Cumplimiento

- **Estado**: TECH-DEBT (PATRON 3) para parte automatizada + PASS para parte manual
- **Severidad original**: HIGH

#### Parte Automatizada (Script)

| Sub-check | Estado | Detalle |
|-----------|--------|---------|
| Secretos hardcodeados | PASS | Sin hallazgos |
| .env en git | PASS | Solo .env.example y .env.test |
| CVEs en dependencias | FAIL | diskcache 5.6.3 — CVE-2025-69872 |
| detect-secrets | PASS | Sin hallazgos |

**CVE-2025-69872**: Vulnerabilidad en `diskcache` (dependencia transitiva de `ragas`/`instructor`). Usa pickle para serializacion; atacante con acceso de escritura al directorio cache puede lograr ejecucion de codigo arbitrario. **No existe version parcheada** (5.6.3 es la ultima al 2026-03-12). Ya registrado en `docs/audit/deuda-tecnica.md` como item activo en MONITOREO desde Sprint 1. Mitigado por entorno containerizado con volumenes controlados.

Aplica **PATRON 3** (gap normativo con bloqueante externo conocido): la correccion depende de un release upstream que no ha ocurrido.

#### Parte Manual — Revision de Cifrado y RBAC (Alcance Sprint 3)

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| TLS in-transit | PASS | Ingress con cert-manager/letsencrypt-prod. HSTS enforced en SecurityHeadersMiddleware (`max-age=31536000; includeSubDomains`). |
| Cifrado at-rest | PASS | Cloud SQL con CMEK. Passwords hasheados (bcrypt). Refresh tokens hasheados (SHA-256). |
| Auth en chat SSE (T2-S3-01) | PASS | `Depends(get_current_user)` en `send_message_endpoint()`. Ownership validada en `prepare_chat_context()` antes de iniciar stream. |
| Input guardrail (T4-S3-01) | PASS | 47 patrones regex + LLM classifier (Gemini Flash Lite). Cobertura bilingue (ES/EN). Corto-circuito con mensaje seguro. Logging a Langfuse. |
| Docker hardening (T1-S3-01) | PASS | Multi-stage build, usuario non-root (UID 1000), filesystem read-only, no secrets en imagen, `.dockerignore` configurado. |
| Helm security (T1-S3-02) | PASS | Pod security context completo: `runAsNonRoot`, `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false`, `drop: ALL`, seccomp `RuntimeDefault`. Cloud SQL Auth Proxy como sidecar con mismo hardening. |
| RBAC en endpoints S3 | PASS | Todos los endpoints de chat y conversaciones requieren JWT. Ownership por `user_id` en queries. |

#### Hallazgos de la Revision Manual (fuera de alcance Sprint 3 pero documentados)

Los siguientes hallazgos son mejoras para produccion, **no bloqueantes para Sprint 3** ya que estan fuera del alcance de las specs de este sprint:

| Hallazgo | Severidad | Ubicacion | Sprint sugerido |
|----------|-----------|-----------|-----------------|
| Network policies deshabilitadas en Helm | HIGH | `values.yaml:401-408` | Pre-produccion |
| Secret management sin External Secrets operator | HIGH | `templates/secret.yaml` | Pre-produccion |
| Chat queries no auditadas en audit middleware | MEDIUM | `audit_middleware.py` | S4 |
| Rate limit en login endpoint no configurado | MEDIUM | `settings.py` | S4 |
| HSTS preload no configurado | LOW | SecurityHeadersMiddleware | Pre-produccion |

---

## Deuda Tecnica

| ID | Hallazgo | Patron | Severidad original | Sprint objetivo |
|----|----------|--------|--------------------|-----------------|
| DT-02 (existente) | CVE-2025-69872 en diskcache 5.6.3 | PATRON 3 | HIGH | Monitoreo continuo |
| DT-S3-01 | 2 tests e2e requieren Gemini API habilitada en GCP | PATRON 3 | HIGH | Cuando se habilite API en proyecto GCP |

**Nota**: DT-02 ya esta registrado en `docs/audit/deuda-tecnica.md` desde Sprint 1. DT-S3-01 depende de la habilitacion de la Generative Language API en el proyecto GCP 840903651879.

---

## Acciones Requeridas

| # | Accion | Severidad | Estado |
|---|--------|-----------|--------|
| 1 | ~~Agregar `.get_secret_value()` en fixture de `tests/integration/test_document_repository.py:34`~~ | ~~CRITICAL~~ | Resuelto (2026-03-12) |
| 2 | ~~Agregar `.get_secret_value()` en fixture de `tests/e2e/test_indexing_e2e.py:53`~~ | ~~CRITICAL~~ | Resuelto (2026-03-12) |
| 3 | ~~Ejecutar `ruff format scripts/generate_pdf.py`~~ | ~~MEDIUM~~ | Resuelto (2026-03-12) |
| 4 | Habilitar Generative Language API en proyecto GCP 840903651879 | HIGH | Pendiente |
| 5 | Monitorear diskcache >= 5.6.4 para CVE-2025-69872 | HIGH | Monitoreo |

---

## Conclusion y Proximos Pasos

El Sprint 3 esta **APROBADO CON DEUDA**. No hay FAILs CRITICAL.

Correcciones aplicadas en esta sesion:
- Regresion SecretStr corregida en 2 fixtures (recupero 12 tests de integracion + revelo estado real de e2e)
- `scripts/generate_pdf.py` reformateado con ruff

Estado final del codigo:
- 476 tests unitarios pasan
- 195 tests de integracion pasan
- 8 de 10 tests e2e pasan (2 fallan por Gemini API no habilitada en GCP — TECH-DEBT PATRON 3)
- Cobertura al 83.28%
- Punto 2 (ruff check, ruff format, mypy) pasa limpiamente
- Seguridad y cumplimiento normativo cubren el alcance del sprint: Docker hardening, Helm pod security, JWT auth en SSE, input guardrail robusto, TLS y RBAC implementados

Deuda tecnica pendiente:
- DT-02: CVE-2025-69872 en diskcache — sin parche upstream, monitoreo continuo
- DT-S3-01: 2 tests e2e requieren habilitacion de Gemini API en proyecto GCP
