# Guia de Auditoria de Sprints -- Enterprise AI Platform

> Guia operativa para ejecutar auditorias de sprint usando la skill `audit-sprint-checklist` y los scripts en `scripts/audit/`.

---

## Que es la auditoria de sprint

Una auditoria de sprint es una verificacion sistematica de 3 puntos de calidad que se ejecuta al final de cada sprint (o antes de un merge/release). Su objetivo es garantizar que el codigo cumple con los estandares de calidad, testing y cumplimiento normativo del proyecto.

### Resultado

La auditoria produce un reporte Markdown con estado **APROBADO** o **RECHAZADO** para el sprint, con detalle de cada punto evaluado.

---

## Prerequisitos

### Herramientas obligatorias
- **Python 3.12+** con **uv** como gestor de paquetes
- **Git** (para verificar archivos committeados)

### Herramientas opcionales (mejoran la auditoria)
- **Docker** (para tests de integracion y e2e con testcontainers). Si Docker no esta disponible, los sub-checks de integracion y e2e se marcan SKIP (no FAIL).

### Verificar prerequisitos
```bash
uv --version          # Debe retornar version de uv
python --version      # Debe ser 3.12+
git status            # Debe estar en el repo
docker info           # Opcional: solo necesario para tests integration/e2e
```

---

## Como ejecutar la auditoria

### Opcion 1: Via agente IA (recomendada)

Simplemente pedir al agente:

```
Carga la skill audit-sprint-checklist y audita el [SPRINT_N].
0. Ten encuenta que ahora hay un archivo llamado "deuda-tecnica.md" que se debe leer al comenzar la auditoria y modificar al terminar la auditoria.
1. Ejecuta `uv sync && uv sync --extra test` para sincronizar dependencias.
2. Levanta los servicios necesarios con Docker si esta disponible.
3. Ejecuta `bash scripts/audit/run_full_audit.sh` para cubrir los 3 puntos automatizados.
4. Lee los specs del sprint en `specs/[SPRINT_N]/` y completa la revision manual del punto 3 (cifrado, RBAC).
5. Genera el reporte completo en Markdown con el template de SKILL.md.
6. Si hay FAILs, ofreceme como corregirlos.
7. Responde siempre en espanol.
```



### Opcion 2: Ejecucion manual

#### Paso 0: Sincronizar dependencias y levantar servicios

```bash
# Sincronizar dependencias del proyecto
uv sync
uv sync --extra test

# Levantar servicios necesarios para tests de integracion y e2e (opcional)
docker compose up -d db redis
# Esperar a que los servicios esten listos
docker compose ps
```

Si Docker no esta disponible, los tests de integracion y e2e se marcaran SKIP automaticamente. El punto puede pasar sin ejecutarlos.

#### Paso 1: Ejecutar auditoria automatizada

```bash
bash scripts/audit/run_full_audit.sh
```

Esto ejecuta en secuencia:
1. `scripts/audit/run_tests.sh` -- Tests unitarios, integracion, e2e + cobertura
2. `scripts/audit/run_linters.sh` -- Ruff check, ruff format, mypy
3. `scripts/audit/run_security_scan.sh` -- Secretos, .env, CVEs, detect-secrets

Los resultados se guardan en `.audit-results/` como JSON:
```
.audit-results/
├── tests.json
├── linters.json
├── security.json
└── full-audit.json
```

#### Paso 2: Revision manual

La parte manual del punto 3 requiere revision humana o del agente:

| Punto | Que revisar | Donde |
|-------|------------|-------|
| 3 (parte manual) | Cifrado, RBAC | Skills `security-pentesting`, `security-mirror` |

#### Paso 3: Generar reporte

Completar el template de reporte con los resultados de ambos pasos. El template esta en la skill: `.opencode/skills/audit-sprint-checklist/SKILL.md` seccion "Generar Reporte".

---

## Los 3 puntos de auditoria

