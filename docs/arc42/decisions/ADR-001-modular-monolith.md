# ADR-001: Monolito Modular Hexagonal como Estilo Arquitectónico

## Status

**Accepted**

## Date

2026-02-13

## Context

Debemos definir el estilo arquitectónico del sistema RAG Enterprise para el sector bancario. El sistema incluye: API REST, pipeline RAG (retrieval + generation), autenticación, gestión documental, guardrails de seguridad, y observabilidad.

### Fuerzas en juego

- **Equipo**: 7-8 personas en 5 tracks paralelos
- **Timeline**: MVP en 4 semanas (4 sprints semanales)
- **Escala target**: ~6000 usuarios, 30 QPS pico
- **Dominio**: Sector bancario con requisitos de auditoría y compliance
- **Pipeline RAG**: Secuencial, latency-sensitive (p95 < 3s), con estado compartido vía LangGraph
- **Madurez operacional**: CI, Docker, y Helm charts se están construyendo durante el MVP
- **Documentación previa**: `docs/arc42/` describe una visión de microservicios que fue diseñada antes de iniciar la implementación

## Considered Options

### Opción 1: Microservicios

Servicios independientes (API Gateway, RAG Generation Service, RAG Indexing Service, Auth Service) comunicándose vía REST/gRPC.

**Pros:**
- Escalado independiente por componente
- Deployment independiente por equipo
- Aislamiento de fallas

**Contras:**
- Overhead operacional desproporcionado para 7-8 personas (5+ CI/CD pipelines, service mesh, API gateway)
- Latencia adicional por network hops entre servicios (incompatible con p95 < 3s)
- LangGraph StateGraph diseñado para estado in-process; distribuirlo anula su ventaja
- Transacciones distribuidas complejas (saga patterns) vs transacciones atómicas simples
- Auditoría bancaria más difícil con datos distribuidos en múltiples DBs
- Las boundaries del dominio RAG aún se están explorando; fijarlas prematuramente genera rigidez
- 30 QPS no justifica escalado independiente de componentes

### Opción 2: Monolito Modular Hexagonal (Clean Architecture)

Un único proceso desplegable (FastAPI) con módulos internos bien definidos, separación por capas (domain/application/infrastructure), y comunicación entre módulos vía interfaces (Protocol classes).

**Pros:**
- Ship MVP en 4 semanas (complejidad operacional mínima)
- LangGraph corre in-process (estado compartido sin serialización)
- Transacciones atómicas en un solo PostgreSQL (audit trail simple)
- Refactoring libre entre módulos sin versionado de APIs
- 80% de los beneficios de microservicios a 20% del costo
- Path claro de extracción a microservicios si escala lo requiere (Strangler Pattern)
- Equipo de 7-8 personas es el tamaño ideal para un monolito (umbral micro: 50+ devs)

**Contras:**
- No se puede escalar un módulo individual independientemente
- Todos los módulos comparten el mismo ciclo de release
- Un bug en un módulo puede afectar otros (mitigado con error handling robusto)

### Opción 3: Monolito tradicional (sin modularización)

Código sin estructura clara de módulos ni separación de capas.

**Descartado inmediatamente**: No cumple con principios SOLID ni permite evolución futura.

## Decision

**Monolito Modular Hexagonal (Opción 2).**

El sistema se implementa como un único proceso FastAPI con arquitectura hexagonal (Clean Architecture) de 3 capas:

```
Domain (puro, sin deps externas)
  └── Entities, Value Objects, Repository Protocols, Domain Services

Application (orquestación)
  └── Use Cases, DTOs, LangGraph Graphs, Application Services

Infrastructure (implementaciones)
  └── API/FastAPI, Database/SQLAlchemy, RAG pipeline, LLM clients,
      Cache/Redis, Security/JWT, Observability/Langfuse
```

Los módulos internos se comunican vía **Protocol classes** (ports), permitiendo extracción futura sin rewrite.

### Deployment en K8s

```
Namespace: enterprise-ai    → FastAPI (2-3 réplicas) + PG + Redis + Next.js
Namespace: airflow           → Airflow 3 (servicio de indexación separado)
Namespace: langfuse          → Langfuse (observabilidad)
```

## Consequences

### Positivas

- Velocidad de desarrollo máxima para el MVP
- Simplicidad operacional (1 Dockerfile, 1 Helm chart, 1 CI pipeline)
- LangGraph funciona nativamente (in-process StateGraph)
- Audit trail atómico en un solo PostgreSQL
- Refactoring libre durante la exploración del dominio RAG

### Negativas

- Si un módulo requiere escalado diferente al resto, hay que extraerlo (Strangler Pattern)
- Un deployment agrupa todo — no se puede hacer rollback parcial de un módulo

### Path de migración

Si la escala lo requiere post-MVP:
1. Extraer embedding service (si múltiples consumidores emergen)
2. Extraer cualquier módulo cuyo perfil de escalado diverga significativamente
3. Las Protocol classes hacen que la extracción sea mecánica, no un rewrite

## Evidence

- Martin Fowler: "Almost all successful microservice stories started with a monolith" ([MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html))
- CNCF 2025: 42% de organizaciones consolidando microservicios de vuelta a monolitos
- Shopify: miles de devs, eligió monolito modular, nunca migró a microservicios
- Sam Newman (autor de "Building Microservices"): "begin with a single deployable unit"
- Ley de Conway: 5 tracks de 1-2 personas = 5 módulos internos, no 5 servicios independientes
- Un FastAPI con 2-3 réplicas en K8s maneja cientos de QPS; target es 30
