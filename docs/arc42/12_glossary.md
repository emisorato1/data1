# Enterprise AI Platform – Glosario

Este documento contiene las definiciones de términos técnicos utilizados en la documentación de arquitectura de la Enterprise AI Platform.

---

## Términos Generales

| Término | Definición |
|---------|------------|
| **A2A** | Agent-to-Agent - Protocolo de comunicación entre agentes de IA |
| **Clean Architecture** | Arquitectura de software con capas independientes que facilita testing, mantenibilidad y evolución |
| **DTO** | Data Transfer Object - Objeto para transferencia de datos entre capas o sistemas |
| **MCP** | Model Context Protocol - Protocolo para exponer herramientas y contexto a modelos de lenguaje |
| **Multi-tenant** | Arquitectura que permite aislar datos y configuraciones por organización o unidad de negocio |
| **Namespace Isolation** | Separación lógica de datos por identificador de tenant |
| **Tenant** | Organización o unidad de negocio aislada en el sistema |

---

## Autenticación y Seguridad

| Término | Definición |
|---------|------------|
| **Access Token** | JWT de corta duración para autenticar requests |
| **ACL** | Access Control List - Lista de control de acceso que define permisos por usuario/grupo |
| **API Key** | Credencial de larga duración para usuarios técnicos |
| **CVE** | Common Vulnerabilities and Exposures - Identificador estándar de vulnerabilidades |
| **JWT** | JSON Web Token - Estándar para tokens de autenticación |
| **mTLS** | Mutual TLS - Autenticación bidireccional mediante certificados |
| **PII** | Personally Identifiable Information - Datos personales identificables |
| **RBAC** | Role-Based Access Control - Control de acceso basado en roles |
| **Red Teaming** | Ejercicio de seguridad donde un equipo simula ataques reales |
| **Refresh Token** | Token de larga duración para renovar access tokens |
| **RLS** | Row-Level Security - Seguridad a nivel de fila en bases de datos |
| **Scope** | Permiso granular asociado a un token |
| **SIEM** | Security Information and Event Management - Sistema de gestión de eventos de seguridad |
| **Zero Trust** | Modelo de seguridad donde ningún componente confía implícitamente en otro |

---

## Comunicación y Protocolos

| Término | Definición |
|---------|------------|
| **Middleware** | Componente que intercepta requests/responses para aplicar lógica transversal |
| **SSE** | Server-Sent Events - Protocolo de streaming unidireccional del servidor al cliente |
| **Trace ID** | Identificador único para rastrear una solicitud a través de múltiples servicios |
| **WebSocket** | Protocolo de comunicación bidireccional en tiempo real |

---

## RAG y Modelos de Lenguaje

| Término | Definición |
|---------|------------|
| **Augmentation** | Proceso de enriquecer el prompt con contexto recuperado de documentos |
| **Chunk** | Fragmento de documento con coherencia semántica, unidad mínima de indexación |
| **Data Poisoning** | Contaminación de datos de indexación o entrenamiento con información maliciosa |
| **Embedding** | Representación vectorial de texto para búsqueda semántica |
| **Guardrail** | Validación de seguridad para entradas o salidas del sistema de IA |
| **LangGraph** | Framework de LangChain para construir agentes con estado |
| **LLM** | Large Language Model - Modelo de lenguaje de gran escala |
| **MMR** | Maximal Marginal Relevance - Estrategia de retrieval que balancea relevancia y diversidad |
| **Prompt Injection** | Ataque donde se inyectan instrucciones maliciosas en el prompt del usuario |
| **RAG** | Retrieval-Augmented Generation - Patrón que combina búsqueda de documentos con generación de texto |
| **SAIF** | Secure AI Framework - Framework de Google para seguridad en sistemas de IA |
| **StateGraph** | Grafo de estados de LangGraph para orquestación de agentes |
| **Supervisor** | Patrón donde un agente central coordina múltiples agentes especializados |

---

## Procesamiento de Datos

| Término | Definición |
|---------|------------|
| **Bronze** | Capa de datos crudos sin transformaciones en la arquitectura Medallion |
| **DLQ** | Dead Letter Queue - Cola de mensajes fallidos para análisis y reprocesamiento |
| **ECM** | Enterprise Content Management - Sistema de gestión de contenido empresarial |
| **Gold** | Capa de datos optimizados para consumo en la arquitectura Medallion |
| **Linaje** | Registro del origen y transformaciones de un dato (Data Lineage) |
| **Medallion** | Arquitectura de capas Bronze/Silver/Gold para procesamiento progresivo de datos |
| **Silver** | Capa de datos limpios y validados en la arquitectura Medallion |

---

## Infraestructura y Resiliencia

| Término | Definición |
|---------|------------|
| **Circuit Breaker** | Patrón que previene llamadas a servicios fallidos temporalmente |
| **pgvector** | Extensión de PostgreSQL para almacenamiento y búsqueda de vectores |
| **Vector Store** | Base de datos especializada en almacenar y buscar embeddings |

---

## Acrónimos de Sistemas

| Acrónimo | Significado |
|----------|-------------|
| **API** | Application Programming Interface |
| **ECM** | Enterprise Content Management |
| **LLM** | Large Language Model |
| **RAG** | Retrieval-Augmented Generation |
| **REST** | Representational State Transfer |
| **SAIF** | Secure AI Framework |
| **SQL** | Structured Query Language |
| **TBC/TBD** | To Be Confirmed / To Be Determined - Elementos pendientes de confirmación |
| **UUID** | Universally Unique Identifier |
