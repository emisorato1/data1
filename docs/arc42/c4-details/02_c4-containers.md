# Enterprise AI Platform – Vista de Contenedores

## 1. Visión General

El diagrama de contenedores presenta la arquitectura interna del sistema **Enterprise AI Platform**, una plataforma de inteligencia artificial empresarial orientada a la generación de respuestas mediante RAG (Retrieval-Augmented Generation).

**Diagrama de referencia:** `docs/arc42/diagrams/02-c4-containers.drawio.svg`

---

## 2. Actores

| Actor | Tipo | Descripción |
|-------|------|-------------|
| Usuario final | Person | Empleado de la organización que utiliza la interfaz de chat conversacional. |
| Usuario técnico | Person | Empleado de la organización que integra sus sistemas mediante API REST/WebSocket. |
| Agente Externo | Software System | Agente de IA externo que colabora con el sistema vía protocolos MCP y A2A [TBC]. |

---

## 3. Sistemas Externos

| Sistema | Descripción | Protocolo |
|---------|-------------|-----------|
| OpenText ECM | Sistema de gestión documental corporativo. Fuente de documentos para indexación. | HTTP |
| Vertex AI | Proveedor de modelos LLM y embeddings (Gemini, Anthropic). | HTTPS/WebSocket |

---

## 4. Contenedores del Sistema

### 4.1 Capa de Presentación

| Contenedor | Tecnología | Descripción |
|------------|------------|-------------|
| RAG Chat Frontend | TypeScript/React | UI de chat conversacional. Accedida por el usuario final vía HTTPS/WebSocket. |

### 4.2 Capa de Servicios

| Contenedor | Tecnología | Descripción |
|------------|------------|-------------|
| API Gateway | Python/FastAPI | Punto de entrada unificado. Gestiona autenticación, routing y rate limits. Expone REST y WebSocket. |
| RAG Generation Service | Python/Langgraph/Langchain | Agente RAG con retrieval, augmentation y generation. Contiene agente orquestador y agentes específicos. |
| RAG Indexation Service | Python/Langchain/Airflow | Pipelines de ingesta de documentos desde OpenText ECM. |
| MCP Server | Python | Expone herramientas MCP para clientes LLM [TBC]. |
| A2A Server | Python | Comunicación agente a agente vía protocolo A2A [TBC]. |

### 4.3 Capa de Datos

| Contenedor | Tecnología | Descripción |
|------------|------------|-------------|
| Platform Database | PostgreSQL | Almacena datos de aplicación: usuarios, tenants, conversaciones, mensajes y roles. |
| Vector Store | PostgreSQL + pgvector | Almacén de embeddings y datos de aplicación para búsqueda semántica. |

### 4.4 Capa de Observabilidad

| Contenedor | Tecnología | Descripción |
|------------|------------|-------------|
| Observabilidad | LangFuse/Prometheus/Grafana | Monitoreo, trazabilidad y métricas del sistema. |

---

## 5. Relaciones entre Contenedores

### 5.1 Flujo Principal (Usuario Final)

1. El **Usuario final** accede al **RAG Chat Frontend** vía HTTPS/WebSocket.
2. El **RAG Chat Frontend** invoca al **API Gateway** mediante HTTP REST/WebSocket/SSE.
3. El **API Gateway** invoca al **RAG Generation Service** vía HTTP/WebSocket.
4. El **RAG Generation Service** lee embeddings de **Vector Store** mediante VQL/SQL.
5. El **RAG Generation Service** integra con **Vertex AI** para generación de respuestas vía HTTPS/WebSocket.
6. El **API Gateway** lee datos de usuario y conversación desde **Platform Database** mediante SQL.

### 5.2 Flujo de Indexación

1. El **RAG Indexation Service** integra con **OpenText ECM** para obtener documentos vía HTTP/SQL.
2. El **RAG Indexation Service** genera embeddings mediante **Vertex AI**.
3. El **RAG Indexation Service** escribe embeddings en **Vector Store** mediante VQL/SQL.
4. El **RAG Indexation Service** ingresa registros de documentos en **Platform Database** mediante SQL.
5. El **RAG Indexation Service** escribe metadata de documentos en **Platform Database** mediante SQL.

### 5.3 Flujo de Usuario Técnico

1. El **Usuario técnico** accede directamente al **API Gateway** vía HTTPS REST/WebSocket.
2. El flujo posterior es idéntico al del usuario final.

### 5.4 Flujo de Agente Externo [TBC]

1. El **Agente Externo** puede comunicarse vía **MCP Server** mediante STDIO/SSE.
2. El **Agente Externo** puede comunicarse vía **A2A Server** mediante HTTPS/JSON-RPC.
3. Ambos servidores invocan al **API Gateway** para ejecutar operaciones.

### 5.5 Observabilidad

Los siguientes contenedores envían métricas al contenedor de **Observabilidad** vía HTTP:

- API Gateway
- RAG Generation Service
- RAG Indexation Service

---

## 6. Notas

- Los elementos marcados con **[TBC]** (To Be Confirmed) están fuera del alcance actual y se representan con líneas punteadas en el diagrama.
- Para definiciones de términos técnicos, consultar el glosario en `docs/arc42/12_glossary.md`.
