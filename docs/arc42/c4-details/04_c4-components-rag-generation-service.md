# Enterprise AI Platform – RAG Generation Service

## 1. Visión General

**Diagrama de referencia:** `docs/arc42/diagrams/04-c4-components-rag-generation-service.drawio.svg`

En este documento se detallan los **componentes internos** del contenedor **RAG Generation Service**, el núcleo de inteligencia artificial del sistema. Implementa una arquitectura multi-agente basada en LangGraph para orquestar consultas RAG (Retrieval-Augmented Generation).

El servicio recibe solicitudes desde API Gateway, coordina múltiples agentes especializados, recupera información relevante desde PostgreSQL/pgvector, genera respuestas utilizando modelos LLM de Vertex AI, y envía métricas al stack de observabilidad.

---

El RAG Generation Service implementa el patrón **Supervisor** de LangGraph, donde un agente orquestador principal coordina agentes especializados según el tipo de consulta. Este diseño permite:

- **Escalabilidad horizontal**: Nuevos agentes pueden agregarse sin modificar el orquestador
- **Segregación de responsabilidades**: Cada agente tiene un dominio específico
- **Auditabilidad**: Cada decisión de routing es trazable
- **Resiliencia**: Fallos en agentes específicos no afectan al sistema completo

---

## 2. Principios y Decisiones de Diseño

| Principio | Descripción | Justificación |
|-----------|-------------|---------------|
| **Arquitectura Supervisor** | Orquestador central que delega a agentes especializados | Patrón recomendado por LangGraph para sistemas multi-agente |
| **Estado conversacional explícito** | Uso de StateGraph para mantener contexto | Permite conversaciones multi-turno y trazabilidad |
| **Guardrails obligatorios** | Validación de entrada y salida en cada interacción | Requisito regulatorio para entornos bancarios |
| **Fail-safe por diseño** | Errores no propagan respuestas incorrectas | Protección contra alucinaciones y datos sensibles |
| **Prompts versionados** | Templates de prompts gestionados centralmente | Auditabilidad y reproducibilidad |

---

## 3. Componentes Internos

### 3.1 Agente Orquestador Principal

| Aspecto | Descripción |
|---------|-------------|
| **Tipo** | Component: LangGraph StateGraph |
| **Responsabilidad** | Punto de entrada único para todas las solicitudes |
| **Función** | Analiza la intención del usuario y delega la consulta al agente apropiado (Público o Privado) |

Es el componente central que recibe todas las peticiones del API Gateway. Utiliza un StateGraph de LangGraph para:

1. Mantener el estado de la conversación
2. Clasificar la intención del usuario
3. Determinar el flujo de ejecución (routing condicional)
4. Consolidar respuestas de agentes especializados

**Nodos del StateGraph:**

| Nodo | Función |
|------|---------|
| `classify_intent` | Determina si la consulta es pública o privada |
| `route_to_agent` | Enruta al agente correspondiente |
| `consolidate_response` | Formatea la respuesta final |
| `error_handler` | Maneja excepciones y fallbacks |

---

### 3.2 State Manager (Memoria Conversacional)

| Aspecto | Descripción |
|---------|-------------|
| **Tipo** | Component: LangGraph Checkpointer |
| **Responsabilidad** | Persistencia del estado conversacional |
| **Función** | Almacena y recupera el contexto de conversaciones multi-turno |

Gestiona la memoria de la conversación utilizando el patrón de checkpointing de LangGraph:

- **Memoria a corto plazo**: Contexto de la sesión actual
- **Memoria a largo plazo**: Historial de interacciones del usuario (opcional)
- **Persistencia**: PostgreSQL para durabilidad

**Campos del estado:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `session_id` | string | Identificador único de sesión |
| `user_id` | string | Identificador del usuario (si autenticado) |
| `messages` | array | Historial de mensajes de la conversación |
| `current_agent` | string | Agente que está procesando la consulta |
| `context` | object | Contexto recuperado del vector store |
| `metadata` | object | Información adicional (timestamps, tokens) |

---

### 3.3 Input Guardrails

| Aspecto | Descripción |
|---------|-------------|
| **Tipo** | Component: Validation Layer |
| **Responsabilidad** | Validación y sanitización de entradas |
| **Función** | Protege el sistema contra inputs maliciosos o sensibles |

**Validaciones implementadas:**

| Validación | Descripción | Acción |
|------------|-------------|--------|
| **Detección de PII** | Identifica datos personales (DNI, tarjetas, etc.) | Enmascara o rechaza |
| **Prompt Injection** | Detecta intentos de manipulación del prompt | Rechaza con log de seguridad |
| **Longitud máxima** | Limita tokens de entrada | Trunca con advertencia |
| **Idioma** | Valida idioma soportado | Responde en idioma detectado |
| **Contenido prohibido** | Detecta solicitudes fuera de alcance | Respuesta predefinida |

