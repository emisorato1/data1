# Enterprise AI Platform - Documentación de Arquitectura

## Descripción General

Enterprise AI Platform es una plataforma empresarial de inteligencia artificial que proporciona acceso a agentes RAG (Retrieval-Augmented Generation) para consultar documentos corporativos. El sistema se integra con OpenText ECM como gestor documental y utiliza Vertex AI como proveedor de modelos LLM y embeddings.

### Actores del Sistema

- **Usuario Final**: Empleado que interactúa con el sistema mediante la interfaz de chat.
- **Usuario Técnico**: Empleado que integra el sistema mediante APIs (MCP, A2A)*.
- **Agente Externo**: Agente de IA que colabora con el sistema vía protocolo A2A*.

> Nota [TBC]: Protocolos MCP y A2A no se encuentra bajo el alcance inicial del proyecto definido en la propuesta tecnica.

---

## Índice de Documentación Arc42

| Documento | Descripción |
|-----------|-------------|
| [01 - Introduction and Goals](./01_introduction_and_goals.md) | Define los objetivos del sistema, stakeholders principales y requisitos de calidad prioritarios para la plataforma AI empresarial. |
| [02 - Architecture Constraints](./02_architecture_constraints.md) | Documenta las restricciones técnicas, organizacionales y convenciones que limitan las decisiones sobre el sistema. |
| [03 - System Scope and Context](./03_system_scope_and_context.md) | Describe el alcance del sistema, sus fronteras y las interfaces con sistemas externos como OpenText ECM y Vertex AI. |
| [04 - Solution Strategy](./04_solution_strategy.md) | Presenta las decisiones estratégicas fundamentales y enfoques tecnológicos adoptados para cumplir los objetivos de la plataforma. |
| [05 - Building Block View](./05_building_block_view.md) | Descompone el sistema en bloques de construcción jerárquicos, mostrando contenedores y componentes principales de la arquitectura. |
| [06 - Runtime View](./06_runtime_view.md) | Ilustra los escenarios de ejecución principales, incluyendo flujos de consulta RAG e indexación de documentos. |
| [07 - Deployment View](./07_deployment_view.md) | Describe la infraestructura técnica, entornos de despliegue y mapeo de contenedores a nodos de ejecución. |
| [08 - Cross-cutting Concepts](./08_cross_cutting_concepts.md) | Documenta conceptos transversales como seguridad, observabilidad, manejo de errores y patrones de diseño aplicados. |
| [09 - Architecture Decisions](./09_architecture_decisions.md) | Registra las decisiones arquitectónicas importantes (ADRs) con su contexto, opciones evaluadas y justificación. |
| [10 - Quality Requirements](./10_quality_requirements.md) | Detalla los requisitos de calidad mediante escenarios concretos de rendimiento, disponibilidad, seguridad y escalabilidad. |
| [11 - Risks and Technical Debt](./11_risks_and_technical_debt.md) | Identifica riesgos técnicos conocidos, deuda técnica acumulada y estrategias de mitigación planificadas. |
| [12 - Glossary](./12_glossary.md) | Define términos técnicos y de dominio utilizados en la documentación: RAG, embeddings, MCP, A2A, entre otros. |

---

## Diagramas C4

| Nivel | Diagrama | Descripción |
|-------|----------|-------------|
| Contexto | [01-c4-context](./diagrams/01-c4-context.drawio.svg) | Vista de contexto mostrando actores y sistemas externos. |
| Contenedores | [02-c4-contenedores](./diagrams/02-c4-contenedores.drawio.svg) | Descomposición en contenedores principales del sistema. |

### Detalle de Contenedores

| Documento | Descripción |
|-----------|-------------|
| [02 - C4 Containers](./c4-details/02_c4-containers.md) | Visión general de todos los contenedores que componen la plataforma y sus responsabilidades. |
| [03 - API Gateway](./c4-details/03_c4-container-api-gateway.md) | Componentes del API Gateway: autenticación, routing, rate limiting y exposición de protocolos MCP/A2A. |
| [04 - RAG Generation Service](./c4-details/04_c4-container-rag-generation-service.md) | Servicio de generación RAG: orquestación de consultas, recuperación de contexto e inferencia LLM. |
| [05 - RAG Indexing Service](./c4-details/05_c4-container-rag-indexing-service.md) | Servicio de indexación: procesamiento de documentos, generación de embeddings y almacenamiento vectorial. |
| [06 - Platform Security](./c4-details/06_c4-container-platform-security.md) | Componentes de seguridad: gestión de identidades, autorización y auditoría de accesos. |