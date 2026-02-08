# Enterprise AI Platform – Seguridad de la Plataforma

## 1. Visión General

**Diagrama de referencia:** `docs/arc42/diagrams/06-c4-platform-security.drawio.svg`

Este documento presenta el análisis de seguridad de la **Enterprise AI Platform** basado en el **Google Secure AI Framework (SAIF)** y alineado con los pilares de seguridad, privacidad y cumplimiento del **Google Cloud Well-Architected Framework**.

El análisis mapea los riesgos identificados en SAIF con los componentes documentados en la arquitectura C4 y define los controles de mitigación implementados.

---

## 2. Principios Rectores

Los principios de seguridad de la plataforma están alineados con el pilar de "Seguridad, privacidad y cumplimiento" del Google Cloud Well-Architected Framework:

| Principio | Descripción | Implementación |
|-----------|-------------|----------------|
| **Zero Trust** | Ningún componente confía implícitamente en otro. Toda comunicación se autentica y autoriza. | JWT validation en cada request, mTLS entre servicios internos. |
| **Least Privilege** | Cada componente tiene únicamente los permisos mínimos necesarios para su función. | RBAC granular, scopes por endpoint, namespace isolation por tenant. |
| **Defense in Depth** | Múltiples capas de controles de seguridad redundantes. | Guardrails de entrada/salida, validación en aplicación y datos, WAF perimetral. |
| **Secure by Default** | Las configuraciones por defecto son seguras. | Rate limiting activo, CORS restrictivo, headers de seguridad habilitados. |
| **Observability First** | Toda actividad de seguridad es trazable y auditable. | Logging centralizado, métricas de seguridad, alertas automáticas. |

---

## 3. Componentes Bajo Alcance

### 3.1 Clasificación por Capa SAIF

| Capa SAIF | Componente | Tecnología | Descripción |
|-----------|------------|------------|-------------|
| **Aplicación** | API Gateway | Python/FastAPI | Punto de entrada. Autenticación, RBAC, rate limiting. |
| **Aplicación** | RAG Chat Frontend | TypeScript/React | UI conversacional. CSP headers, XSS prevention. |
| **Aplicación** | RAG Indexation Service | Python/Langchain/Airflow | Pipelines de ingesta con validación de integridad. |
| **Modelo** | RAG Generation Service | Python/Langgraph/Langchain | Orquestador RAG con output validation y context limits. |
| **Modelo** | Vertex AI | GCP Managed Service | Proveedor LLM externo (Gemini, Claude). |
| **Datos** | Platform Database | PostgreSQL | Datos de usuario, conversaciones, roles. RLS, cifrado en reposo. |
| **Datos** | Vector Store | PostgreSQL + pgvector | Embeddings con namespace isolation por tenant. |
| **Transversal** | Observabilidad | LangFuse/Prometheus/Grafana | Trazabilidad LLM, métricas, alertas de seguridad. |
| **Externo** | OpenText ECM | Sistema Corporativo | Fuente de documentos. Validación de integridad en ingesta. |

### 3.2 Actores y Niveles de Confianza

| Actor | Tipo | Nivel de Confianza |
|-------|------|-------------------|
| Usuario Final | Interno | Medio - Autenticado, permisos por rol |
| Usuario Técnico | Interno | Medio - API Key + JWT, scopes restringidos |
| Agente Externo [TBC] | Externo | Bajo - Requiere validación adicional |
| OpenText ECM | Sistema Externo | Medio - Fuente corporativa autorizada |
| Vertex AI | Proveedor Cloud | Alto - Servicio gestionado GCP con SLA |

---

## 4. Matriz de Riesgos SAIF

### 4.1 Riesgos de Datos

#### SAIF-DATA-001: Data Poisoning

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Inyección de datos maliciosos en el pipeline de indexación para alterar el comportamiento del modelo. |
| **Aplica** | Sí |
| **Componentes Afectados** | RAG Indexation Service, Vector Store, OpenText ECM |
| **Vector de Ataque** | Documentos maliciosos desde ECM → Indexación → Embeddings envenenados |
| **Control Implementado** | Validador de integridad en flujo ECM → Indexation que verifica hash, procedencia y ejecuta scan de malware. |
| **Control Adicional** | Validación de schema y tenant authorization antes de escribir en Vector Store. |

#### SAIF-DATA-002: Unauthorized Training Data

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Uso de datos no autorizados o sin consentimiento en el entrenamiento del modelo. |
| **Aplica** | Parcialmente |
| **Justificación** | La plataforma NO entrena modelos propios. Consume modelos pre-entrenados de Vertex AI. El riesgo aplica a los datos de indexación. |
| **Control Implementado** | Los documentos indexados provienen exclusivamente de OpenText ECM, sistema corporativo con controles de acceso propios. Solo se indexan documentos con permisos verificados. |

#### SAIF-DATA-003: Excessive Data Handling

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Recolección o procesamiento de datos más allá de lo necesario para la funcionalidad. |
| **Aplica** | Sí |
| **Componentes Afectados** | Todos los que manejan datos de usuario |
| **Control Implementado** | Pre-Embedding Sanitizer que redacta PII antes de enviar al LLM. Minimización de datos en logs. |
| **Política** | Los prompts de usuario NO se persisten para entrenamiento. Solo para auditoría con retención limitada. |

