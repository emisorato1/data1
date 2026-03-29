# Registro Consolidado de Deuda Tecnica

Documento que consolida las acciones pendientes identificadas en los reportes de auditoria de cada sprint.
Solo incluye items **no resueltos**. Los items resueltos estan marcados en cada reporte de sprint individual.

**Ultima actualizacion**: 2026-03-25 (Sprint 7 — 8 items nuevos, ADC e2e regresion)

---

## Deuda Activa

### CVE-2025-69872 en diskcache 5.6.3 (DT-S7-02)

- **Severidad**: HIGH
- **Estado**: MONITOREO
- **Sprints afectados**: S1, S2, S3, S4, S5, S6, S7
- **Descripcion**: Dependencia transitiva de `ragas`/`instructor`. Usa Python pickle para serializacion; atacante con acceso de escritura al directorio de cache puede lograr ejecucion de codigo arbitrario. Sin version parcheada disponible (5.6.3 es la ultima al 2026-03-25).
- **Mitigacion**: Entorno containerizado (Docker/K8s) con volumenes controlados reduce riesgo. Documentado en `pyproject.toml:40-41`.
- **Accion**: Monitorear por diskcache >= 5.6.4 y actualizar cuando disponible.

---

### CVE-2026-4539 en pygments 2.19.2 (DT-S7-03)

- **Severidad**: LOW
- **Estado**: MONITOREO
- **Sprints afectados**: S7
- **Descripcion**: ReDoS en `AdlLexer` de pygments. Requiere acceso local. Dependencia transitiva de herramientas de highlighting. Sin fix disponible.
- **Mitigacion**: Solo explotable con acceso local; no se usa para procesar input de usuarios.
- **Accion**: Monitorear por pygments >= 2.19.3.

---

### Account lockout no implementado (DT-S7-04)

- **Severidad**: HIGH
- **Estado**: PENDIENTE
- **Sprints afectados**: S7
- **Descripcion**: El login logea intentos fallidos pero no bloquea la cuenta tras N intentos consecutivos. Recomendacion BCRA Com. "A" 4609.
- **Bloqueante**: Decision arquitectura — definir umbral (ej. 5 intentos), duracion de bloqueo, y mecanismo (Redis counter vs DB column).
- **Accion**: Implementar en Sprint 8-9. Patron TECH-DEBT 3 (bloqueante externo: decision de arquitectura pendiente).

---

### Password policy no implementada (DT-S7-05)

- **Severidad**: HIGH
- **Estado**: PENDIENTE
- **Sprints afectados**: S7
- **Descripcion**: Sin validacion de complejidad (min longitud, mayusculas, numeros, especiales), rotacion periodica ni historial de passwords. Bcrypt hashea correctamente pero acepta passwords debiles.
- **Bloqueante**: Decision de producto — definir requisitos de complejidad alineados con BCRA y politica interna del banco.
- **Accion**: Implementar en Sprint 8-9. Patron TECH-DEBT 3.

---

### RBAC binario sin roles granulares (DT-S7-06)

- **Severidad**: MEDIUM
- **Estado**: PENDIENTE
- **Sprints afectados**: S7
- **Descripcion**: Solo existe admin/user. Sin roles como auditor, compliance, document_manager. El JWT lleva claim `role` pero no se usa para autorizacion granular en endpoints.
- **Bloqueante**: Decision de producto — definir matriz de roles y permisos requeridos.
- **Accion**: Disenar en Sprint 9-10. Patron TECH-DEBT 3.

---

### mTLS interno no configurado (DT-S7-07)

- **Severidad**: MEDIUM
- **Estado**: PENDIENTE
- **Sprints afectados**: S7
- **Descripcion**: Trafico backend→PostgreSQL y backend→Redis dentro del cluster K8s sin cifrar. TLS solo en ingress (terminacion en nginx).
- **Bloqueante**: Requiere service mesh (Istio/Linkerd) o configuracion TLS en cada servicio.
- **Accion**: Evaluar en Sprint 10+. Patron TECH-DEBT 3.

---

### CMEK no mandatorio en GCS (DT-S7-08)

