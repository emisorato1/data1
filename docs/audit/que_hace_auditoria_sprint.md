# Que Hace la Auditoria de Sprint -- Analisis Exhaustivo

> Analisis detallado de los 3 puntos de auditoria tal como estan definidos en la guia
> (`docs/audit/GUIA-AUDITORIA-SPRINTS.md`), la skill `audit-sprint-checklist` (SKILL.md),
> el checklist completo (`.opencode/skills/audit-sprint-checklist/references/checklist-completo.md`),
> los criterios de severidad (`.opencode/skills/audit-sprint-checklist/references/severidad-criterios.md`)
> y los 4 scripts de automatizacion (`scripts/audit/run_*.sh`).
>
> Objetivo: documentar con precision que verifica cada punto, como lo verifica
> y contra que fuentes de verdad lo cruza.

---

## Estructura General de la Auditoria

### Fuentes de verdad que componen la auditoria

| Fuente | Ubicacion | Rol |
|--------|-----------|-----|
| Guia operativa | `docs/audit/GUIA-AUDITORIA-SPRINTS.md` | Instrucciones de ejecucion paso a paso |
| Skill del agente | `.opencode/skills/audit-sprint-checklist/SKILL.md` | Reglas de ejecucion + definicion de los 3 puntos |
| Checklist completo | `.opencode/skills/audit-sprint-checklist/references/checklist-completo.md` | Criterios PASS/FAIL detallados por punto |
| Criterios de severidad | `.opencode/skills/audit-sprint-checklist/references/severidad-criterios.md` | Clasificacion CRITICAL/HIGH/MEDIUM/LOW |
| Script tests | `scripts/audit/run_tests.sh` | Automatiza punto 1 |
| Script linters | `scripts/audit/run_linters.sh` | Automatiza punto 2 |
| Script security | `scripts/audit/run_security_scan.sh` | Automatiza parte del punto 3 |
| Script orquestador | `scripts/audit/run_full_audit.sh` | Ejecuta los 3 scripts en secuencia |

### Reglas de ejecucion

La skill define 8 reglas que el agente auditor DEBE cumplir sin excepcion:

1. **NUNCA suavizar resultados**: FAIL es FAIL. No existe "parcialmente cumple".
2. **NUNCA omitir verificaciones**: Los 3 puntos se evaluan siempre. N/A requiere justificacion.
3. **NUNCA dar puntajes parciales**: Cada punto es binario: PASS o FAIL.
4. **Script = fuente de verdad**: Para puntos 1, 2 y la parte automatizada del 3, el resultado del script es definitivo. El agente NO puede sobreescribirlo.
5. **Sin excepciones subjetivas**: No se acepta "funciona pero no tiene tests" ni "lo arreglaremos despues". La unica via para no marcar algo como FAIL es que aplique un patron TECH-DEBT definido en `.opencode/skills/audit-sprint-checklist/references/severidad-criterios.md`.
6. **Severidad obligatoria**: Cada FAIL se clasifica como CRITICAL, HIGH, MEDIUM o LOW.
7. **Bloqueo por CRITICAL**: 1+ FAIL CRITICAL = sprint RECHAZADO. No negociable.
8. **TECH-DEBT es una clasificacion, no una excusa**: Si un hallazgo encaja en uno de los 3 patrones TECH-DEBT definidos en `.opencode/skills/audit-sprint-checklist/references/severidad-criterios.md`, se clasifica como TECH-DEBT y se documenta. El sprint puede aprobarse con TECH-DEBT. Sin patron aplicable = FAIL.

### Clasificacion de tipos

| Tipo | Puntos | Descripcion |
|------|--------|-------------|
| Automatizado | 1, 2 | Ejecutados por scripts bash. El resultado del script es la fuente de verdad. |
| Hibrido | 3 | Parte automatizada (script security scan) + parte manual (cifrado, RBAC, revision agente). |

### Criterio de aprobacion del sprint

- **APROBADO**: 0 FAILs CRITICAL y 0 TECH-DEBT
- **APROBADO CON DEUDA**: 0 FAILs CRITICAL + 1 o mas TECH-DEBT documentados en el reporte
- **RECHAZADO**: 1 o mas FAILs CRITICAL (sin patron TECH-DEBT aplicable)

