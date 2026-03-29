# 4. Solution Strategy

> **arc42 Section 4**: Describe las decisiones fundamentales y estrategias de solución que dan forma a la arquitectura del sistema.
>
> **Referencia**: [arc42 Section 4 — Solution Strategy](https://docs.arc42.org/section-4/)

---

## 4.1 Estrategia del Monorepo

El proyecto es un **monorepo** que contiene backend Python, frontend Next.js, DAGs de Airflow y Helm charts. Dos ecosistemas de dependencias coexisten sin interferencia:

```
enterprise-ai-platform/          (monorepo)
│
├── pyproject.toml                ← UV gestiona ESTO
├── uv.lock                      ← Lock file de Python
├── .python-version               ← Python 3.12
├── src/                          ← Código Python (FastAPI, LangGraph, etc.)
├── dags/                         ← DAGs de Airflow (también Python)
├── tests/                        ← Tests Python
│
├── frontend/                     ← TERRITORIO NODE.JS (UV no lo toca)
│   ├── package.json              ← npm/pnpm gestiona ESTO
│   ├── pnpm-lock.yaml            ← Lock file de Node
│   ├── node_modules/             ← Dependencias Node
│   ├── next.config.js
│   └── app/
│
└── helm/                         ← Sin runtime, solo templates YAML
```

**Regla clave**: `pyproject.toml` gobierna Python. `package.json` gobierna Node. Nunca se cruzan. UV ignora `frontend/`, npm ignora `src/`.

### ¿Por qué un solo pyproject.toml?

Porque el backend Python es un **monolito modular**, no microservicios. Todo el código Python comparte:

- Las mismas dependencias (FastAPI, LangGraph, SQLAlchemy, etc.)
- El mismo virtualenv (`.venv/`)
- Los mismos modelos de dominio
- Las mismas configuraciones de linting/mypy

Si tuviéramos microservicios Python separados, cada uno tendría su propio `pyproject.toml`. Pero ese no es nuestro caso.

---

## 4.2 Monolito Modular: definición y justificación

### ¿Qué es un monolito modular?

Es el punto medio entre un monolito tradicional y microservicios:

```
MONOLITO TRADICIONAL          MONOLITO MODULAR              MICROSERVICIOS
(todo mezclado)               (NUESTRO CASO)                (cada servicio independiente)

┌─────────────────┐    ┌──────────────────────────┐    ┌──────┐ ┌──────┐ ┌──────┐
│ auth            │    │  ┌──────┐ ┌───────────┐  │    │ auth │ │ rag  │ │ docs │
│ rag             │    │  │ auth │ │ rag       │  │    │      │ │      │ │      │
│ documents       │    │  │      │ │ indexing  │  │    │ DB   │ │ DB   │ │ DB   │
│ indexing        │    │  │      │ │ retrieval │  │    └──┬───┘ └──┬───┘ └──┬───┘
│ admin           │    │  │      │ │ generation│  │       │        │        │
│ (todo acoplado) │    │  └──┬───┘ └──┬────────┘  │       ▼        ▼        ▼
│                 │    │     │        │           │    3 deploys, 3 DBs, 3 repos
└─────────────────┘       ┌──┴────────┴────────┐  │    (complejidad operativa alta)
                        │ │  dominio compartido │ │
 Problema: cambiar      │ │  (entities, repos)  │ │
 una cosa rompe todo    │ └─────────────────────┘ │
                        │                         │
                        │  1 deploy, 1 DB, 1 repo │
                        │  (módulos con fronteras)│
                        └─────────────────────────┘
```

### Estructura interna del monolito modular

La arquitectura hexagonal (Clean Architecture) es la que provee la modularización. El sistema es **un solo proceso Python** con fronteras internas bien definidas:

```
┌─────────────────── UN SOLO PROCESO PYTHON ───────────────────┐
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    CAPA DOMINIO                          │  │
│  │  entities/    repositories/    services/                  │  │
│  │  (puro Python, sin deps externas)                        │  │
│  └───────────────────────┬─────────────────────────────────┘  │
│                          │ interfaces (Protocol)               │
│  ┌───────────────────────┴─────────────────────────────────┐  │
│  │                 CAPA APLICACIÓN                          │  │
│  │                                                          │  │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │  │
│  │  │  auth/  │  │   rag/   │  │  docs/   │  │  admin/ │  │  │
│  │  │ use     │  │ use      │  │ use      │  │ use     │  │  │
│  │  │ cases   │  │ cases    │  │ cases    │  │ cases   │  │  │
│  │  └────┬────┘  └────┬─────┘  └────┬─────┘  └────┬────┘  │  │
│  │       │ MÓDULOS INDEPENDIENTES     │             │       │  │
│  │       │ (pueden llamarse entre sí  │             │       │  │
│  │       │  solo via interfaces)      │             │       │  │
│  └───────┴────────────┴──────────────┴─────────────┴───────┘  │
│                          │                                     │
│  ┌───────────────────────┴─────────────────────────────────┐  │
│  │               CAPA INFRAESTRUCTURA                       │  │
│  │  api/   database/   rag/   llm/   cache/   security/     │  │
│  │  (FastAPI, SQLAlchemy, pgvector, Gemini, Redis, JWT)     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  TODO esto compila y despliega como UNA sola imagen Docker     │
└────────────────────────────────────────────────────────────────┘
```

### ¿Por qué monolito modular y no microservicios?

| Factor | Monolito Modular | Microservicios |
|--------|-----------------|----------------|
| **Equipo** | 7-8 personas | 30+ personas |
| **Deadline** | 1 mes | 3+ meses |
| **Comunicación** | Llamadas a funciones (nanosegundos) | HTTP/gRPC (milisegundos) |
| **Transacciones** | Una DB, ACID nativo | Sagas distribuidas, eventual consistency |
| **Debug** | Stack trace único | Tracing distribuido obligatorio |
| **Deploy** | 1 imagen, 1 Helm release | N imágenes, N releases, orquestación |
| **Refactor** | Mover código entre módulos | Rediseñar APIs, contratos, versiones |

El pipeline RAG necesita que auth, retrieval, generación y guardrails hablen entre sí **en la misma request**. Con microservicios, cada paso sería una llamada HTTP/gRPC que agrega latencia y complejidad. Con el monolito modular, es una llamada a función.

### Camino de evolución

El monolito modular no es un punto final. Las fronteras internas (hexagonal) facilitan extraer módulos a servicios si el equipo crece:

```
HOY (MVP, 7-8 personas)              FUTURO (si escala a 30+)

┌───────────────────────┐           ┌──────────┐  ┌──────────┐
│  Monolito Modular     │           │ API      │  │ RAG      │
│  ┌─────┐ ┌─────────┐ │    ──►    │ Service  │  │ Service  │
│  │auth │ │rag      │ │           │          │  │          │
│  │     │ │         │ │           └──────────┘  └──────────┘
│  └─────┘ └─────────┘ │
│  1 deploy              │           N deploys (solo si necesario)
└───────────────────────┘
```

**Decisión relacionada**: [ADR-001 — Monolito Modular Hexagonal](decisions/ADR-001-modular-monolith.md)

---

## 4.3 Separación de concerns por ecosistema

El sistema se compone de cuatro ecosistemas independientes:

| Ecosistema | Tecnología | Gestión de deps | Artefacto |
|------------|-----------|-----------------|-----------|
| **Backend** | Python 3.12 | UV + pyproject.toml | Imagen Docker |
| **Frontend** | Next.js + React | pnpm + package.json | Imagen Docker |
| **Pipelines** | Airflow 3 DAGs | Comparte deps de Python | GCS bucket sync (sin imagen propia) |
| **Infraestructura** | Helm + YAML | N/A | Manifests K8s |

Cada ecosistema tiene su propio ciclo de build, sus propias dependencias, y su propia estrategia de deploy. Se coordinan a nivel de monorepo pero no se mezclan.

---

## 4.4 Resumen visual del proyecto

```
┌──────────────────────────────────────────────────────────────────┐
│                         MONOREPO                                  │
│                                                                    │
│  ┌─── Python (UV) ────────────────┐  ┌─── Node.js (pnpm) ──┐   │
│  │                                 │  │                       │   │
│  │  pyproject.toml                 │  │  frontend/            │   │
│  │  src/  (monolito modular)       │  │  package.json         │   │
│  │  dags/ (Airflow DAGs)           │  │  app/                 │   │
│  │  tests/                         │  │  components/          │   │
│  │  alembic/                       │  │                       │   │
│  │                                 │  │                       │   │
│  │  → docker/Dockerfile.backend    │  │  → docker/Dockerfile  │   │
│  │  → 1 imagen Docker              │  │    .frontend          │   │
│  │                                 │  │  → 1 imagen Docker    │   │
│  └─────────────────────────────────┘  └───────────────────────┘   │
│                                                                    │
│  ┌─── Helm ──────────────────────────────────────────────────┐   │
│  │  helm/enterprise-ai-platform/                              │   │
│  │    → Deployment backend (imagen Python)                     │   │
│  │    → Deployment frontend (imagen Node)                      │   │
│  │    → StatefulSet PostgreSQL (sub-chart bitnami)             │   │
│  │    → Deployment Redis (sub-chart bitnami)                   │   │
│  │    → Ingress, ConfigMap, Secret, ServiceAccount             │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌─── Skills (.claude/) ─────────┐  ┌─── Specs (specs/) ────┐   │
│  │  HOW to build                  │  │  WHAT to build         │   │
│  │  (conocimiento técnico)        │  │  (unidades de trabajo) │   │
│  └────────────────────────────────┘  └────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Reglas rápidas

| Pregunta | Respuesta |
|----------|-----------|
| ¿UV gestiona el frontend? | No. Solo Python. |
| ¿Cuántas imágenes Docker? | 2: backend (Python) + frontend (Node) |
| ¿Cuántos Helm charts propios? | 1: `enterprise-ai-platform` (con sub-charts) |
| ¿El backend son microservicios? | No. Es un monolito modular (1 imagen, módulos internos) |
| ¿Los DAGs necesitan imagen? | No. Se sincronizan via GCS bucket al Airflow existente |
| ¿Puedo extraer microservicios después? | Sí. Las fronteras modulares (hexagonal) lo facilitan |
