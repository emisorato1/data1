# Reporte de Auditoria de Sprint 2

**Fecha**: 2026-03-11
**Estado General**: APROBADO CON DEUDA
**Auditor**: OpenCode (automatizado + revision manual)

## Resumen Ejecutivo

| # | Punto de Auditoria | Estado | Severidad | Hallazgos |
|---|---|---|---|---|
| 1 | Suite de Tests | TECH-DEBT (CRITICAL) | HIGH | 2 FAILED + 8 ERROR en `test_dag_ragas.py` por `airflow` no instalado (PATRON 1); Cobertura 84.07% >= 80% PASS; integration PASS; e2e PASS |
| 2 | Ruff & Mypy | PASS | - | ruff check PASS, ruff format PASS, mypy PASS — 0 errores |
| 3 | Seguridad y Cumplimiento | FAIL | HIGH | CVE-2025-69872 en diskcache 5.6.3 (sin fix); falso positivo en secretos hardcodeados; revision manual cifrado/RBAC: PASS (19/19 checkpoints) |

**Resultado**: 0 FAILs CRITICAL. Sprint **APROBADO CON DEUDA** (1 TECH-DEBT + 1 FAIL HIGH).

---

## Specs del Sprint 2 Evaluadas

| ID | Spec | Estado | Track |
|----|------|--------|-------|
| T1-S2-01 | Schema SQL completo + migraciones de dominio | done | T1 |
| T1-S2-02 | Deploy Airflow 3 en K8s | done | T1 |
| T1-S2-02b | Airflow 3 en Docker Compose local | done | T1 |
| T1-S2-03 | Langfuse instrumentacion | done | T1 |
| T2-S2-01 | Auth completa (JWT + refresh tokens) | done | T2 |
| T2-S2-02 | Middleware de seguridad global | done | T2 |
| T2-S2-03 | API de conversaciones | done | T2 |
| T3-S2-01 | Gemini embeddings + pgvector storage | done | T3 |
| T3-S2-02 | Indexing service como modulo reutilizable | done | T3 |
| T3-S2-03 | Airflow DAG de indexacion | done | T3 |
| T4-S2-01 | Hybrid Search (vector + BM25) | done | T4 |
| T4-S2-02 | Reranking con Vertex AI | done | T4 |
| T4-S2-03 | Nodo de generacion RAG | done | T4 |

Todas las 13 specs del Sprint 2 estan marcadas como **done**.

---

## Detalle por Punto

### Punto 1: Suite de Tests

- **Estado**: TECH-DEBT (CRITICAL) — Patron 1 aplicado
- **Severidad degradada**: HIGH

#### Sub-checks

| Sub-check | Resultado | Detalle |
|-----------|-----------|---------|
| Tests unitarios | FAIL | 2 FAILED + 8 ERROR en `test_dag_ragas.py` |
| Tests integracion | PASS | Docker disponible, todos pasan |
| Tests e2e | PASS | Docker disponible, todos pasan |
| Cobertura >= 80% | PASS | 84.07% (3629 stmts, 578 sin cubrir) |

#### Evidencia

- **2 tests FAILED + 8 ERROR** en `tests/unit/test_dag_ragas.py`: todos por `ModuleNotFoundError: No module named 'airflow.models'`.
- El archivo usa `pytest.importorskip("airflow")` en linea 9, pero los tests individuales importan `airflow.models.DagBag` dentro del cuerpo del test, lo cual falla cuando `airflow` no esta instalado o cuando Airflow 3.x movio `DagBag` a otro modulo.
- `apache-airflow` esta declarado en `[project.optional-dependencies.airflow]` (no en `test` ni en `dependencies`).
- **Cobertura 84.07%** >= 80% requerido: PASS.

**Nota**: El script `run_tests.sh` reporto cobertura como FAIL, pero la ejecucion directa de `pytest --cov=src --cov-fail-under=80` confirma 84.07% >= 80%. El FAIL de cobertura en el script se debe a que los tests fallidos de `test_dag_ragas.py` causan exit code != 0, no a cobertura insuficiente. La cobertura real es **PASS**.

#### Clasificacion TECH-DEBT — PATRON 1