### Severidades

| Severidad | Bloquea Sprint? | Timeline de Correccion | Accion |
|-----------|:---------------:|----------------------|--------|
| CRITICAL | Si | Inmediato (antes de merge) | Corregir ahora |
| HIGH | No | Sprint actual o siguiente | Plan con fecha |
| MEDIUM | No | 1-2 sprints | Registrar en backlog |
| LOW | No | Sin urgencia | Tech debt |
| TECH-DEBT | No | Sprint objetivo definido en reporte | Documentar con patron aplicable |

---

## Los 3 Puntos de Auditoria -- Detalle Exhaustivo

---

### PUNTO 1: Suite de Tests

- **Categoria**: A - Calidad de Codigo y Testing
- **Tipo**: Automatizado
- **Script**: `scripts/audit/run_tests.sh`
- **Severidad tipica**: CRITICAL

#### Pre-requisitos

Antes de ejecutar los tests, se debe preparar el entorno:

```bash
# Sincronizar dependencias del proyecto
uv sync
uv sync --extra test
```

Esto garantiza que todas las dependencias de produccion y de testing estan instaladas y sincronizadas.

#### Levantamiento de servicios Docker

Los tests de integracion y e2e requieren servicios externos (PostgreSQL+pgvector, Redis). Si Docker esta disponible, se levantan automaticamente:

```bash
docker compose up -d db redis
```

Si Docker **no** esta disponible, los sub-checks de integracion y e2e se marcan **SKIP** (no FAIL), y el punto puede pasar sin ejecutarlos. Esto permite ejecutar la auditoria en entornos sin Docker (como CI ligero o maquinas de desarrollo sin Docker instalado).

```
Docker disponible:     unit + integration + e2e + coverage
Docker NO disponible:  unit + coverage (integration=SKIP, e2e=SKIP)
```

#### Que ejecuta el script exactamente

| Sub-check | Comando | Criterio PASS |
|-----------|---------|--------------|
| Tests unitarios | `uv run pytest -m unit --tb=short -q` | Exit code 0 |
| Tests integracion | `uv run pytest -m integration --tb=short -q` | Exit code 0 (requiere Docker/testcontainers) |
| Tests e2e | `uv run pytest -m e2e --tb=short -q` | Exit code 0 (requiere Docker) |
| Cobertura | `uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80` | >= 80% sobre `src/` |

#### Criterios adicionales del checklist (no automatizados)

- No hay `@pytest.mark.skip` sin `reason=` (skip sin justificacion)
- No hay `xfail` sin ticket asociado
- Archivos nuevos en `src/` tienen tests correspondientes en `tests/`

#### Fuentes que verifica

- `tests/unit/` -- tests sin I/O (capa domain)
- `tests/integration/` -- tests con DB/Redis via testcontainers (capa infrastructure)
- `tests/e2e/` -- tests de API completa (todas las capas)
- `tests/security/` -- tests de guardrails y permisos
- `tests/conftest.py` -- fixtures globales
- `pyproject.toml` [tool.pytest.ini_options] -- configuracion de markers
- `pyproject.toml` [tool.coverage.*] -- configuracion de cobertura

#### Como verifica alineacion con la arquitectura

La separacion de tests por markers (`unit`, `integration`, `e2e`) refleja las 3 capas de la
arquitectura hexagonal:
- `unit` = domain (sin I/O, puro Python)
- `integration` = infrastructure (con DB real via testcontainers)
- `e2e` = API completa (FastAPI + todos los servicios)

La cobertura sobre `src/` abarca domain + application + infrastructure.

#### Como verifica alineacion con la infraestructura

Tests de integracion y e2e requieren Docker, lo cual refleja el stack de produccion
(PostgreSQL+pgvector, Redis). Si Docker no esta disponible, los sub-checks se
marcan SKIP (no FAIL), y el punto puede pasar sin ejecutarlos. Cuando Docker esta
disponible, se levantan los servicios necesarios con `docker compose up -d db redis`
antes de ejecutar los tests.

#### Como verifica alineacion con los specs