| # | Punto | Tipo | Script |
|---|-------|------|--------|
| 1 | Suite de Tests | Automatizado | `scripts/audit/run_tests.sh` |
| 2 | Linting y Type Checking | Automatizado | `scripts/audit/run_linters.sh` |
| 3 | Seguridad y Cumplimiento | Hibrido (auto + manual) | `scripts/audit/run_security_scan.sh` + revision agente |

### Detalle rapido de cada punto

**1. Suite de Tests**: Primero ejecuta `uv sync && uv sync --extra test`. Luego ejecuta pytest con markers `unit`, `integration`, `e2e`. Si Docker esta disponible, levanta los servicios necesarios (PostgreSQL+pgvector, Redis) para tests de integracion y e2e. Si Docker no esta disponible, integration y e2e se marcan SKIP. Verifica cobertura >= 80%.

**2. Linting y Type Checking**: `ruff check src/` + `ruff format --check .` + `mypy src/` pasan limpio.

**3. Seguridad y Cumplimiento**: Parte automatizada: `run_security_scan.sh` busca secretos hardcodeados, archivos `.env` committeados, CVEs en dependencias y ejecuta detect-secrets. Parte manual: ISO 27001, PCI-DSS, SOC 2, BCRA, NIST cubiertos para el alcance del sprint. Verifica cifrado y RBAC.

---

## Interpretacion de resultados

### Estados posibles
| Estado | Significado |
|--------|-------------|
| **PASS** | El punto cumple con todos los criterios |
| **FAIL** | El punto NO cumple. Tiene severidad asignada |
| **N/A** | No aplica para este sprint (requiere justificacion) |
| **SKIP** | No se pudo ejecutar (ej: Docker no disponible para integration/e2e) |
| **TECH-DEBT** | Hallazgo que encaja en un patron definido (dep opcional, scripts utilitarios, bloqueante externo). No bloquea la aprobacion. Se documenta en la seccion "Deuda Tecnica" del reporte. |

### Severidades de FAIL
| Severidad | Bloquea sprint? | Accion |
|-----------|:---------------:|--------|
| CRITICAL | Si | Corregir antes de merge |
| HIGH | No | Plan de correccion con fecha |
| MEDIUM | No | Registrar en backlog |
| LOW | No | Tech debt, sin urgencia |

### Criterio de aprobacion
- **APROBADO**: 0 FAILs CRITICAL y 0 TECH-DEBT
- **APROBADO CON DEUDA**: 0 FAILs CRITICAL + 1 o mas TECH-DEBT documentados en el reporte
- **RECHAZADO**: 1 o mas FAILs CRITICAL (sin patron TECH-DEBT aplicable)

---

## Proceso de remediacion

Cuando un punto falla:

1. **Revisar el detalle del FAIL** en el reporte (evidencia, causa raiz, archivos afectados)
2. **Aplicar la remediacion sugerida** o pedir al agente que la ejecute
3. **Re-ejecutar el punto especifico** para verificar la correccion:
   - Punto 1: `bash scripts/audit/run_tests.sh`
   - Punto 2: `bash scripts/audit/run_linters.sh`
   - Punto 3 (auto): `bash scripts/audit/run_security_scan.sh`
4. **Re-ejecutar la auditoria completa** para el reporte final

---

## Archivos de referencia

| Archivo | Descripcion |
|---------|-------------|
| `.opencode/skills/audit-sprint-checklist/SKILL.md` | Instrucciones completas de la skill |
| `.opencode/skills/audit-sprint-checklist/references/checklist-completo.md` | Criterios detallados de los 3 puntos |
| `.opencode/skills/audit-sprint-checklist/references/severidad-criterios.md` | Como clasificar severidad |
| `scripts/audit/run_full_audit.sh` | Script orquestador |
| `scripts/audit/run_tests.sh` | Script de tests (punto 1) |
| `scripts/audit/run_linters.sh` | Script de linting (punto 2) |
| `scripts/audit/run_security_scan.sh` | Script de seguridad (punto 3 automatizado) |

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
