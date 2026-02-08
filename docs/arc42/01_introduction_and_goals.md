# 1. Introducción y Objetivos

## 1.1 Objetivo del Proyecto

“Integrar nuestro sistema de IA a los documentos del banco Macro para consultas 
internas en lenguaje natural, que entregue **respuestas correctas y sustentadas con citas**, respetando **roles y permisos**, con **trazabilidad/auditoría** por interacción, y cumpliendo slo de **latencia/QPS** definidos, 
validado contra un set de evaluación representativo del negocio.”

---

## 1.2 Requisitos de Alto Nivel

### Métricas Clave de Calidad

| Métrica | Objetivo | Descripción |
|---------|----------|-------------|
| **Faithfulness/Factualidad** | > 90% | Respuestas sin alucinaciones, sustentadas en evidencia documental |
| **Context Precision** | > 80% | Precisión en la recuperación de documentos relevantes |
| **Latencia P95** | < 3 segundos | Tiempo de respuesta en el percentil 95 |
| **Disponibilidad** | > 99.5% | Uptime del sistema en producción |
| **Cumplimiento de permisos** | 100% | Respeto de políticas de seguridad y permisos del Gestor Documental |

---

## 1.3 Stakeholders

### Actores del Sistema

| Actor | Tipo | Descripción |
|-------|------|-------------|
| **Usuario Final** | Persona | Empleado de la organización que utiliza la interfaz de chat conversacional para consultas en lenguaje natural |
| **Usuario Técnico** | Persona | Empleado de la organización que integra sus sistemas mediante API REST/WebSocket |
| **Equipo de Soporte** | Persona | Responsable de atender escalamientos (HIDL) y gestionar incidentes |
| **Área de Compliance** | Persona | Responsable de auditoría, cumplimiento normativo y validación de políticas de seguridad |

### Dimensionamiento de Usuarios

| Parámetro | Valor | Notas |
|-----------|-------|-------|
| Base de usuarios | 6,000 | Referencia técnica para dimensionamiento |
| Usuarios intensivos diarios | ~540 (9%) | Usuarios con uso frecuente del sistema |
| Usuarios concurrentes estimados | ~100 | Según información de Banco Macro |
| QPS en picos | 30 | Durante 6 horas diarias, 22 días/mes |

> **Nota**: La referencia de usuarios es técnica (para capacidad/costos) y **no implica una limitación funcional** en la cantidad de usuarios.

### Sistemas Externos

| Sistema | Descripción | Rol |
|---------|-------------|-----|
| **OpenText ECM (Azure)** | Sistema de gestión documental corporativo | Fuente principal de documentos para indexación |
| **SQL Server (Azure)** | Base de datos relacional | Fuente de datos estructurados |
| **Vertex AI** | Proveedor de modelos LLM y embeddings | Generación de embeddings y respuestas |

---

## 1.4 Drivers de Calidad

Los siguientes atributos de calidad guían las decisiones arquitectónicas del sistema:

### 1.4.1 Precisión y Confiabilidad

| Driver | Descripción | Criterio de Éxito |
|--------|-------------|-------------------|
| **Respuestas con evidencia** | Toda respuesta debe estar sustentada con citas de documentos fuente | 100% de respuestas muestran al menos 1 cita cuando existe evidencia |
| **Reducción de alucinaciones** | El sistema debe minimizar respuestas inventadas o sin fundamento | Faithfulness > 90% en set de evaluación |
| **Manejo de incertidumbre** | Cuando no hay información, el sistema debe indicarlo claramente | Respuesta "no encontrado/no puedo responder con evidencia" sin inventar |

### 1.4.2 Trazabilidad y Auditoría

| Driver | Descripción | Criterio de Éxito |
|--------|-------------|-------------------|
| **Trazabilidad por interacción** | Cada interacción debe tener un identificador único para auditoría | Trace ID en cada respuesta |
| **Registro de decisiones** | Cada decisión del sistema debe quedar registrada | Log de: entrada, docs usados, decisión de guardrails, salida |
| **Explicabilidad** | Capacidad de demostrar "por qué el sistema dijo lo que dijo" | Árbol de decisión auditable |

### 1.4.3 Seguridad y Cumplimiento

| Driver | Descripción | Criterio de Éxito |
|--------|-------------|-------------------|
| **Roles y permisos** | El sistema debe respetar los permisos del Gestor Documental | 0% de accesos a contenido no autorizado |
| **Protección de PII** | Detección y manejo de información personal identificable | Bloqueo/anonimización según política |
| **Anti prompt-injection** | Protección contra ataques de manipulación de prompts | Bloqueo/neutralización/log de intentos |
| **Escalamiento a humano** | Capacidad de derivar a soporte cuando corresponda | HIDL implementado y funcional |

### 1.4.4 Rendimiento

| Driver | Descripción | Criterio de Éxito |
|--------|-------------|-------------------|
| **Latencia** | Tiempo de respuesta aceptable para usuarios | P95 < 3s, P50 < 1.5s, P99 < 5s |
| **Throughput** | Capacidad de atender carga esperada | 30 QPS en picos |
| **Disponibilidad** | Sistema operativo cuando se necesita | > 99.5% uptime |

### 1.4.5 Operabilidad

| Driver | Descripción | Criterio de Éxito |
|--------|-------------|-------------------|
| **Observabilidad** | Visibilidad del estado y comportamiento del sistema | Métricas, logs y trazas integradas |
| **Mantenibilidad** | Facilidad para operar y actualizar el sistema | Runbook operativo, rollout/rollback documentado |
| **Recuperabilidad** | Capacidad de recuperación ante fallas | RTO 4h, RPO 24h para logs |

---

## 1.5 Arquitectura

Para una vista de alto nivel del sistema y sus interacciones, asi como detalles especificos de la **arquitectura** ver:
- **Diagrama C4 Contexto**: [`diagrams/01-c4-context.drawio.svg`](diagrams/01-c4-context.drawio.svg)
- **Diagrama C4 Contenedores**: [`diagrams/02-c4-contenedores.drawio.svg`](diagrams/02-c4-contenedores.drawio.svg)
- **Detalle de la arquitectura**: [`c4-details`](c4-details)