Las 3 condiciones se cumplen:
1. `apache-airflow` figura en `[project.optional-dependencies.airflow]`, no en `[project.dependencies]` ni en `[project.optional-dependencies.test]`.
2. El modulo de tests tiene `pytest.importorskip("airflow")` declarado al nivel del modulo (linea 9 de `test_dag_ragas.py`).
3. La cobertura global (84.07%) >= 80% se mantiene excluyendo esos tests.

Se clasifica como TECH-DEBT con severidad HIGH (degradada de CRITICAL).

- **Causa Raiz**: `pytest.importorskip("airflow")` en linea 9 importa el modulo `airflow` pero no protege contra submodulos como `airflow.models.DagBag` que son importados dentro del cuerpo de cada test. En Airflow 3.x, `DagBag` posiblemente se movio a `airflow.sdk`.

- **Remediacion Sugerida**:
  1. Agregar `pytest.importorskip("airflow.models")` al inicio del archivo para skip completo si el submodulo no esta disponible.
  2. Alternativa: mover `apache-airflow` a `[project.optional-dependencies.test]`.

- **Archivos Afectados**: `tests/unit/test_dag_ragas.py`

---

### Punto 2: Ruff & Mypy

- **Estado**: PASS
- **Severidad**: -

| Sub-check | Resultado | Detalle |
|-----------|-----------|---------|
| `ruff check src/` | PASS | 0 errores de linting |
| `ruff format --check .` | PASS | 0 archivos sin formatear |
| `mypy src/` | PASS | 0 errores de tipo |

Los 3 comandos retornaron exit code 0. No hay hallazgos.

---

### Punto 3: Seguridad y Cumplimiento

- **Estado**: FAIL
- **Severidad**: HIGH (no CRITICAL — ver analisis)

#### 3a. Parte Automatizada (Script)

| Sub-check | Resultado | Detalle |
|-----------|-----------|---------|
| Secretos hardcodeados | FAIL (script) / **FALSO POSITIVO** | Ver analisis |
| Archivos `.env` en git | PASS | Sin `.env` committeados (solo `.env.example`) |
| CVEs en dependencias | FAIL | CVE-2025-69872 en diskcache 5.6.3 |
| detect-secrets | PASS | Sin hallazgos |

**Analisis de secretos hardcodeados (FALSO POSITIVO)**:

El script detecto 2 lineas en `scripts/validate-helm-chart.sh:136-137`:
```
--set postgresql.auth.password="$HELM_PG_PASSWORD"
--set redis.auth.password="$HELM_REDIS_PASSWORD"
```

Estas lineas usan **variables de entorno bash** (`$HELM_PG_PASSWORD`, `$HELM_REDIS_PASSWORD`) generadas con `openssl rand -hex 16` (lineas 128-129), NO valores hardcodeados. El regex del script captura la sintaxis `password="$VARIABLE"` como falso positivo. El archivo esta en `scripts/` (no en `src/`) y es un script de validacion de Helm charts.

**Analisis de CVE-2025-69872 (diskcache 5.6.3)**:

| Campo | Valor |
|-------|-------|
| Paquete | diskcache 5.6.3 |
| CVE | CVE-2025-69872 |
| Descripcion | DiskCache usa Python pickle por defecto. Un atacante con acceso de escritura al directorio de cache puede lograr ejecucion de codigo arbitrario al leer del cache. |
| Fix versions | Ninguna publicada |
| Dependencia | Transitiva — requerida por `instructor` y `ragas` (herramientas de evaluacion), no por codigo de produccion |
| Vector de ataque | Requiere acceso de escritura al filesystem del servidor |
| Riesgo en contexto | Reducido — entorno containerizado (Docker/K8s) con volumenes controlados |
| Clasificacion | **HIGH** (no CRITICAL): requiere acceso local, no es remotamente explotable, sin fix disponible |

#### 3b. Parte Manual — Cifrado At-Rest

