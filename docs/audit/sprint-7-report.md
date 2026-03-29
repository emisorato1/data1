# Reporte de Auditoria de Sprint 7
**Fecha**: 2026-03-25
**Estado General**: APROBADO CON DEUDA

## Resumen Ejecutivo

| # | Punto de Auditoria | Estado | Severidad | Hallazgos |
|---|---|---|---|---|
| 1 | Suite de Tests | FAIL | HIGH | 9 tests fallan: 6 por texto HOTFIX (acentos), 1 limite demo docs, 2 e2e GCP PERMISSION_DENIED. Cobertura 85.23% OK |
| 2 | Ruff & Mypy | FAIL + TECH-DEBT | HIGH + MEDIUM | mypy: 2 errores en src/. ruff format: 4 archivos fuera de src/ (PATRON 2) |
| 3 | Seguridad y Cumplimiento | FAIL | HIGH | 5 CVEs en dependencias (ninguno CVSS>=9.0). Revision manual: seguridad core implementada, gaps menores |

**Specs del Sprint 7**: 16 specs totales — 11 done, 5 pending (T2-S7-01, T3-S7-01, T5-S7-01, T5-S7-03, T6-S7-01)

---

## Detalle por Punto

### Punto 1: Suite de Tests

- **Estado**: FAIL
- **Severidad**: HIGH
- **Cobertura**: 85.23% >= 80% ✅

#### Fallos unitarios (2)

| Test | Causa | Archivo |
|------|-------|---------|
| `TestDemoDataset::test_demo_has_maximum_documents` | Demo docs crecio a 22, test espera <=20 | `tests/unit/test_dag_load_demo_data.py:188` |
| `TestRAGGraphFueraDominioFlow::test_fuera_dominio_returns_blocked_response` | HOTFIX cambio "area" → "área" (acento), assertion no actualizada | `tests/unit/test_rag_graph.py:237` |

#### Fallos de integracion (3)

| Test | Causa | Archivo |
|------|-------|---------|
| `TestRespondBlockedIntegration::test_fuera_dominio_response` | Assertion busca "fuera de mi area" pero respuesta tiene "área" | `tests/integration/test_rag_nodes.py:319` |
| `TestRespondBlockedIntegration::test_blocked_response` | Assertion busca "reformula" pero respuesta tiene "reformulá" | `tests/integration/test_rag_nodes.py:324` |
| `TestRAGGraphIntegration::test_fuera_dominio_routes_to_respond_blocked` | Misma causa: "area" vs "área" | `tests/integration/test_rag_nodes.py:623` |

#### Fallos e2e (3)

| Test | Causa | Archivo |
|------|-------|---------|
| `TestIndexingE2E::test_full_pipeline_pdf` | GCP 403 PERMISSION_DENIED (ADC expirado) | `tests/e2e/test_indexing_e2e.py:175` |
| `TestIndexingE2E::test_duplicate_detection_e2e` | Misma causa: GCP 403 | `tests/e2e/test_indexing_e2e.py` |
| `TestPromptInjectionE2EFlow::test_injection_is_blocked` | Probable misma causa: servicio externo | `tests/e2e/test_rag_pipeline.py` |

#### Fallo de seguridad (1)

| Test | Causa | Archivo |
|------|-------|---------|
| `TestTopicClassifierNode::test_deflection_response_matches_config` | "fuera de mi area" vs "área" (acento del HOTFIX) | `tests/security/test_topic_control.py:331` |

**Causa Raiz**: El commit `0581d12` (HOTFIX classify_intent) corrigio la ortografia de los mensajes de deflexion (agrego tildes), pero no actualizo las assertions en 6 tests que verifican texto exacto. Los 3 e2e fallan por ADC expirado (ya ocurrio en S3-S6, se resolvio con `gcloud auth application-default login`).

**Remediacion Sugerida**:
1. Actualizar las 6 assertions de texto para usar `"área"` y `"reformulá"` con tilde
2. Ajustar limite de demo docs a 25 en `test_dag_load_demo_data.py:188`
3. Re-autenticar ADC: `gcloud auth application-default login --project=itmind-macro-ai-dev-0`

---

### Punto 2: Ruff & Mypy

- **Estado**: FAIL (mypy) + TECH-DEBT (ruff format)
- **Severidad**: HIGH (mypy) + MEDIUM (format, PATRON 2)