---

### 4.2 Riesgos de Infraestructura

#### SAIF-INFRA-001: Model Source Tampering

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Modificación maliciosa del código fuente del modelo o frameworks. |
| **Aplica** | Parcialmente |
| **Justificación** | No desarrollamos modelos propios. Consumimos Vertex AI (GCP managed). El riesgo aplica a nuestro código de aplicación. |
| **Control Implementado** | CI/CD con firma de commits, dependency scanning (Dependabot/Snyk), container image signing. |

#### SAIF-INFRA-002: Model Exfiltration

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Robo de pesos del modelo o arquitectura propietaria. |
| **Aplica** | No Aplica |
| **Justificación** | **Mitigado por diseño**: No almacenamos modelos localmente. Los modelos residen en Vertex AI (GCP) con sus controles de seguridad propios. |

#### SAIF-INFRA-003: Model Deployment Tampering

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Manipulación del modelo durante el despliegue. |
| **Aplica** | No Aplica |
| **Justificación** | **Mitigado por diseño**: No desplegamos modelos. Vertex AI gestiona el ciclo de vida completo del modelo. |

#### SAIF-INFRA-004: Denial of ML Service

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Ataques que degradan o impiden el funcionamiento del servicio de ML. |
| **Aplica** | Sí |
| **Componentes Afectados** | API Gateway, RAG Generation Service, Vertex AI |
| **Control Implementado** | Rate Limiting en API Gateway (configurable por tenant). Circuit breaker en conexión a Vertex AI. Auto-scaling de servicios. |

#### SAIF-INFRA-005: Insecure Integrated Component

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Vulnerabilidades en componentes de terceros integrados. |
| **Aplica** | Sí |
| **Componentes Afectados** | Langchain, Langgraph, pgvector, FastAPI |
| **Control Implementado** | Dependency scanning automático en CI/CD. Alertas de CVE. Política de actualización de dependencias con SLA de remediación por severidad. |

---

### 4.3 Riesgos de Modelo

#### SAIF-MODEL-001: Prompt Injection

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Inyección de instrucciones maliciosas en prompts para manipular el comportamiento del LLM. |
| **Aplica** | Sí - **RIESGO CRÍTICO** |
| **Componentes Afectados** | RAG Chat Frontend, API Gateway, RAG Generation Service |
| **Vector de Ataque** | Usuario → Frontend → API Gateway → RAG Generation → LLM |
| **Control Implementado** | Input/Output Guardrails - Componente dedicado con validación de patrones, detección de injection patterns, sanitización de entrada. |

#### SAIF-MODEL-002: Model Evasion

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Técnicas para evadir las defensas del modelo y obtener outputs no deseados. |
| **Aplica** | Sí |
| **Control Implementado** | Los Guardrails de entrada detectan patrones de evasión conocidos. Adversarial testing en QA. Actualización continua de patterns basada en threat intelligence. |

#### SAIF-MODEL-003: Model Reverse Engineering

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Extracción del comportamiento del modelo mediante queries sistemáticas. |
| **Aplica** | Bajo Riesgo |
| **Justificación** | Utilizamos modelos públicos de Vertex AI, no modelos propietarios. El valor está en nuestros datos y prompts, no en el modelo. |
| **Control Implementado** | Rate limiting agresivo para prevenir query exhaustivo. Logging de patrones de uso anómalos. |

---

### 4.4 Riesgos de Aplicación

#### SAIF-APP-001: Sensitive Data Disclosure

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Exposición no autorizada de datos sensibles a través de las respuestas del modelo. |
| **Aplica** | Sí - **RIESGO CRÍTICO** |
| **Componentes Afectados** | RAG Generation Service, Vector Store, API Gateway |
| **Control Implementado** | Retrieval Access Control (Multitenant Isolation) - Filtrado de embeddings por tenant/rol antes del retrieval. Output Guardrails - Validación de respuestas antes de enviar al usuario. |

#### SAIF-APP-002: Inferred Sensitive Data

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Inferencia de datos sensibles a partir de respuestas aparentemente inocuas. |
| **Aplica** | Sí |
| **Control Implementado** | Output Guardrails con detección de patrones de inferencia. Restricción de contexto disponible para el LLM basado en permisos del usuario. |

#### SAIF-APP-003: Insecure Model Output

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Outputs del modelo que contienen código malicioso, URLs peligrosos o instrucciones dañinas. |
| **Aplica** | Sí |
| **Control Implementado** | Output Guardrails - Sanitización de respuestas. Detección de URLs, código ejecutable, instrucciones de sistema. Content filtering. |

#### SAIF-APP-004: Rogue Actions

| Aspecto | Detalle |
|---------|---------|
| **Descripción** | Agentes ejecutando acciones no autorizadas o fuera del scope del usuario. |
| **Aplica** | Aplica a componentes TBC |
| **Componentes Afectados** | MCP Server [TBC], A2A Server [TBC] |
| **Control Planificado** | Agent User Control (confirmación de acciones), Agent Permissions (least privilege), Agent Observability (logging de acciones). |