---

### 3.4 Output Guardrails

| Aspecto | Descripción |
|---------|-------------|
| **Tipo** | Component: Validation Layer |
| **Responsabilidad** | Validación de respuestas generadas |
| **Función** | Asegura calidad y seguridad de las respuestas |

**Validaciones implementadas:**

| Validación | Descripción | Acción |
|------------|-------------|--------|
| **Detección de alucinaciones** | Verifica que la respuesta esté fundamentada en el contexto | Regenera o advierte |
| **Filtro de PII** | Evita exposición de datos sensibles en respuestas | Enmascara |
| **Relevancia** | Valida que la respuesta sea pertinente | Regenera si score < umbral |
| **Formato** | Asegura estructura esperada de la respuesta | Reformatea |
| **Longitud** | Controla extensión de la respuesta | Trunca con indicador |

---

### 3.5 Prompt Manager

| Aspecto | Descripción |
|---------|-------------|
| **Tipo** | Component: Template Engine |
| **Responsabilidad** | Gestión centralizada de prompts |
| **Función** | Versionado, auditoría y optimización de prompts |

**Características:**

- Templates versionados con control de cambios
- Variables de contexto inyectables
- Métricas de efectividad por template
- A/B testing de prompts

**Estructura de un template:**

| Campo | Descripción |
|-------|-------------|
| `template_id` | Identificador único |
| `version` | Versión semántica |
| `system_prompt` | Instrucciones del sistema |
| `user_template` | Template para consulta del usuario |
| `context_template` | Template para inyección de contexto |
| `output_format` | Formato esperado de respuesta |

---

### 3.6 Agente Información Pública

| Aspecto | Descripción |
|---------|-------------|
| **Tipo** | Component: LangGraph Agent |
| **Responsabilidad** | Consultas sobre información pública del banco |
| **Patrón** | Augmentation + Generation |
| **Origen** | Peticiones desde banco chat |

Maneja consultas que no requieren autenticación del usuario:

- Información general de productos
- Horarios y sucursales
- Requisitos de trámites
- Preguntas frecuentes

**Flujo de ejecución:**

1. Recibe consulta clasificada
2. Invoca Tool Vector Search con filtros de documentos públicos
3. Construye prompt con contexto recuperado
4. Genera respuesta vía Vertex AI
5. Aplica Output Guardrails

---

### 3.7 Agente Información Privada

| Aspecto | Descripción |
|---------|-------------|
| **Tipo** | Component: LangGraph Orchestrator |
| **Responsabilidad** | Sub-orquestador de consultas privadas |
| **Función** | Valida autenticación y delega a agentes especializados según el tipo de consulta |

Actúa como segundo nivel de orquestación:

1. Verifica que el usuario esté autenticado (token JWT válido)
2. Extrae roles y permisos del usuario
3. Determina cuál agente especializado debe atender la consulta
4. Aplica filtros de acceso según ACLs del usuario

---

### 3.8 Agentes Especializados (Información Privada)

Estos agentes manejan consultas que requieren autenticación y acceso a datos sensibles.

| Aspecto | Descripción |
|---------|-------------|
| **Tipo** | Component: LangGraph Agent |
| **Patrón** | Augmentation + Generation |
| **Acceso** | Requiere autenticación del usuario |
| **Delegación** | Invocados por el Agente Información Privada según tipo de consulta |

**Agentes identificados (relevamiento 08-01-2026):**

> **Nota**: Los siguientes agentes son ejemplos preliminares identificados durante el relevamiento inicial. La lista definitiva se confirmará al finalizar la etapa de relevamiento.

- Agente de Call Center
- Agente de Sucursal
- Agente de Recursos Humanos

#### N Agentes Adicionales

Representa la extensibilidad del sistema. Nuevos agentes especializados pueden agregarse según los relevamientos de necesidades del negocio.

El diseño permite agregar nuevos agentes especializados de forma modular. La incorporación de nuevos agentes se realizará conforme se identifiquen necesidades adicionales durante el proceso de relevamiento y evolución del producto.

### 3.9 Tool - Vector Search

| Aspecto | Descripción |
|---------|-------------|
| **Tipo** | Component: LangChain Tool |
| **Responsabilidad** | Retrieval de información |
| **Función** | Busca información en la base de datos por similitud semántica (embeddings) |

Herramienta compartida por todos los agentes. Ejecuta búsquedas vectoriales contra PostgreSQL/pgvector para encontrar los fragmentos de documentos más relevantes según la consulta del usuario. Es el componente "R" (Retrieval) del patrón RAG.

**Parámetros de búsqueda:**