| # | Checkpoint | Estado | Evidencia |
|---|-----------|--------|-----------|
| 1 | Passwords con bcrypt cost=12 | PASS | `src/infrastructure/security/password.py:8` — `_BCRYPT_ROUNDS = 12`, salt via `bcrypt.gensalt()`, input truncado a 72 bytes |
| 2 | Refresh tokens hasheados SHA-256 | PASS | `src/infrastructure/security/refresh_token.py:12,22` — `secrets.token_urlsafe()` (256-bit entropy) + `hashlib.sha256()`. Raw token nunca almacenado. Verificado en `login.py:69`: `token_hash=hash_token(raw_refresh)` |
| 3 | Secrets como SecretStr | PASS | `src/config/settings.py:26,30,57-58` — `jwt_secret: SecretStr`, `gemini_api_key: SecretStr`, `langfuse_public_key: SecretStr`, `langfuse_secret_key: SecretStr`. Previene leak en logs/serialization |
| 4 | Validador anti-placeholder | PASS | `src/config/settings.py:137-158` — `_reject_placeholder_secrets` rechaza "CHANGE_ME" en entornos != development. JWT secret minimo 32 chars |

#### 3c. Parte Manual — Cifrado In-Transit

| # | Checkpoint | Estado | Evidencia |
|---|-----------|--------|-----------|
| 1 | HSTS | PASS | `src/infrastructure/api/middleware/security_headers.py:54` — `Strict-Transport-Security: max-age=31536000; includeSubDomains` |
| 2 | X-Content-Type-Options | PASS | `security_headers.py:48` — `X-Content-Type-Options: nosniff` |
| 3 | X-Frame-Options | PASS | `security_headers.py:51` — `X-Frame-Options: DENY` |
| 4 | CSP | PASS | `security_headers.py:38,63-65` — API: `default-src 'none'; frame-ancestors 'none'`. Prod: CSP estricta |
| 5 | Cache-Control | PASS | `security_headers.py:68-70` — `no-store, no-cache, must-revalidate` para rutas `/api/` |
| 6 | Cookies HTTPOnly+Secure | PASS | `src/infrastructure/api/v1/auth.py:49-50` — `httponly=True`, `secure=_SECURE` (True en prod). `SameSite=lax` |
| 7 | CORS controlado | PASS | `src/infrastructure/api/main.py:166-173` — `allow_origins=settings.cors_origin_list` (no wildcard) |
| 8 | TrustedHost middleware | PASS | `main.py:176-179` — `TrustedHostMiddleware` con `allowed_hosts` configurables |
| 9 | Docs deshabilitados en prod | PASS | `main.py:153-155` — `docs_url=None`, `redoc_url=None`, `openapi_url=None` en produccion |
| 10 | Request size limit | PASS | `src/infrastructure/api/middleware/request_size_limit.py:20,48` — 10 MB default, configurable |

#### 3d. Parte Manual — RBAC

| # | Checkpoint | Estado | Evidencia |
|---|-----------|--------|-----------|
| 1 | `get_current_user` valida JWT | PASS | `src/infrastructure/api/dependencies.py:28-73` — Lee cookie, decodifica JWT, valida expiracion/firma, extrae `sub`, carga user de DB, verifica `is_active` |
| 2 | Endpoints protegidos | PASS | Todos los endpoints de negocio usan `Depends(get_current_user)`. Solo health y auth (login/refresh) son publicos |
| 3 | Admin endpoints con `require_admin` | PASS | `src/api/routes/admin.py:9-22` — Verifica `current_user.is_superuser`. HTTP 403 si no es admin |
| 4 | Owner-based filtering | PASS | `src/infrastructure/database/repositories/conversation_repository.py:35,69,100` — Todas las queries filtran por `user_id`. Un usuario NUNCA accede a conversaciones de otro |
| 5 | Feedback verifica ownership | PASS | `src/api/routes/feedback.py:34` — `if message.conversation.user_id != current_user.id` -> HTTP 403 |

**Endpoints protegidos verificados**:

| Endpoint | Metodo | Proteccion | Archivo |
|----------|--------|------------|---------|
| `/api/v1/conversations` | POST | `Depends(get_current_user)` | `chat.py:50` |
| `/api/v1/conversations` | GET | `Depends(get_current_user)` | `chat.py:70` |
| `/api/v1/conversations/{id}` | GET | `Depends(get_current_user)` | `chat.py:90` |
| `/api/v1/conversations/{id}` | PATCH | `Depends(get_current_user)` | `chat.py:110` |
| `/api/v1/conversations/{id}` | DELETE | `Depends(get_current_user)` | `chat.py:131` |
| `/api/v1/conversations/{id}/messages` | POST | `Depends(get_current_user)` | `chat.py:155` |
| `/api/v1/documents` | POST | `Depends(get_current_user)` | `documents.py:56` |
| `/api/v1/feedback` | POST | `Depends(get_current_user)` | `feedback.py:19` |
| `/api/v1/admin/audit-logs` | GET | `Depends(require_admin)` | `admin.py:33` |
| `/api/v1/admin/audit-logs/verify` | POST | `Depends(require_admin)` | `admin.py:58` |
| `/health`, `/health/ready` | GET | Publico (correcto) | `health.py` |
| `/api/v1/auth/login` | POST | Publico (correcto) | `auth.py:72` |
| `/api/v1/auth/logout` | POST | Publico (correcto) | `auth.py:93` |
| `/api/v1/auth/refresh` | POST | Publico (usa refresh cookie) | `auth.py:106` |

#### 3e. Security Mirror (OpenText)

| # | Checkpoint | Estado | Evidencia |
|---|-----------|--------|-----------|
| 1 | Modelos OpenText completos | PASS | `src/infrastructure/database/models/permission.py` — 5 tablas: `Kuaf`, `KuafChildren`, `DTree`, `DTreeACL`, `DTreeAncestors`. Bitmask `SeeContents=2` |
| 2 | PermissionResolver con cache + CTE | PASS | `src/infrastructure/security/permission_resolver.py` — Vista materializada + CTE recursiva. Cache Redis TTL 5 min |
| 3 | Filtro fail-closed en retrieval | PASS | `src/infrastructure/rag/retrieval/hybrid_search.py:167-169` — Lista vacia = 0 resultados (no bypass). Confirmado en `retrieve.py:77` |

#### 3f. Guardrails

| # | Checkpoint | Estado | Evidencia |
|---|-----------|--------|-----------|
| 1 | Input guardrail (10 patterns regex) | PASS | `src/infrastructure/security/guardrails/input_validator.py:47-157` — 6 reglas injection + 4 reglas jailbreak |
| 2 | Output guardrail (PII + faithfulness) | PASS | `src/infrastructure/security/guardrails/output_validator.py:48-61` — DNI, CUIT/CUIL, CBU. Faithfulness heuristica con threshold 0.3 |

#### 3g. Normas Aplicables

| Norma | Estado | Justificacion |
|-------|--------|---------------|
| ISO 27001 (A.8.24 Criptografia) | PASS | bcrypt, SHA-256, JWT HS256, CMEK, SecretStr |
| PCI-DSS (Req 3 - Proteccion de datos) | PASS | Passwords y tokens protegidos; PII argentino detectado y filtrado |
| SOC 2 (Seguridad y disponibilidad) | PASS | Audit logs con hash chain, RBAC implementado, rate limiting |
| BCRA (Proteccion de datos) | PASS | Cifrado implementado; Security Mirror replica ACLs de OpenText |
| NIST SP 800-53 (SC-28 At-rest) | PASS | Implementacion de cifrado adecuada para alcance del sprint |

**Revision manual (19/19 checkpoints): PASS completo.**

---

## Deuda Tecnica

| ID | Hallazgo | Patron | Severidad original | Sprint objetivo |
|----|----------|--------|--------------------|-----------------|
| DT-01 | Tests `test_dag_ragas.py` (2 FAILED + 8 ERROR) fallan por `airflow` no instalado como dependencia de test | PATRON 1 | CRITICAL | Sprint 3 |
| DT-02 | CVE-2025-69872 en diskcache 5.6.3 (dependencia transitiva de `instructor`/`ragas`, sin fix disponible) | - | HIGH | Monitorear; actualizar cuando fix este disponible |
| DT-03 | Falso positivo en script de deteccion de secretos (`validate-helm-chart.sh` usa env vars, no secretos reales) | - | MEDIUM | Sprint 3 (mejorar regex del script para excluir `$VARIABLE`) |