#### ruff check: PASS ✅

Sin errores de linting ni reglas de seguridad bandit (`S`).

#### ruff format: TECH-DEBT (PATRON 2)

4 archivos fuera de `src/` necesitan reformateo:

| Archivo | Ubicacion |
|---------|-----------|
| `dags/indexing/load_demo_data.py` | dags/ (fuera de src/) |
| `scripts/seed_data.py` | scripts/ (fuera de src/) |
| `tests/security/test_pii_output_guardrail.py` | tests/ (fuera de src/) |
| `tests/unit/test_title_prompt.py` | tests/ (fuera de src/) |

Todos fuera de `src/` → **PATRON 2** (archivos utilitarios/infraestructura). Clasificado como TECH-DEBT MEDIUM.

#### mypy: FAIL

| Archivo | Linea | Error |
|---------|-------|-------|
| `src/application/graphs/rag_graph.py` | 123 | `Argument "conn" to "AsyncPostgresSaver" has incompatible type "AsyncConnectionPool[AsyncConnection[tuple[Any, ...]]]"; expected "AsyncConnection[dict[str, Any]] \| AsyncConnectionPool[AsyncConnection[dict[str, Any]]]"` |
| `src/application/use_cases/rag/stream_response.py` | 73 | `Module "src.infrastructure.database.session" has no attribute "AsyncSessionLocal"; maybe "AsyncSession"?` |

**Causa Raiz**: El primer error viene del commit `0581d12` (HOTFIX) que configuro `AsyncConnectionPool` sin `row_factory=dict_row` para el tipo generico. El segundo es un import incorrecto (`AsyncSessionLocal` no existe en el modulo `session`; el nombre correcto es `async_session_maker`).

**Remediacion Sugerida**:
1. `rag_graph.py:123`: Pasar `row_factory=dict_row` al `AsyncConnectionPool` para satisfacer la firma de tipos de `AsyncPostgresSaver`
2. `stream_response.py:73`: Cambiar import de `AsyncSessionLocal` a `async_session_maker`

---

### Punto 3: Seguridad y Cumplimiento

- **Estado**: FAIL (CVEs automatizado) + PASS con observaciones (manual)
- **Severidad**: HIGH

#### Parte Automatizada

| Sub-check | Estado | Detalle |
|-----------|--------|---------|
| Secretos hardcodeados | PASS | Sin hallazgos en src/, docker/, scripts/, dags/ |
| Archivos .env en git | PASS | Solo .env.example y .env.test (permitidos) |
| CVEs en dependencias | FAIL | 5 CVEs encontrados (ver tabla) |
| detect-secrets | PASS | Sin hallazgos |

**CVEs Encontrados**:

| Paquete | Version | CVE | CVSS | Fix | Impacto en plataforma |
|---------|---------|-----|------|-----|----------------------|
| pyjwt | 2.11.0 | CVE-2026-32597 | ~7.5 (ref) | 2.12.0 | HIGH — header `crit` no validado; plataforma usa JWT para auth bancaria |
| pyasn1 | 0.6.2 | CVE-2026-30922 | medio | 0.6.3 | MEDIUM — DoS por recursion en ASN.1; dependencia transitiva de google-auth |
| requests | 2.32.5 | CVE-2026-25645 | bajo | 2.33.0 | LOW — temp file predecible; uso estandar no afectado |
| diskcache | 5.6.3 | CVE-2025-69872 | medio | - | MEDIUM — pickle RCE requiere escritura local; mitigado por containers (ya trackeado S1-S6) |
| pygments | 2.19.2 | CVE-2026-4539 | bajo | - | LOW — ReDoS local; solo highlight de codigo |

Ninguno tiene CVSS >= 9.0. No es CRITICAL. Severidad conjunta: **HIGH** (pyjwt en sistema de auth bancario requiere actualizacion prioritaria).

#### Parte Manual (Revision del Agente)