| Parámetro | Tipo | Descripción | Default |
|-----------|------|-------------|---------|
| `query` | string | Consulta del usuario | - |
| `k` | integer | Número de resultados | 5 |
| `score_threshold` | float | Umbral mínimo de similitud | 0.7 |
| `filter` | object | Filtros de metadata (tipo documento, ACLs) | - |
| `search_type` | string | Tipo de búsqueda: "similarity" \| "mmr" | "similarity" |

**Estrategia de retrieval:**

- **MMR (Maximal Marginal Relevance)**: Para diversidad en resultados
- **Filtrado por ACL**: Solo documentos accesibles por el usuario
- **Reranking**: Opcional, para mejorar relevancia

---

## 4. Integraciones Externas

### API Gateway → RAG Generation Service

| Aspecto | Descripción |
|---------|-------------|
| **Contenedor Origen** | API Gateway (Python/FastAPI) |
| **Protocolo** | HTTP/WebSocket |
| **Dirección** | Invoca al RAG Generation Service |

El API Gateway es el punto de entrada HTTP/WebSocket para los clientes. Luego de autenticar y aplicar rate limits, invoca al RAG Generation Service mediante HTTP para solicitudes síncronas y WebSocket para streaming de tokens.

---

### RAG Generation Service → PostgreSQL + pgvector

| Aspecto | Descripción |
|---------|-------------|
| **Contenedor Destino** | PostgreSQL + pgvector |
| **Protocolo** | SQL |
| **Operación** | Lee embeddings |

El Tool Vector Search consulta la base de datos PostgreSQL con la extensión pgvector para recuperar los embeddings más similares a la consulta del usuario. Este almacén contiene tanto embeddings como datos de aplicación.

---

### RAG Generation Service → Vertex AI (LLM Provider)

| Aspecto | Descripción |
|---------|-------------|
| **Sistema Destino** | Vertex AI (Google Cloud) |
| **Protocolo** | HTTPS/REST |
| **Operación** | Genera respuestas |

Todos los agentes utilizan Vertex AI como proveedor de modelos LLM (Gemini, Claude) para la fase de generación de respuestas.

**Configuración de llamadas:**

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `temperature` | 0.1 - 0.3 | Baja para respuestas consistentes |
| `max_tokens` | 1024 | Límite de tokens de salida |
| `top_p` | 0.95 | Nucleus sampling |
| `timeout` | 30s | Timeout de llamada |

**Resiliencia:**

- Circuit breaker con umbral de 5 errores consecutivos
- Retry con backoff exponencial (1s, 2s, 4s)
- Fallback a respuesta predefinida si el servicio no está disponible

---

### RAG Generation Service → Observabilidad

| Aspecto | Descripción |
|---------|-------------|
| **Contenedor Destino** | Observabilidad (Langfuse/Prometheus/Grafana) |
| **Protocolo** | HTTP |
| **Operación** | Envía métricas y trazas |

El servicio envía telemetría y métricas al stack de observabilidad para monitoreo, debugging y análisis de performance de los agentes.

---

## 5. Contratos de Datos

### Contrato de Entrada (Request)

| Campo | Tipo | Obligatorio | Validación |
|-------|------|-------------|------------|
| `session_id` | string | Sí | UUID v4 |
| `message` | string | Sí | 1-4000 caracteres |
| `user_id` | string | No | Si autenticado |
| `conversation_history` | array | No | Max 10 mensajes |
| `metadata` | object | No | Campos adicionales |

### Contrato de Salida (Response)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `response_id` | string | Sí | UUID de la respuesta |
| `message` | string | Sí | Respuesta generada |
| `sources` | array | Sí | Documentos fuente utilizados |
| `agent_used` | string | Sí | Agente que procesó la consulta |
| `confidence_score` | float | No | Score de confianza (0-1) |
| `tokens_used` | object | Sí | Tokens de entrada y salida |
| `latency_ms` | integer | Sí | Tiempo de procesamiento |

### Estructura de Sources

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `document_id` | string | ID del documento fuente |
| `chunk_id` | string | ID del chunk utilizado |
| `title` | string | Título del documento |
| `relevance_score` | float | Score de similitud |
| `snippet` | string | Extracto del contenido |

---

## 6. Manejo de Errores y Recuperación

### Clasificación de Errores

| Severidad | Tipo | Ejemplo | Acción |
|-----------|------|---------|--------|
| **Crítico** | Seguridad | Intento de prompt injection | Log de seguridad, respuesta genérica |
| **Alto** | LLM Provider | Timeout de Vertex AI | Circuit breaker, fallback |
| **Medio** | Retrieval | Sin resultados relevantes | Respuesta "No tengo información" |
| **Bajo** | Formato | Respuesta mal formateada | Reformatear, log |

### Respuestas de Fallback