No cruza directamente contra specs. Solo ejecuta los tests existentes.

#### Criterios de severidad para este punto

| Situacion | Severidad |
|-----------|-----------|
| Tests core fallan (la app no se puede verificar) | CRITICAL |
| Tests fallan por dependencia opcional no instalada (PATRON 1) | TECH-DEBT (HIGH) |
| Cobertura < 80% pero > 60% | HIGH |
| Tests existentes pero podrian mejorar edge cases | LOW |

---

### PUNTO 2: Linting y Type Checking

- **Categoria**: A - Calidad de Codigo y Testing
- **Tipo**: Automatizado
- **Script**: `scripts/audit/run_linters.sh`
- **Severidad tipica**: HIGH (CRITICAL si hay errores bandit `S`)

#### Que ejecuta el script exactamente

| Sub-check | Comando | Criterio PASS |
|-----------|---------|--------------|
| Linting | `uv run ruff check src/` | Exit code 0 (solo codigo de produccion en src/) |
| Formatting | `uv run ruff format --check .` | Exit code 0 |
| Type checking | `uv run mypy src/` | Exit code 0 |

#### Configuracion de referencia (pyproject.toml)

| Herramienta | Configuracion |
|-------------|--------------|
| Ruff linting | target=py312, line-length=120, rules: E, W, F, I, N, UP, B, A, **S** (bandit/seguridad), T20, SIM, TCH, RUF |
| Ruff format | quote-style=double, indent-style=space, line-length=120 |
| Mypy | python_version=3.12, check_untyped_defs=true, plugin=pydantic.mypy, ignore_missing_imports=true |

#### Como verifica alineacion con la arquitectura

- Mypy valida types en `src/` (domain + application + infrastructure)
- Las reglas S (bandit) detectan patrones de seguridad inseguros en Python
- **Limitacion**: Mypy NO verifica que domain no importe de infrastructure. No valida la
  regla de dependencias hexagonal.

#### Como verifica alineacion con los specs

No cruza contra specs. Verifica que el codigo cumple con la configuracion de calidad
ya definida en `pyproject.toml`.

#### Criterios de severidad para este punto

| Situacion | Severidad |
|-----------|-----------|
| Errores bandit (reglas `S`) -- patrones de seguridad | CRITICAL |
| Errores de mypy en modulos criticos | HIGH |
| Errores de formatting de ruff | MEDIUM |
| Violations de ruff fuera de src/ (scripts/, dags/, debug_*.py) (PATRON 2) | TECH-DEBT (MEDIUM) |
| Warnings menores de linting | LOW |

---

### PUNTO 3: Seguridad y Cumplimiento

- **Categoria**: B - Seguridad y Cumplimiento Normativo
- **Tipo**: Hibrido (automatizado + manual)
- **Script (parte automatizada)**: `scripts/audit/run_security_scan.sh`
- **Severidad tipica**: CRITICAL (secretos/CVEs) o HIGH (gaps normativos)
- **Skills referenciadas**: `security-pentesting`, `security-mirror`

#### Parte A: Escaneo automatizado de seguridad

El script `run_security_scan.sh` ejecuta 4 sub-checks:

| Sub-check | Que busca | Criterio PASS | Si no disponible |
|-----------|-----------|--------------|-----------------|
| Secretos hardcodeados | Patrones regex de passwords, api keys, tokens en `src/`, `docker/`, `scripts/`, `dags/` | Sin hallazgos reales (falsos positivos filtrados) | Siempre ejecutable |
| Archivos `.env` en git | `git ls-files '*.env' '.env*'` excluyendo `.env.example`, `.env.test` | Sin archivos `.env` committeados | Siempre ejecutable |
| CVEs en dependencias | `pip-audit` sobre dependencias instaladas | Sin CVEs conocidos | SKIP (pip-audit no instalado) |
| detect-secrets | `detect-secrets scan` sobre el proyecto | Sin hallazgos | SKIP (detect-secrets no instalado) |

#### Parte B: Revision manual de cumplimiento