- **Severidad**: MEDIUM
- **Estado**: PENDIENTE
- **Sprints afectados**: S7
- **Descripcion**: `gcs_kms_key_name` default vacio usa Google-managed encryption. Para compliance bancario, CMEK deberia ser obligatorio.
- **Bloqueante**: Requiere provisioning de KMS key en GCP y decision de equipo infra.
- **Accion**: Coordinar con infra para Sprint 9. Patron TECH-DEBT 3.

---

### xECM sync bloqueado (T3-S5-02)

## Items Resueltos (2026-03-12)

Referencia rapida de lo que se resolvio. Detalle completo en cada reporte de sprint.

| Item | Sprints | Resolucion |
|------|---------|------------|
| Tests DAG RAGAS (`airflow.models` faltante) | S1-S6 | `pytest.importorskip("airflow.models")` en `test_dag_ragas.py` |
| Falso positivo regex security scan | S1, S2 | Filtro `\$[A-Z_]` en `run_security_scan.sh` |
| LLM classifier deshabilitado en guardrail | S2 | `enable_llm` ahora es automatico segun environment en `validate_input.py` |
| ACs sin marcar en specs T3-S2-01, T2-S5-02, T2-S5-03 | S2, S5 | Checkboxes marcados como `[x]` |
| Errores ruff en scripts utilitarios | S5, S6 | Per-file-ignores en `pyproject.toml` + auto-fix |
| `database_url`/`redis_url` como `str` | S5 | Migrados a `SecretStr` con `.get_secret_value()` |
| Errores ruff + mypy en `src/` | S6 | Ya pasaban antes de esta sesion (corregidos previamente) |
| Placeholder auth en `admin.py` | S6 | Ya corregido previamente — `require_admin()` con JWT real |
| langgraph CVE | S6 | Ya corregido previamente — `pyproject.toml` tiene `>=1.0.10` |
| Ruff format en `scripts/generate_pdf.py` | S3 | `ruff format` aplicado (2026-03-12) |
| Regresion SecretStr en fixtures tests integration/e2e | S3 | `.get_secret_value()` agregado en 2 fixtures (2026-03-12) |
| Regex CUIT permisivo en output guardrail | S4 | Regex corregido a `(?:\d{2}-\d{8}-\d|\d{11})` + test agregado (2026-03-12) |
| Network policies deshabilitadas en Helm | S4 | `networkPolicy.enabled: true` en `values.yaml` (2026-03-12) |
| Headers OWASP incompletos (Referrer-Policy, Permissions-Policy) | S5 | Headers agregados en `security_headers.py` (2026-03-12) |
| ACs sin marcar en specs T3-S6-01 y T3-S6-02 | S6 | Checkboxes marcados como `[x]` (2026-03-13) |
| ef_search f-string en `retrieve.py` | S6 | Parametrizado con `:ef_search` binding (2026-03-13) |
| PII Sanitizer standalone (DT-S6-01 / T4-S6-02) | S6 | `pii_sanitizer.py` + `dlp_client.py` creados, integrados en `memory_service.py`, 55 tests nuevos, mypy/ruff clean (2026-03-13) |
| Tests e2e 403 PERMISSION_DENIED (Gemini API) | S3-S6 | Causa raiz: ADC no configurado + diagnostico incorrecto "API deshabilitada". Real: `USE_VERTEX_AI=true` en `.env` ya apuntaba a Vertex AI (habilitada). Resuelto con `gcloud auth application-default login --project=itmind-macro-ai-dev-0`. Los 3 tests pasan (2026-03-13) |

## Regresiones detectadas en S7

| Item | Sprint original | Estado S7 |
|------|-----------------|-----------|
| Tests e2e 403 PERMISSION_DENIED | Resuelto S6 | **REGRESION** — ADC expiro nuevamente. Re-ejecutar `gcloud auth application-default login --project=itmind-macro-ai-dev-0` |
| ruff format archivos fuera de src/ | Resuelto S5-S6 (parcial) | **REGRESION** — 4 archivos nuevos sin formatear (dags/, scripts/, tests/) |