| Escenario | Respuesta |
|-----------|-----------|
| LLM no disponible | "En este momento no puedo procesar tu consulta. Por favor, intenta nuevamente en unos minutos." |
| Sin contexto relevante | "No encontré información específica sobre tu consulta. ¿Podrías reformularla o ser más específico?" |
| Consulta fuera de alcance | "Esta consulta está fuera de mi área de conocimiento. Te sugiero contactar a [canal apropiado]." |
| Error de autenticación | "Para acceder a esta información necesitas estar autenticado. Por favor, inicia sesión." |

### Política de Reintentos

| Tipo de error | Reintentos | Backoff | Timeout |
|---------------|------------|---------|---------|
| LLM timeout | 2 | Exponencial (1s, 2s) | 30s |
| Vector search timeout | 2 | Lineal (500ms) | 10s |
| Error de validación | 0 | - | - |

---

## 7. Observabilidad y Métricas

El stack de observabilidad (Langfuse + Prometheus + Grafana) permite monitorear el comportamiento del sistema.

### Métricas de Performance

| Métrica | Descripción | Herramienta | Umbral de alerta |
|---------|-------------|-------------|------------------|
| `llm_request_latency_seconds` | Tiempo de respuesta de llamadas al LLM | Prometheus | P95 > 10s |
| `llm_tokens_total` | Tokens consumidos (input + output) | Langfuse | > 10K/min |
| `rag_retrieval_latency_seconds` | Tiempo de búsqueda vectorial | Prometheus | P95 > 2s |
| `rag_documents_retrieved` | Cantidad de documentos recuperados por consulta | Prometheus | avg < 1 |
| `agent_execution_time_seconds` | Tiempo total de ejecución por agente | Langfuse | P95 > 15s |
| `agent_invocations_total` | Contador de invocaciones por tipo de agente | Prometheus | - |
| `agent_errors_total` | Contador de errores por tipo de agente | Prometheus | > 5%/5min |

### Métricas de Calidad

| Métrica | Descripción | Herramienta |
|---------|-------------|-------------|
| `vector_search_similarity_score` | Score de similitud promedio de resultados | Langfuse |
| `response_relevance_score` | Relevancia de la respuesta vs consulta | Langfuse |
| `guardrail_triggers_total` | Activaciones de guardrails por tipo | Prometheus |
| `conversation_turns_total` | Cantidad de turnos por conversación | Langfuse |
| `fallback_responses_total` | Respuestas de fallback generadas | Prometheus |

### Métricas Claves Recomendadas

Considerando la arquitectura multi-agente con RAG, estas son las 3 métricas más críticas:

#### 1. Latencia End-to-End por Agente (`agent_execution_time_seconds`)

**Por qué es importante**: Permite identificar cuellos de botella en agentes específicos. Si el Agente de RRHH tarda significativamente más que otros, indica problemas en su retrieval o prompts.

**Uso**: Dashboard con percentiles P50, P95, P99 por tipo de agente. Alertas si P95 > 10 segundos.

#### 2. Tokens Consumidos por Solicitud (`llm_tokens_total`)

**Por qué es importante**: Impacta directamente en costos operativos. Permite optimizar prompts y detectar consultas que generan respuestas excesivamente largas.

**Uso**: Monitoreo de consumo diario/mensual, desglosado por agente. Alertas de anomalías (ej: consumo 3x superior al promedio).

#### 3. Tasa de Errores por Agente (`agent_errors_total`)

**Por qué es importante**: Detecta degradación del servicio. Errores pueden indicar problemas con el LLM provider, timeouts de base de datos, o fallos en la lógica de agentes.

**Uso**: Rate de errores por minuto. Alertas si error_rate > 5% en ventana de 5 minutos.

### Trazabilidad (Langfuse)

Cada interacción genera una traza completa que incluye:

- Consulta original
- Clasificación de intención
- Agente seleccionado
- Documentos recuperados con scores
- Prompt construido
- Respuesta del LLM
- Validaciones de guardrails
- Respuesta final

---

## 8. Consideraciones de Seguridad

### Protección de Datos

| Control | Descripción |
|---------|-------------|
| **Enmascaramiento de PII** | Datos sensibles nunca se envían al LLM sin enmascarar |
| **Filtrado por ACL** | Solo se recuperan documentos accesibles por el usuario |
| **Logs sanitizados** | Los logs no contienen información sensible |
| **Encriptación en tránsito** | TLS 1.3 para todas las comunicaciones |

### Auditoría

Todas las interacciones se registran con:

- Timestamp (ISO 8601)
- User ID (si autenticado)
- Session ID
- Consulta (hash si contiene PII)
- Agente utilizado
- Documentos accedidos
- Respuesta generada (hash)
- Resultado de guardrails

---

## 9. Referencias

- Para definiciones de términos técnicos, consultar el glosario en `docs/arc42/12_glossary.md`.