---

## 5. Estado de Controles SAIF

### 5.1 Controles de Datos

| Control SAIF | Estado | Implementación |
|--------------|--------|----------------|
| Privacy Enhancing Technologies | Implementado | Pre-Embedding Sanitizer redacta PII antes del procesamiento. |
| Training Data Management | N/A | No entrenamos modelos propios. |
| Training Data Sanitization | N/A | No entrenamos modelos propios. |
| User Data Management | Implementado | Retención limitada de prompts, no uso para entrenamiento, consentimiento explícito. |

### 5.2 Controles de Infraestructura

| Control SAIF | Estado | Implementación |
|--------------|--------|----------------|
| Model and Data Inventory Management | Implementado | Registro de datasets en Platform Database. Versionado de documentos indexados. |
| Model and Data Access Controls | Implementado | RBAC + Tenant isolation + RLS en PostgreSQL. |
| Model and Data Integrity Management | Implementado | Hash de documentos, validación de integridad en ingesta. |
| Secure-by-Default ML Tooling | Implementado | Uso de Langchain/Langgraph con configuraciones seguras. Dependency scanning. |

### 5.3 Controles de Modelo

| Control SAIF | Estado | Implementación |
|--------------|--------|----------------|
| Input Validation and Sanitization | Implementado | Input Guardrails component. |
| Output Validation and Sanitization | Implementado | Output Guardrails + PII filtering en respuestas. |
| Adversarial Training and Testing | Planificado | Red teaming programado pre-producción. |

### 5.4 Controles de Aplicación

| Control SAIF | Estado | Implementación |
|--------------|--------|----------------|
| Application Access Management | Implementado | OAuth 2.0 + JWT + RBAC. |
| User Transparency and Controls | Implementado | Disclosure de uso de IA en UI. Control de historial. |
| Agent User Control | TBC | Pendiente para MCP/A2A. |
| Agent Permissions | TBC | Pendiente para MCP/A2A. |
| Agent Observability | TBC | Pendiente para MCP/A2A. |

### 5.5 Controles de Assurance

| Control SAIF | Estado | Implementación |
|--------------|--------|----------------|
| Red Teaming | Planificado | Ejercicios de red team pre-producción y trimestrales. |
| Vulnerability Management | Implementado | Dependabot + Snyk + SLA de remediación por severidad. |
| Threat Detection | Implementado | Security Monitoring/SIEM Integration. |
| Incident Response Management | Implementado | Runbooks definidos, escalación automática, RTO/RPO documentados. |

### 5.6 Controles de Governance

| Control SAIF | Estado | Implementación |
|--------------|--------|----------------|
| User Policies and Education | Planificado | Políticas de uso aceptable pendientes. |
| Internal Policies and Education | Implementado | Capacitación de equipo en seguridad de IA. |
| Product Governance | Implementado | Review de seguridad en cada release. |
| Risk Governance | Implementado | Este documento + revisión trimestral. |

---

## 6. Riesgos Específicos del Dominio Bancario

### 6.1 Riesgos Regulatorios

| Riesgo | Control |
|--------|---------|
| Incumplimiento de retención de datos | Políticas de retención configurables por tenant según regulación local. |
| Falta de auditoría de acceso | Audit trail completo en Platform Database + SIEM. |
| Uso de datos de clientes sin consentimiento | Disclosure explícito en UI, opt-in requerido. |

### 6.2 Riesgos de Negocio

| Riesgo | Control |
|--------|---------|
| Respuestas incorrectas en contexto financiero | Guardrails específicos para disclaimers. Contexto con fuentes citables. |
| Generación de consejos financieros no autorizados | Detección de patrones de "asesoría" en output. Filtrado automático. |
| Acceso a documentos de otros tenants | Namespace isolation estricto. RLS en todas las queries. Testing de penetración específico. |

---

## 7. Referencias

### 7.1 Documentación Interna

| Área | Documento | Sección Relevante |
|------|-----------|-------------------|
| Autenticación y Autorización | `03_c4-container-api-gateway.md` | Sección 11: Modelo de Seguridad |
| Middleware de Seguridad | `03_c4-container-api-gateway.md` | Sección 5.1: Middleware Pipeline |
| Pipeline de Indexación | `05_c4-container-rag-indexing-service.md` | Sección 10: Manejo de Errores |
| Arquitectura de Contenedores | `02_c4-containers.md` | Vista general de componentes |

### 7.2 Referencias Externas

| Framework | URL | Descripción |
|-----------|-----|-------------|
| Google SAIF | https://saif.google/secure-ai-framework/ | Framework de seguridad para sistemas de IA |
| GCP Well-Architected Framework - Security | https://cloud.google.com/architecture/framework/security | Pilares de seguridad, privacidad y cumplimiento |

---

## 8. Referencias

- Para definiciones de términos técnicos, consultar el glosario en `docs/arc42/12_glossary.md`.