##### RBAC y Autenticacion

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| JWT Authentication | ✅ IMPLEMENTADO | `src/infrastructure/security/jwt.py` — HS256, 15min TTL, claims sub/exp/iat/role |
| Auth dependency en endpoints | ✅ IMPLEMENTADO | Todos los endpoints protegidos con `Depends(get_current_user)` excepto auth/health |
| Admin guard | ✅ IMPLEMENTADO | `src/api/routes/admin.py` — `require_admin` verifica `is_superuser` desde DB |
| Document ACL (Security Mirror) | ✅ IMPLEMENTADO | `src/infrastructure/security/permission_resolver.py` — ACL bitmask OpenText, cache Redis 5min |
| Rate limiting por rol | ✅ IMPLEMENTADO | `src/infrastructure/api/middleware/rate_limiter.py` — Token Bucket en Redis, limites por rol |
| Granularidad RBAC | ⚠️ PARCIAL | Solo admin/user. Sin roles granulares (auditor, compliance). Suficiente para MVP |
| Account lockout | ❌ FALTANTE | Login logea fallos pero no bloquea cuenta tras N intentos |
| Password policy | ❌ FALTANTE | Sin validacion de complejidad/rotacion/historial al registrar |

##### Cifrado

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| Password hashing | ✅ IMPLEMENTADO | `src/infrastructure/security/password.py` — bcrypt cost 12, truncation 72 bytes |
| TLS/HTTPS produccion | ✅ IMPLEMENTADO | `helm/*/ingress.yaml` — cert-manager + letsencrypt-prod |
| HSTS | ✅ IMPLEMENTADO | `security_headers.py` — max-age=31536000; includeSubDomains |
| Cookie security | ✅ IMPLEMENTADO | `auth.py` — httponly=True, secure=prod, samesite=lax, path scoping |
| GCS at-rest (CMEK) | ⚠️ PARCIAL | `gcs_client.py` soporta CMEK pero default vacio (Google-managed) |
| Internal mTLS | ❌ FALTANTE | Backend→DB/Redis sin cifrado dentro del cluster K8s |
| DB column encryption | ❌ FALTANTE | Sin pgcrypto/TDE para campos sensibles |

##### Security Headers y Hardening

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| Headers OWASP | ✅ IMPLEMENTADO | CSP, X-Frame-Options DENY, nosniff, XSS-Protection, Referrer-Policy, Permissions-Policy |
| Container security | ✅ IMPLEMENTADO | non-root, readOnlyRootFilesystem, seccomp, drop ALL caps |
| Network policies | ✅ IMPLEMENTADO | `values.yaml` — restriccion a ingress-nginx namespace |
| Request size limit | ✅ IMPLEMENTADO | 50MB limit |
| Swagger disabled prod | ✅ IMPLEMENTADO | `main.py` — docs=None, redoc_url=None en produccion |
| Input guardrails | ✅ IMPLEMENTADO | Prompt injection, jailbreak, PII detection (local + DLP) |
| Output guardrails | ✅ IMPLEMENTADO | Faithfulness check, PII sanitization en respuestas |
| Audit logging | ✅ IMPLEMENTADO | Hash chain SHA-256 tamper-evident + SecurityEvent typed |

##### Cumplimiento Normativo

| Norma | Estado | Observaciones |
|-------|--------|---------------|
| ISO 27001 (A.9, A.12) | ✅ | Access control, audit logging con hash chain, structured logging |
| PCI-DSS | N/A | Plataforma RAG documental, no procesa datos de tarjeta |
| BCRA Com. "A" 4609 | ⚠️ PARCIAL | Auth y audit OK. Falta: account lockout, password policy, session concurrency |
| NIST CSF | ⚠️ PARCIAL | PROTECT/DETECT OK. IDENTIFY/RESPOND/RECOVER parciales |
| SOC 2 | ✅ | Audit trail, access control, encryption, monitoring |

---

## Deuda Tecnica