| Requisito | Donde buscar | Criterio PASS | Criterio FAIL |
|-----------|-------------|--------------|---------------|
| Cifrado | bcrypt para passwords, TLS en transit | Datos sensibles cifrados at-rest y in-transit | Passwords en texto plano |
| RBAC | `src/infrastructure/security/` | Control de acceso con menor privilegio | Endpoints sin verificacion de permisos |

#### Normas de referencia

| Norma | Aplicabilidad al proyecto |
|-------|--------------------------|
| ISO 27001 | Seguridad de la informacion general |
| PCI-DSS | Datos financieros y transacciones |
| SOC 2 | Controles de seguridad y disponibilidad |
| BCRA | Regulacion bancaria argentina |
| NIST | Framework de ciberseguridad |

#### Como verifica alineacion con la arquitectura

Verifica que los modulos de seguridad existen y funcionan:
- RBAC en infrastructure/security
- Cifrado de datos sensibles (bcrypt para passwords, TLS en transit)
- Ausencia de secretos hardcodeados en el codigo fuente (via script)
- Dependencias sin CVEs conocidos (via pip-audit)

#### Como verifica alineacion con los specs

No cruza contra specs individuales. Las normas son transversales al proyecto.

#### Criterios de severidad para este punto

| Situacion | Severidad |
|-----------|-----------|
| Secretos hardcodeados en codigo | CRITICAL |
| Archivos `.env` committeados en git | CRITICAL |
| CVEs en dependencias (CVSS >= 9.0) | CRITICAL |
| CVEs en dependencias (CVSS < 9.0) | HIGH |
| detect-secrets encuentra hallazgos | HIGH |
| Viola regulacion bancaria directa (BCRA, PCI-DSS) | CRITICAL |
| Gaps menores en documentacion normativa | MEDIUM |

---

## Resumen de Cobertura por Aspecto del Proyecto

| Aspecto | Puntos que lo verifican | Nivel de cobertura | Detalle |
|---------|------------------------|-------------------|---------|
| Tests y calidad de codigo | 1, 2 | FUERTE | Automatizado. Cubre unit/integration/e2e/coverage/linting/typing. |
| Seguridad en codigo | 2 (bandit), 3 (auto) | FUERTE | Las reglas S de ruff + security scan (secretos, CVEs, detect-secrets). |
| Cumplimiento normativo | 3 (manual) | MODERADA | Revision manual. Verifica cifrado y RBAC. |

---

## Ejecucion Completa Paso a Paso

### Paso 0: Preparacion

```bash
# Sincronizar dependencias
uv sync
uv sync --extra test

# Levantar servicios Docker (si disponible)
docker compose up -d db redis
```

### Paso 1: Auditoria automatizada

```bash
bash scripts/audit/run_full_audit.sh
```

Ejecuta puntos 1, 2 y la parte automatizada del 3. Resultados en `.audit-results/`.

### Paso 2: Revision manual del punto 3

Verificar cumplimiento normativo (cifrado, RBAC) contra las skills `security-pentesting` y `security-mirror`.

### Paso 3: Generar reporte

Reporte en `docs/audit/sprint-N-report.md` con template de la skill.

---

## Directorio de resultados

Los scripts generan resultados en `.audit-results/` (gitignored). Estructura:

```
.audit-results/
├── tests.json          # Resultado punto 1
├── linters.json        # Resultado punto 2
├── security.json       # Resultado punto 3 (parte automatizada)
└── full-audit.json     # Consolidado
```

Cada JSON individual tiene esta estructura:
```json
{
  "point": 1,
  "name": "Suite de Tests",
  "status": "PASS",
  "failures": 0,
  "details": {
    "unit": "PASS",
    "integration": "PASS",
    "e2e": "SKIP",
    "coverage": "PASS"
  }
}
```

El `full-audit.json` consolidado tiene esta estructura:
```json
{
  "timestamp": "2026-03-11T12:00:00Z",
  "overall_status": "PASS",
  "total_automated_failures": 0,
  "points": {
    "1_tests": "PASS",
    "2_linters": "PASS",
    "3_security_automated": "PASS"
  },
  "note": "El punto 3 tiene una parte automatizada (este reporte) y una parte manual (cifrado, RBAC) que requiere revision por el agente."
}
```