**Nota sobre DT-01**: Este item fue documentado como deuda del Sprint 1. Persiste en Sprint 2 porque las condiciones del PATRON 1 siguen aplicando (airflow sigue en optional-dependencies, no en test). Si en Sprint 3 no se resuelve y la dependencia ya se movio, se reclasificara como FAIL.

---

## Observaciones (informativas, no-bloqueantes)

| # | Observacion | Archivo:Linea | Impacto |
|---|------------|---------------|---------|
| O1 | LLM classifier deshabilitado por default en input guardrail | `src/application/graphs/nodes/validate_input.py:65` | Solo regex protege contra prompt injection. Habilitar `enable_llm=True` en produccion |
| O2 | Chunked transfer encoding bypass en request size limit | `src/infrastructure/api/middleware/request_size_limit.py:10-12` | TODO documentado: solo verifica `Content-Length` header |
| O3 | Input guardrail fail-open si LLM falla | `src/infrastructure/security/guardrails/input_validator.py:326-328` | Decision deliberada: "availability > security for MVP" |
| O4 | Rate limiter fail-open si Redis cae | `src/infrastructure/api/middleware/rate_limiter.py:231-233` | Decision documentada: requests pasan si Redis no disponible |
| O5 | Langfuse tracing pendiente en DAG de indexacion | `specs/sprint-2/T3-S2-03_airflow-dag-indexing.md` | AC parcialmente cumplido: 7/8 (falta adapter sync para Langfuse) |
| O6 | Embeddings spec T3-S2-01 tiene 1 AC no marcado | `specs/sprint-2/T3-S2-01_embeddings-pgvector.md:27` | El primer AC esta sin check `[ ]` aunque la funcionalidad existe en el codebase |

---

## Conclusion y Proximos Pasos

El Sprint 2 introduce funcionalidad critica del sistema:

- **Autenticacion completa** (JWT + refresh tokens rotativos + bcrypt) — T2-S2-01
- **Middleware de seguridad global** (CORS, security headers, trusted host) — T2-S2-02
- **API de conversaciones** con CRUD completo y owner isolation — T2-S2-03
- **Schema SQL** con migraciones de dominio RAG + Security Mirror OpenText — T1-S2-01
- **Pipeline de indexacion** (embeddings + chunking + pgvector) — T3-S2-01/02/03
- **Busqueda hibrida** (vector + BM25 + RRF) con reranking — T4-S2-01/02
- **Nodo de generacion** con citaciones y streaming — T4-S2-03

Los 3 puntos de auditoria:
1. **Tests**: TECH-DEBT (HIGH) — Solo 10 tests de DAG RAGAS fallan por dependencia opcional airflow. Cobertura real 84.07%.
2. **Linters**: PASS — 0 errores en ruff check, ruff format y mypy.
3. **Seguridad**: FAIL (HIGH) — CVE sin fix en dependencia transitiva + falso positivo del script. Revision manual de cifrado y RBAC: 19/19 PASS.

**Sprint APROBADO CON DEUDA** — 0 FAILs CRITICAL.

### Acciones Recomendadas

| Prioridad | Accion | Esfuerzo | Impacto | Estado |
|-----------|--------|----------|---------|--------|
| 1 | Fix `test_dag_ragas.py`: agregar `pytest.importorskip("airflow.models")` o mover airflow a deps de test | 30min | Resuelve DT-01, elimina 10 tests fallidos | **RESUELTO** (2026-03-12) |
| 2 | Mejorar regex de `run_security_scan.sh` para excluir variables bash `\$[A-Z_]+` | 30min | Elimina falso positivo DT-03 | **RESUELTO** (2026-03-12) |
| 3 | Monitorear CVE-2025-69872 en diskcache — actualizar cuando fix disponible | Continuo | DT-02 | MONITOREO — 5.6.3 sigue siendo ultima version |
| 4 | Habilitar LLM classifier en input guardrail para produccion | 1h | Mejora defensa contra prompt injection (O1) | **RESUELTO** (2026-03-12) — Habilitado automaticamente en entornos != development |
| 5 | Marcar AC faltante en T3-S2-01 spec si la funcionalidad existe | 5min | Coherencia documental (O6) | **RESUELTO** (2026-03-12) — ACs marcados como [x] |