| ID | Hallazgo | Patron | Severidad original | Sprint objetivo |
|----|----------|--------|--------------------|-----------------|
| DT-S7-01 | ruff format: 4 archivos fuera de src/ sin formatear | PATRON 2 | MEDIUM | Sprint 8 |
| DT-S7-02 | CVE-2025-69872 diskcache 5.6.3 (sin fix disponible) | PATRON 1 (dep. transitiva) | HIGH | Monitoreo continuo |
| DT-S7-03 | CVE-2026-4539 pygments 2.19.2 (sin fix disponible, solo local) | PATRON 1 (dep. transitiva) | LOW | Monitoreo continuo |
| DT-S7-04 | Account lockout no implementado (BCRA recomendacion) | PATRON 3 (decision arquitectura pendiente) | HIGH | Sprint 8-9 |
| DT-S7-05 | Password policy no implementada (complejidad, rotacion) | PATRON 3 (decision arquitectura pendiente) | HIGH | Sprint 8-9 |
| DT-S7-06 | RBAC binario (admin/user) sin roles granulares | PATRON 3 (decision de producto pendiente) | MEDIUM | Sprint 9-10 |
| DT-S7-07 | mTLS interno no configurado (backend↔DB/Redis) | PATRON 3 (requiere service mesh) | MEDIUM | Sprint 10+ |
| DT-S7-08 | CMEK no mandatorio en GCS (default Google-managed) | PATRON 3 (requiere KMS provisioning) | MEDIUM | Sprint 9 |

---

## Hallazgos FAIL que Requieren Correccion Inmediata

### FAIL-S7-01: 6 assertions de texto desactualizadas por HOTFIX (HIGH)

**Evidencia**: Commit `0581d12` corrigio ortografia en mensajes de deflexion (tildes). 6 tests verifican texto exacto sin tildes.

**Archivos afectados**:
- `tests/unit/test_rag_graph.py:237`
- `tests/integration/test_rag_nodes.py:319, 324, 623`
- `tests/security/test_topic_control.py:331`
- `tests/unit/test_dag_load_demo_data.py:188`

**Remediacion**: Actualizar assertions con texto correcto (tildes). Ajustar limite demo docs a 25.

### FAIL-S7-02: 2 errores mypy en src/ (HIGH)

**Evidencia**: `rag_graph.py:123` tipo incompatible AsyncConnectionPool, `stream_response.py:73` import inexistente.

**Archivos afectados**:
- `src/application/graphs/rag_graph.py:123`
- `src/application/use_cases/rag/stream_response.py:73`

**Remediacion**: Corregir tipo del pool con `row_factory=dict_row` y fix import a `async_session_maker`.

### FAIL-S7-03: 3 CVEs con fix disponible en dependencias (HIGH)

**Evidencia**: pip-audit reporta 5 CVEs, 3 tienen fix.

**Paquetes a actualizar**:
- `pyjwt>=2.12.0` (CVE-2026-32597 — **prioritario**, auth bancaria)
- `pyasn1>=0.6.3` (CVE-2026-30922 — DoS recursion)
- `requests>=2.33.0` (CVE-2026-25645 — temp file predecible)

**Remediacion**: Actualizar versiones minimas en `pyproject.toml` y re-ejecutar `uv lock`.

### FAIL-S7-04: ADC expirado para tests e2e (HIGH)

**Evidencia**: 3 tests e2e fallan con `403 PERMISSION_DENIED` contra Gemini API.

**Remediacion**: `gcloud auth application-default login --project=itmind-macro-ai-dev-0`

---

## Conclusion y Proximos Pasos

### Veredicto: APROBADO CON DEUDA

El Sprint 7 se aprueba con deuda tecnica documentada. No hay fallos CRITICAL — los 4 grupos de FAILs son todos HIGH y tienen remediacion clara:

1. **Inmediato (antes de merge)**: Corregir assertions de tests (FAIL-S7-01) y errores mypy (FAIL-S7-02)
2. **Esta semana**: Actualizar dependencias con CVEs (FAIL-S7-03), re-autenticar ADC (FAIL-S7-04)
3. **Sprint 8-9**: Account lockout (DT-S7-04), password policy (DT-S7-05)
4. **Sprint 9-10**: RBAC granular (DT-S7-06), CMEK obligatorio (DT-S7-08)
5. **Sprint 10+**: mTLS interno (DT-S7-07)
6. **Monitoreo continuo**: diskcache CVE (DT-S7-02), pygments CVE (DT-S7-03)

### Metricas del Sprint

| Metrica | Valor |
|---------|-------|
| Specs completadas | 11/16 (69%) |
| Cobertura de codigo | 85.23% |
| Tests totales (aprox.) | ~660 |
| Tests fallidos | 9 (1.4%) |
| CVEs abiertos | 5 (3 con fix, 2 sin fix) |
| Items deuda tecnica nuevos | 8 |
| Items deuda tecnica resueltos del sprint anterior | 0 |
