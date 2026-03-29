# Backlog Celula Agentica — Plataforma IA Enterprise

> Generado: 26/02/2026
> Base: Gantt BC+IA (25/02/2026) + Roadmap IA Detallado (20/02/2026)
> Equipo: Celula Agentica (IA - ITMind)
> Proyecto Jira: BC-AI (sugerido)
> **Metodologia: PERT** — Te = (O + 4M + P) / 6

## Convenciones


| Simbolo   | Significado                                                           |
| --------- | --------------------------------------------------------------------- |
| **EPIC**  | Agrupacion principal dentro de cada etapa (Epic en Jira)              |
| TAREA     | Tarea ejecutable por el equipo IA (Story/Task en Jira)                |
| ↳ SUB     | Subtarea de una tarea (Sub-task en Jira)                              |
| **[DEP]** | Dependencia externa — item de seguimiento, no ejecutado por equipo IA |
| **[+]**   | Tarea adicional recomendada (no esta en el Gantt original)            |
| **Ref**   | ID de referencia en el Gantt compartido BC+IA                         |


**Columnas PERT:**


| Columna | Significado                                                |
| ------- | ---------------------------------------------------------- |
| Opt.    | Duracion optimista (O) — mejor escenario, en dias          |
| Prob.   | Duracion probable (M) — escenario mas frecuente, en dias   |
| Pes.    | Duracion pesimista (P) — peor escenario razonable, en dias |
| Te      | Tiempo estimado PERT = (O + 4M + P) / 6, en dias           |


**Notas sobre fechas:** Las fechas con `~` son estimadas usando Te PERT. Las tareas sin fecha dependen de entregables del Banco o xECM. Las fechas de ETAPA 3+ reflejan el impacto acumulado de la distribucion PERT sobre la ruta critica.

---

## ETAPA 1: CONEXION

### EPIC: Instalacion Servidores IA

> Estado: **COMPLETADO**
> Provision y despliegue de servicios de infraestructura IA en Google Cloud.
> Ref Gantt: Id 19 | Duracion Gantt: 2 dias


| Tipo  | ID     | Nombre Tarea                       | Opt. | Prob. | Pes. | Te  | Pred.  | %    | Comienzo | Fin   | Ref |
| ----- | ------ | ---------------------------------- | ---- | ----- | ---- | --- | ------ | ---- | -------- | ----- | --- |
| TAREA | AI-001 | Instalacion Airflow + Langfuse     | 2    | 2     | 2    | 2.0 | —      | 100% | 23/02    | 24/02 | 20  |
| TAREA | AI-002 | Instalacion VectorDB + Platform DB | 1    | 1     | 1    | 1.0 | —      | 100% | 23/02    | 23/02 | 21  |
| TAREA | AI-003 | Instalacion IA Platform            | 1    | 1     | 1    | 1.0 | AI-002 | 100% | 24/02    | 24/02 | 22  |


**Resumen EPIC: 3 tareas | 3/3 completadas (100%)**

---

## ETAPA 2: REALIZACION

### EPIC: Configuracion Infraestructura y Plataforma IA DEV

> Configuracion tecnica de infraestructura, bases de datos, pipeline y plataforma en ambiente DEV.
> Ref Gantt: Id 54 | Duracion Gantt: 16 dias | Comienzo: 02/03 | Fin estimado: 25/03

#### Dependencias externas


| Tipo  | ID      | Dependencia                                               | Equipo | Estado | Fecha Est. | Impacta a      | Ref |
| ----- | ------- | --------------------------------------------------------- | ------ | ------ | ---------- | -------------- | --- |
| [DEP] | DEP-001 | xECM instalado y operativo                                | xECM   | ~50%   | 20-24/02   | AI-007         | 14  |
| [DEP] | DEP-002 | Configuracion xECM completa (carpetas, categorias, roles) | xECM   | 0%     | Sem. 9-10  | AI-008, AI-009 | 34  |


#### Tareas


| Tipo  | ID       | Nombre Tarea                                                                   | Opt. | Prob. | Pes. | Te  | Pred.                   | %    | Comienzo | Fin    | Ref |
| ----- | -------- | ------------------------------------------------------------------------------ | ---- | ----- | ---- | --- | ----------------------- | ---- | -------- | ------ | --- |
| TAREA | AI-004   | Configuracion VectorDB + Platform DB                                           | 1.5  | 2     | 3    | 2.1 | AI-003                  | 80%  | 02/03    | 03/03  | 56  |
| ↳ SUB | AI-004.1 | Configuracion indices pgvector y esquema HNSW en DEV                           | 0.25 | 0.5   | 1    | 0.5 | —                       | 100% | 02/03    | 02/03  | —   |
| ↳ SUB | AI-004.2 | Aplicacion migraciones Alembic en ambiente DEV                                 | 0.25 | 0.5   | 0.75 | 0.5 | —                       | 100% | 02/03    | 02/03  | —   |
| ↳ SUB | AI-004.3 | Carga datos base (roles, configuracion inicial)                                | 0.25 | 0.5   | 1    | 0.5 | AI-004.2                | 50%  | 03/03    | 03/03  | —   |
| ↳ SUB | AI-004.4 | Verificacion rendimiento busqueda vectorial en DEV                             | 0.25 | 0.5   | 1.5  | 0.6 | AI-004.1                | 50%  | 03/03    | 03/03  | —   |
| TAREA | AI-005   | Configuracion Pipeline de Documentos                                           | 2    | 3     | 5    | 3.2 | AI-004                  | 60%  | 04/03    | 07/03  | 57  |
| ↳ SUB | AI-005.1 | Configuracion adaptive chunker (parametros, overlap, deteccion area funcional) | 0.5  | 1     | 2    | 1.1 | —                       | 100% | 04/03    | 04/03  | —   |
| ↳ SUB | AI-005.2 | Configuracion Gemini embedding service (768d, halfvec)                         | 0.25 | 0.5   | 1    | 0.5 | —                       | 100% | 04/03    | 04/03  | —   |
| ↳ SUB | AI-005.3 | Prueba procesamiento completo documento (carga, fragmentacion, almacenamiento) | 0.5  | 1     | 2.5  | 1.2 | AI-005.1, AI-005.2      | 30%  | 05/03    | 06/03  | —   |
| ↳ SUB | AI-005.4 | Validacion calidad fragmentacion y metadatos                                   | 0.25 | 0.5   | 1.5  | 0.6 | AI-005.3                | 0%   | 07/03    | 07/03  | —   |
| TAREA | AI-006   | Configuracion Plataforma IA                                                    | 2    | 3     | 5    | 3.2 | AI-004                  | 55%  | 04/03    | 07/03  | 58  |
| ↳ SUB | AI-006.1 | Configuracion endpoints API (health, chat, documents, conversations)           | 0.25 | 0.5   | 1    | 0.5 | —                       | 100% | 04/03    | 04/03  | —   |
| ↳ SUB | AI-006.2 | Configuracion middleware seguridad (CORS, auth JWT, rate limit)                | 0.25 | 0.5   | 1.5  | 0.6 | —                       | 80%  | 04/03    | 04/03  | —   |
| ↳ SUB | AI-006.3 | Despliegue contenedorizado en DEV (Docker + Helm)                              | 0.5  | 1     | 2.5  | 1.2 | AI-006.1                | 70%  | 05/03    | 06/03  | —   |
| ↳ SUB | AI-006.4 | Configuracion Langfuse (trazabilidad, metricas, costos)                        | 0.25 | 0.5   | 1    | 0.5 | AI-006.3                | 60%  | 07/03    | 07/03  | —   |
| ↳ SUB | AI-006.5 | [+] Configuracion monitoreo GCP (dashboards, alertas)                          | 0.25 | 0.5   | 1.5  | 0.6 | AI-006.3                | 30%  | 07/03    | 07/03  | —   |
| TAREA | AI-007   | Conexion interna xECM                                                          | 0.5  | 1     | 3    | 1.3 | DEP-001                 | 10%  | ~10/03   | ~11/03 | 55  |
| ↳ SUB | AI-007.1 | Configurar cliente API conexion a Content Server                               | 0.25 | 0.5   | 2    | 0.7 | —                       | 20%  | ~10/03   | ~10/03 | —   |
| ↳ SUB | AI-007.2 | Prueba conectividad y acceso a documentos desde plataforma IA                  | 0.25 | 0.5   | 1.5  | 0.6 | AI-007.1                | 0%   | ~11/03   | ~11/03 | —   |
| TAREA | AI-008   | Sincronizacion xECM Roles y Permisos - Metadata                                | 0.5  | 1     | 2    | 1.1 | AI-006, AI-005, DEP-002 | 0%   | ~20/03   | ~21/03 | 59  |
| ↳ SUB | AI-008.1 | Diseno tablas sincronizacion permisos                                          | 0.25 | 0.5   | 1    | 0.5 | —                       | 0%   | ~20/03   | ~20/03 | —   |
| ↳ SUB | AI-008.2 | Implementacion sincronizacion inicial roles y permisos desde xECM              | 0.25 | 0.5   | 1.5  | 0.6 | AI-008.1                | 0%   | ~21/03   | ~21/03 | —   |
| TAREA | AI-009   | Testing plataforma interna IA                                                  | 0.5  | 1     | 2    | 1.1 | AI-008                  | 30%  | ~25/03   | ~26/03 | 60  |
| ↳ SUB | AI-009.1 | Pruebas integracion sistema completo en DEV                                    | 0.25 | 0.5   | 1.5  | 0.6 | —                       | 40%  | ~25/03   | ~25/03 | —   |
| ↳ SUB | AI-009.2 | Pruebas autenticacion y autorizacion                                           | 0.25 | 0.25  | 0.5  | 0.3 | —                       | 50%  | ~25/03   | ~25/03 | —   |
| ↳ SUB | AI-009.3 | Correccion errores detectados y validacion interna                             | 0.25 | 0.25  | 0.75 | 0.3 | AI-009.1                | 0%   | ~26/03   | ~26/03 | —   |


**Resumen EPIC: 6 tareas, 14 subtareas | Progreso promedio: ~40%**

---

### EPIC: Desarrollo y Entrenamiento Pipeline RAG

> Desarrollo del pipeline RAG completo, configuracion del modelo de lenguaje, guardrails, frontend y ajuste de calidad.
> Ref Gantt: Id 61 (Entrenamiento IA) | Duracion Gantt: 23 dias | Comienzo: 25/02 | Fin estimado: ~30/03

#### Dependencias externas


| Tipo  | ID      | Dependencia                                         | Equipo | Estado    | Fecha Est.    | Impacta a        | Ref |
| ----- | ------- | --------------------------------------------------- | ------ | --------- | ------------- | ---------------- | --- |
| [DEP] | DEP-003 | Disponibilizacion informacion para entrenamiento IA | Banco  | 0%        | Pendiente     | AI-016           | 62  |
| [DEP] | DEP-004 | Personalidad y tono del agente                      | Banco  | Pendiente | Reunion 24/02 | AI-014           | —   |
| [DEP] | DEP-005 | Mensajes de fallback aprobados                      | Banco  | Pendiente | Reunion 24/02 | AI-014           | —   |
| [DEP] | DEP-006 | Lista temas prohibidos (Compliance)                 | Banco  | Pendiente | Reunion 24/02 | AI-013           | —   |
| [DEP] | DEP-007 | Consultas reales con respuestas esperadas           | Banco  | Pendiente | Reunion 26/02 | AI-017.3, AI-019 | —   |
| [DEP] | DEP-008 | Branding y assets visuales (logo, colores, nombre)  | Banco  | Pendiente | Reunion 24/02 | AI-014.3         | —   |


#### Tareas


| Tipo  | ID       | Nombre Tarea                                                             | Opt. | Prob. | Pes. | Te  | Pred.                             | %   | Comienzo | Fin    | Ref |
| ----- | -------- | ------------------------------------------------------------------------ | ---- | ----- | ---- | --- | --------------------------------- | --- | -------- | ------ | --- |
| TAREA | AI-010   | Configuracion modelo lenguaje (Gemini)                                   | 1.5  | 2     | 3    | 2.1 | AI-003                            | 50% | 25/02    | 27/02  | 63  |
| ↳ SUB | AI-010.1 | Seleccion y configuracion modelo Gemini (version, parametros)            | 0.25 | 0.5   | 1    | 0.5 | —                                 | 80% | 25/02    | 25/02  | —   |
| ↳ SUB | AI-010.2 | Diseno system prompt principal (instrucciones, contexto, restricciones)  | 0.5  | 1     | 2    | 1.1 | AI-010.1                          | 30% | 25/02    | 26/02  | —   |
| ↳ SUB | AI-010.3 | Configuracion parametros generacion (temperature, top-k, max tokens)     | 0.25 | 0.5   | 1    | 0.5 | AI-010.1                          | 40% | 27/02    | 27/02  | —   |
| TAREA | AI-011   | Configuracion pipeline RAG (retrieval + generacion)                      | 3    | 4     | 6    | 4.2 | AI-010, AI-005                    | 65% | 27/02    | 05/03  | 63  |
| ↳ SUB | AI-011.1 | Configuracion busqueda hibrida (Vector + BM25 + RRF)                     | 0.5  | 1     | 2    | 1.1 | —                                 | 90% | 27/02    | 28/02  | —   |
| ↳ SUB | AI-011.2 | Configuracion reranking (Vertex AI)                                      | 0.25 | 0.5   | 1.5  | 0.6 | AI-011.1                          | 80% | 28/02    | 28/02  | —   |
| ↳ SUB | AI-011.3 | Configuracion streaming SSE para respuestas en tiempo real               | 0.25 | 0.5   | 1    | 0.5 | —                                 | 90% | 28/02    | 28/02  | —   |
| ↳ SUB | AI-011.4 | Configuracion sistema citaciones (fuentes documentales en respuestas)    | 0.25 | 0.5   | 1.5  | 0.6 | AI-011.1                          | 40% | 03/03    | 03/03  | —   |
| ↳ SUB | AI-011.5 | Integracion LangGraph state machine (orquestacion nodos RAG)             | 0.5  | 1     | 2    | 1.1 | AI-011.1                          | 70% | 03/03    | 04/03  | —   |
| ↳ SUB | AI-011.6 | [+] Configuracion cache semantico de consultas                           | 0.25 | 0.5   | 1.5  | 0.6 | AI-011.1                          | 0%  | 05/03    | 05/03  | —   |
| TAREA | AI-012   | [+] Desarrollo Frontend (Login + Chat UI)                                | 4    | 5     | 8    | 5.3 | AI-006                            | 0%  | ~07/03   | ~14/03 | —   |
| ↳ SUB | AI-012.1 | Scaffold proyecto Next.js y configuracion base                           | 0.25 | 0.5   | 1    | 0.5 | —                                 | 0%  | ~07/03   | ~07/03 | —   |
| ↳ SUB | AI-012.2 | Pantalla de login con autenticacion JWT                                  | 1    | 1.5   | 3    | 1.7 | AI-012.1                          | 0%  | ~07/03   | ~10/03 | —   |
| ↳ SUB | AI-012.3 | Chat UI con streaming SSE y renderizado markdown                         | 1.5  | 2     | 4    | 2.3 | AI-012.1                          | 0%  | ~10/03   | ~12/03 | —   |
| ↳ SUB | AI-012.4 | Integracion citaciones, feedback y sidebar conversaciones                | 0.5  | 1     | 2    | 1.1 | AI-012.3                          | 0%  | ~12/03   | ~14/03 | —   |
| TAREA | AI-013   | Configuracion filtros de seguridad (entrada y salida)                    | 1.5  | 2     | 4    | 2.3 | AI-010, DEP-006                   | 40% | ~03/03   | ~05/03 | 63  |
| ↳ SUB | AI-013.1 | Input guardrails (deteccion prompt injection, jailbreak, PII en entrada) | 0.5  | 1     | 2    | 1.1 | —                                 | 70% | ~03/03   | ~03/03 | —   |
| ↳ SUB | AI-013.2 | Output guardrails (control tematico, deteccion PII basico en salida)     | 0.25 | 0.5   | 1.5  | 0.6 | —                                 | 20% | ~04/03   | ~04/03 | —   |
| ↳ SUB | AI-013.3 | Configuracion lista temas prohibidos (Compliance bancario)               | 0.25 | 0.5   | 1    | 0.5 | DEP-006                           | 0%  | —        | —      | —   |
| TAREA | AI-014   | Aplicacion personalidad, tono y branding                                 | 1    | 2     | 3    | 2.0 | DEP-004, DEP-005, DEP-008, AI-010 | 0%  | —        | —      | 63  |
| ↳ SUB | AI-014.1 | Aplicacion personalidad y tono en system prompt                          | 0.25 | 0.5   | 1    | 0.5 | DEP-004                           | 0%  | —        | —      | —   |
| ↳ SUB | AI-014.2 | Configuracion mensajes fallback aprobados por el banco                   | 0.25 | 0.5   | 1    | 0.5 | DEP-005                           | 0%  | —        | —      | —   |
| ↳ SUB | AI-014.3 | Aplicacion branding interfaz (logo, colores, nombre del asistente)       | 0.5  | 1     | 2    | 1.1 | DEP-008                           | 0%  | —        | —      | —   |
| TAREA | AI-015   | [+] Configuracion observabilidad completa                                | 1    | 2     | 3    | 2.0 | AI-011                            | 40% | ~05/03   | ~07/03 | —   |
| ↳ SUB | AI-015.1 | Instrumentacion traces Langfuse en pipeline RAG completo                 | 0.5  | 1     | 1.5  | 1.0 | —                                 | 60% | ~05/03   | ~06/03 | —   |
| ↳ SUB | AI-015.2 | Configuracion metricas de calidad (RAGAS) y seguimiento costos           | 0.25 | 0.5   | 1.5  | 0.6 | AI-015.1                          | 20% | ~06/03   | ~07/03 | —   |
| ↳ SUB | AI-015.3 | [+] Configuracion dashboards monitoreo GCP                               | 0.25 | 0.5   | 1    | 0.5 | AI-015.1                          | 0%  | ~07/03   | ~07/03 | —   |
| TAREA | AI-016   | Carga y procesamiento dataset documentos                                 | 2    | 3     | 5    | 3.2 | AI-005, DEP-003                   | 0%  | —        | —      | 63  |
| ↳ SUB | AI-016.1 | Carga documentos de prueba iniciales (sinteticos)                        | 0.25 | 0.5   | 1    | 0.5 | AI-005                            | 10% | —        | —      | —   |
| ↳ SUB | AI-016.2 | Validacion calidad extraccion y fragmentacion con docs reales            | 0.5  | 1     | 2    | 1.1 | AI-016.1                          | 0%  | —        | —      | —   |
| ↳ SUB | AI-016.3 | Carga dataset definitivo del banco                                       | 0.5  | 1     | 2    | 1.1 | DEP-003                           | 0%  | —        | —      | —   |
| ↳ SUB | AI-016.4 | Verificacion cobertura e integridad del indice                           | 0.25 | 0.5   | 1    | 0.5 | AI-016.3                          | 0%  | —        | —      | —   |
| TAREA | AI-017   | Ajuste y refinamiento RAG                                                | 3    | 5     | 10   | 5.5 | AI-011, AI-016                    | 0%  | —        | —      | 63  |
| ↳ SUB | AI-017.1 | Ajuste parametros busqueda (top-k, similarity threshold, chunk overlap)  | 1    | 2     | 4    | 2.2 | —                                 | 0%  | —        | —      | —   |
| ↳ SUB | AI-017.2 | Optimizacion respuestas segun personalidad y tono definidos              | 0.5  | 1     | 2    | 1.1 | AI-014                            | 0%  | —        | —      | —   |
| ↳ SUB | AI-017.3 | Validacion calidad respuestas contra escenarios esperados del banco      | 0.5  | 1     | 3    | 1.3 | DEP-007                           | 0%  | —        | —      | —   |
| ↳ SUB | AI-017.4 | Ajuste filtros seguridad con casos reales bancarios                      | 0.5  | 1     | 2    | 1.1 | AI-013                            | 0%  | —        | —      | —   |
| TAREA | AI-018   | Pruebas DEV                                                              | 1    | 2     | 4    | 2.2 | AI-017, DEP-002                   | 0%  | ~28/03   | ~01/04 | 64  |
| ↳ SUB | AI-018.1 | Pruebas end-to-end pipeline RAG completo                                 | 0.5  | 1     | 2    | 1.1 | —                                 | 0%  | ~28/03   | ~28/03 | —   |
| ↳ SUB | AI-018.2 | Pruebas rendimiento y latencia bajo carga                                | 0.25 | 0.5   | 1.5  | 0.6 | —                                 | 0%  | ~31/03   | ~31/03 | —   |
| ↳ SUB | AI-018.3 | Correccion errores detectados                                            | 0.25 | 0.5   | 1.5  | 0.6 | AI-018.1                          | 0%  | ~01/04   | ~01/04 | —   |


**Resumen EPIC: 9 tareas, 27 subtareas | Progreso promedio: ~25%**

---

### EPIC: Validacion Escenarios IA con xECM

> Validacion del sistema con datos reales de xECM, escenarios del banco y transporte a QAS.
> Ref Gantt: Id 65 | Duracion Gantt: 7 dias | Comienzo: ~20/03 | Fin estimado: ~03/04


| Tipo  | ID       | Nombre Tarea                                                  | Opt. | Prob. | Pes. | Te  | Pred.              | %   | Comienzo | Fin    | Ref |
| ----- | -------- | ------------------------------------------------------------- | ---- | ----- | ---- | --- | ------------------ | --- | -------- | ------ | --- |
| TAREA | AI-019   | Configuracion escenarios prueba representativos               | 2    | 3     | 5    | 3.2 | DEP-007, DEP-002   | 0%  | ~20/03   | ~25/03 | 65  |
| ↳ SUB | AI-019.1 | Diseno escenarios CAT (catalogo) con documentos xECM          | 0.5  | 1     | 2    | 1.1 | —                  | 0%  | ~20/03   | ~21/03 | —   |
| ↳ SUB | AI-019.2 | Diseno escenarios RRHH con documentos xECM                    | 0.5  | 1     | 2    | 1.1 | —                  | 0%  | ~21/03   | ~22/03 | —   |
| ↳ SUB | AI-019.3 | Validacion cobertura escenarios vs consultas reales del banco | 0.5  | 1     | 2    | 1.1 | AI-019.1, AI-019.2 | 0%  | ~24/03   | ~25/03 | —   |
| TAREA | AI-020   | Integracion y validacion con datos xECM reales                | 2    | 3     | 5    | 3.2 | AI-019, AI-007     | 0%  | ~25/03   | ~28/03 | 65  |
| ↳ SUB | AI-020.1 | Pruebas consultas con documentos reales de Content Server     | 1    | 1.5   | 3    | 1.7 | —                  | 0%  | ~25/03   | ~26/03 | —   |
| ↳ SUB | AI-020.2 | Ajuste respuestas segun contexto documental xECM              | 1    | 1.5   | 3    | 1.7 | AI-020.1           | 0%  | ~27/03   | ~28/03 | —   |
| TAREA | AI-021   | Transporte configuracion DEV a QAS                            | 1    | 2     | 4    | 2.2 | AI-018, AI-020     | 0%  | ~01/04   | ~03/04 | 66  |
| ↳ SUB | AI-021.1 | Migracion configuracion, datos y modelos a ambiente QAS       | 0.5  | 1     | 2.5  | 1.2 | —                  | 0%  | ~01/04   | ~02/04 | —   |
| ↳ SUB | AI-021.2 | Validacion funcional completa en QAS                          | 0.5  | 1     | 2    | 1.1 | AI-021.1           | 0%  | ~02/04   | ~03/04 | —   |


**Resumen EPIC: 3 tareas, 7 subtareas | Progreso: 0%**

---

### EPIC: Pruebas QAS y Capacitacion Key Users IA

> Pruebas en ambiente QAS, capacitacion a usuarios clave y entrega de material borrador.
> Ref Gantt: Id 67 (parcial IA) | Comienzo: ~07/04 | Fin estimado: ~17/04


| Tipo  | ID       | Nombre Tarea                                                     | Opt. | Prob. | Pes. | Te  | Pred.                  | %   | Comienzo | Fin    | Ref |
| ----- | -------- | ---------------------------------------------------------------- | ---- | ----- | ---- | --- | ---------------------- | --- | -------- | ------ | --- |
| TAREA | AI-022   | Disponibilizacion script pruebas QAS                             | 0.5  | 1     | 2    | 1.1 | AI-021                 | 0%  | ~07/04   | ~07/04 | 72  |
| TAREA | AI-023   | Capacitacion key users IA                                        | 1    | 1     | 1    | 1.0 | AI-022                 | 0%  | ~07/04   | ~07/04 | 73  |
| ↳ SUB | AI-023.1 | Sesion capacitacion key users CAT                                | 0.5  | 0.5   | 0.5  | 0.5 | —                      | 0%  | ~07/04   | ~07/04 | 74  |
| ↳ SUB | AI-023.2 | Sesion capacitacion key users RRHH                               | 0.5  | 0.5   | 0.5  | 0.5 | —                      | 0%  | ~07/04   | ~07/04 | 75  |
| TAREA | AI-024   | Entrega material soporte funcional (Draft)                       | 0.5  | 1     | 2    | 1.1 | AI-022                 | 0%  | ~08/04   | ~08/04 | 76  |
| TAREA | AI-025   | Entrega material soporte tecnico (Draft)                         | 0.5  | 1     | 2    | 1.1 | AI-022                 | 0%  | ~08/04   | ~08/04 | 77  |
| TAREA | AI-026   | Pruebas QAS                                                      | 3    | 5     | 8    | 5.2 | AI-023, AI-024, AI-025 | 0%  | ~08/04   | ~15/04 | 78  |
| ↳ SUB | AI-026.1 | Ejecucion pruebas funcionales end-to-end en QAS                  | 1    | 2     | 4    | 2.2 | —                      | 0%  | ~08/04   | ~10/04 | —   |
| ↳ SUB | AI-026.2 | Ejecucion pruebas no funcionales (rendimiento, seguridad basica) | 1    | 1.5   | 3    | 1.7 | —                      | 0%  | ~10/04   | ~11/04 | —   |
| ↳ SUB | AI-026.3 | Correccion errores detectados en QAS                             | 1    | 1.5   | 3    | 1.7 | AI-026.1               | 0%  | ~11/04   | ~15/04 | —   |


**Resumen EPIC: 5 tareas, 5 subtareas | Progreso: 0%**

---

## ETAPA 3: PREPARACION FINAL

### EPIC: Preproduccion y Seguridad IA

> Preparacion del ambiente productivo y desarrollo de componentes criticos de seguridad (Bloques B y D del roadmap).
> Estos bloques son pre-requisitos para go-live y NO estan en el Gantt original.
> Ref Gantt: Id 89 | Duracion Gantt: 5 dias | **Nuestro estimado Te PERT: 5.5d (ruta critica Bloque B)**
>
> **RIESGO:** El Gantt asigna 5 dias para preproduccion IA. Incluimos Bloques B (permisos documentales)
> y D (filtros seguridad avanzados) que son criticos para produccion bancaria. Se ejecutan en paralelo
> para minimizar impacto en timeline. σ combinada Bloques B+D = 1.17d.

#### Dependencias externas


| Tipo  | ID      | Dependencia                               | Equipo | Estado | Fecha Est. | Impacta a | Ref |
| ----- | ------- | ----------------------------------------- | ------ | ------ | ---------- | --------- | --- |
| [DEP] | DEP-009 | xECM con permisos listos para sincronizar | xECM   | 0%     | Sem. 12-13 | AI-029    | —   |


#### Tareas


| Tipo  | ID       | Nombre Tarea                                                            | Opt. | Prob. | Pes. | Te  | Pred.              | %   | Comienzo | Fin    | Ref |
| ----- | -------- | ----------------------------------------------------------------------- | ---- | ----- | ---- | --- | ------------------ | --- | -------- | ------ | --- |
| TAREA | AI-027   | Preparacion ambiente produccion                                         | 1    | 2     | 4    | 2.2 | AI-026             | 0%  | ~16/04   | ~17/04 | 89  |
| ↳ SUB | AI-027.1 | Configuracion infraestructura PRD (GKE, Cloud SQL, secrets, networking) | 0.5  | 1     | 2.5  | 1.2 | —                  | 0%  | ~16/04   | ~16/04 | —   |
| ↳ SUB | AI-027.2 | Configuracion monitoreo y alertas produccion                            | 0.25 | 0.5   | 1    | 0.5 | AI-027.1           | 0%  | ~17/04   | ~17/04 | —   |
| ↳ SUB | AI-027.3 | Configuracion backups y plan disaster recovery                          | 0.25 | 0.5   | 1.5  | 0.6 | AI-027.1           | 0%  | ~17/04   | ~17/04 | —   |
| TAREA | AI-028   | [+] Filtros de seguridad avanzados (Bloque D)                           | 3    | 5     | 8    | 5.2 | AI-026, AI-013     | 0%  | ~16/04   | ~23/04 | —   |
| ↳ SUB | AI-028.1 | Deteccion automatica datos sensibles (DNI, CUIT, CBU) en respuestas     | 1    | 2     | 4    | 2.2 | —                  | 0%  | ~16/04   | ~17/04 | —   |
| ↳ SUB | AI-028.2 | Validacion automatica fidelidad respuestas vs documentos fuente         | 1    | 2     | 4    | 2.2 | —                  | 0%  | ~18/04   | ~21/04 | —   |
| ↳ SUB | AI-028.3 | Control tematico reforzado (solo dominio bancario autorizado)           | 0.5  | 1     | 2    | 1.1 | AI-028.1           | 0%  | ~22/04   | ~23/04 | —   |
| TAREA | AI-029   | [+] Permisos y seguridad documental (Bloque B)                          | 3    | 5     | 10   | 5.5 | AI-008, DEP-009    | 0%  | ~16/04   | ~23/04 | —   |
| ↳ SUB | AI-029.1 | Sincronizacion permisos desde OpenText Content Server                   | 1    | 2     | 4    | 2.2 | DEP-009            | 0%  | ~16/04   | ~17/04 | —   |
| ↳ SUB | AI-029.2 | Filtrado resultados busqueda segun permisos del usuario                 | 1    | 1.5   | 3    | 1.7 | AI-029.1           | 0%  | ~18/04   | ~21/04 | —   |
| ↳ SUB | AI-029.3 | Sincronizacion automatica periodica de cambios de permisos              | 0.5  | 1     | 2    | 1.1 | AI-029.1           | 0%  | ~18/04   | ~18/04 | —   |
| ↳ SUB | AI-029.4 | Pruebas permisos con datos reales xECM (grupos, herencia)               | 0.25 | 0.5   | 2    | 0.7 | AI-029.2           | 0%  | ~22/04   | ~23/04 | —   |
| TAREA | AI-030   | [+] Testing integrado pre-produccion                                    | 2    | 3     | 5    | 3.2 | AI-028, AI-029     | 0%  | ~23/04   | ~28/04 | —   |
| ↳ SUB | AI-030.1 | Pruebas integracion completa (MVP + permisos + filtros avanzados)       | 0.5  | 1     | 2    | 1.1 | —                  | 0%  | ~23/04   | ~24/04 | —   |
| ↳ SUB | AI-030.2 | Pruebas seguridad pre-go-live (OWASP Top 10 + LLM Top 10)               | 0.5  | 1     | 2    | 1.1 | —                  | 0%  | ~24/04   | ~25/04 | —   |
| ↳ SUB | AI-030.3 | Validacion rendimiento sistema completo bajo carga simulada             | 0.25 | 0.5   | 1    | 0.5 | —                  | 0%  | ~25/04   | ~25/04 | —   |
| ↳ SUB | AI-030.4 | Correccion errores criticos y aprobacion interna go-live                | 0.25 | 0.5   | 2    | 0.7 | AI-030.1, AI-030.2 | 0%  | ~25/04   | ~28/04 | —   |


**Resumen EPIC: 4 tareas, 14 subtareas | Progreso: 0%**

---

### EPIC: Cutover IA a Produccion

> Despliegue de la version final en ambiente productivo, migracion de datos y validacion.
> Ref Gantt: Id 91 | Duracion Gantt: 5 dias | Comienzo estimado: ~28/04


| Tipo  | ID       | Nombre Tarea                                                 | Opt. | Prob. | Pes. | Te  | Pred.              | %   | Comienzo | Fin    | Ref |
| ----- | -------- | ------------------------------------------------------------ | ---- | ----- | ---- | --- | ------------------ | --- | -------- | ------ | --- |
| TAREA | AI-031   | Despliegue version final en produccion                       | 1    | 2     | 3    | 2.0 | AI-030             | 0%  | ~28/04   | ~29/04 | 91  |
| ↳ SUB | AI-031.1 | Deploy plataforma IA en PRD via Helm (GKE)                   | 0.5  | 1     | 2    | 1.1 | —                  | 0%  | ~28/04   | ~28/04 | —   |
| ↳ SUB | AI-031.2 | Validacion estabilidad post-despliegue (health checks, logs) | 0.25 | 0.5   | 1    | 0.5 | AI-031.1           | 0%  | ~29/04   | ~29/04 | —   |
| ↳ SUB | AI-031.3 | Activacion monitoreo y alertas produccion                    | 0.25 | 0.5   | 1    | 0.5 | AI-031.1           | 0%  | ~29/04   | ~29/04 | —   |
| TAREA | AI-032   | Migracion datos y configuracion a PRD                        | 1    | 2     | 4    | 2.2 | AI-031             | 0%  | ~29/04   | ~02/05 | 91  |
| ↳ SUB | AI-032.1 | Migracion VectorDB (embeddings, documentos indexados)        | 0.5  | 1     | 2.5  | 1.2 | —                  | 0%  | ~29/04   | ~30/04 | —   |
| ↳ SUB | AI-032.2 | Migracion Platform DB (usuarios, roles, configuracion)       | 0.25 | 0.5   | 1    | 0.5 | —                  | 0%  | ~30/04   | ~30/04 | —   |
| ↳ SUB | AI-032.3 | Verificacion integridad datos post-migracion                 | 0.25 | 0.5   | 1.5  | 0.6 | AI-032.1, AI-032.2 | 0%  | ~02/05   | ~02/05 | —   |
| TAREA | AI-033   | Smoke test produccion                                        | 0.5  | 1     | 2    | 1.1 | AI-032             | 0%  | ~02/05   | ~02/05 | 91  |


**Resumen EPIC: 3 tareas, 6 subtareas | Progreso: 0%**

---

### EPIC: Pruebas de Aceptacion Pre Go-Live

> Pruebas de aceptacion (UAT) por usuarios clave del banco antes del go-live.
> Ref Gantt: Id 93-95 | Duracion Gantt: 2 dias | Comienzo: ~02/05


| Tipo  | ID     | Nombre Tarea                             | Opt. | Prob. | Pes. | Te  | Pred.          | %   | Comienzo | Fin    | Ref |
| ----- | ------ | ---------------------------------------- | ---- | ----- | ---- | --- | -------------- | --- | -------- | ------ | --- |
| TAREA | AI-034 | Pruebas aceptacion con key users CAT+IA  | 1    | 2     | 3    | 2.0 | AI-033         | 0%  | ~02/05   | ~05/05 | 94  |
| TAREA | AI-035 | Pruebas aceptacion con key users RRHH+IA | 1    | 2     | 3    | 2.0 | AI-033         | 0%  | ~02/05   | ~05/05 | 95  |
| TAREA | AI-036 | Resolucion observaciones criticas UAT    | 1    | 2     | 5    | 2.3 | AI-034, AI-035 | 0%  | ~05/05   | ~07/05 | —   |


**Resumen EPIC: 3 tareas | Progreso: 0%**

---

### EPIC: Capacitacion Usuarios Finales

> Capacitacion a usuarios finales del banco y entrega de material de soporte definitivo.
> Ref Gantt: Id 96-102 | Comienzo: ~07/05


| Tipo  | ID     | Nombre Tarea                                    | Opt. | Prob. | Pes. | Te  | Pred.          | %   | Comienzo | Fin    | Ref |
| ----- | ------ | ----------------------------------------------- | ---- | ----- | ---- | --- | -------------- | --- | -------- | ------ | --- |
| TAREA | AI-037 | Entrega material soporte funcional (definitivo) | 0.5  | 1     | 1.5  | 1.0 | AI-036         | 0%  | ~07/05   | ~07/05 | 98  |
| TAREA | AI-038 | Entrega material soporte tecnico (definitivo)   | 0.5  | 1     | 1.5  | 1.0 | AI-036         | 0%  | ~07/05   | ~07/05 | 99  |
| TAREA | AI-039 | Sesion capacitacion usuarios finales CAT        | 0.5  | 1     | 1.5  | 1.0 | AI-037, AI-038 | 0%  | ~08/05   | ~08/05 | 100 |
| TAREA | AI-040 | Sesion capacitacion usuarios finales RRHH       | 0.5  | 1     | 1.5  | 1.0 | AI-037, AI-038 | 0%  | ~08/05   | ~08/05 | 101 |
| TAREA | AI-041 | Sesion capacitacion IT                          | 0.5  | 1     | 1.5  | 1.0 | AI-037, AI-038 | 0%  | ~08/05   | ~08/05 | 102 |


**Resumen EPIC: 5 tareas | Progreso: 0%**

---

## ETAPA 4: LANZAMIENTO

### EPIC: Go-Live BC+IA

> Puesta en produccion y monitoreo activo inicial.
> Ref Gantt: Id 103-105 | Duracion Gantt: 5 dias | Go-Live: ~08/05


| Tipo  | ID       | Nombre Tarea                                                  | Opt. | Prob. | Pes. | Te  | Pred.    | %   | Comienzo | Fin    | Ref |
| ----- | -------- | ------------------------------------------------------------- | ---- | ----- | ---- | --- | -------- | --- | -------- | ------ | --- |
| TAREA | AI-042   | Go-Live IA en produccion                                      | 3    | 5     | 7    | 5.0 | AI-036   | 0%  | ~08/05   | ~14/05 | 104 |
| ↳ SUB | AI-042.1 | Comunicacion go-live al banco y stakeholders                  | 0.25 | 0.5   | 1    | 0.5 | —        | 0%  | ~08/05   | ~08/05 | —   |
| ↳ SUB | AI-042.2 | Activacion accesos usuarios finales                           | 0.25 | 0.5   | 1    | 0.5 | —        | 0%  | ~08/05   | ~08/05 | —   |
| ↳ SUB | AI-042.3 | Monitoreo activo primeras 48h (rendimiento, errores, calidad) | 1.5  | 2     | 3    | 2.1 | AI-042.1 | 0%  | ~08/05   | ~12/05 | —   |
| ↳ SUB | AI-042.4 | Soporte incidencias primeros dias                             | 1.5  | 2     | 3    | 2.1 | AI-042.1 | 0%  | ~08/05   | ~12/05 | —   |


**Resumen EPIC: 1 tarea, 4 subtareas | Progreso: 0%**

---

## ETAPA 5: SOPORTE Y MEJORAS

### EPIC: Soporte Post-Go Live BC+IA

> Soporte, estabilizacion y ajuste fino post-lanzamiento.
> Ref Gantt: Id 106-108 | Duracion Gantt: 10 dias | Comienzo: ~14/05 | Fin: ~28/05


| Tipo  | ID       | Nombre Tarea                                       | Opt. | Prob. | Pes. | Te   | Pred.    | %   | Comienzo | Fin    | Ref |
| ----- | -------- | -------------------------------------------------- | ---- | ----- | ---- | ---- | -------- | --- | -------- | ------ | --- |
| TAREA | AI-043   | Soporte post-go live y estabilizacion              | 7    | 10    | 15   | 10.3 | AI-042   | 0%  | ~14/05   | ~28/05 | 107 |
| ↳ SUB | AI-043.1 | Monitoreo activo rendimiento y calidad respuestas  | 3    | 5     | 8    | 5.2  | —        | 0%  | ~14/05   | ~20/05 | —   |
| ↳ SUB | AI-043.2 | Resolucion incidencias reportadas por usuarios     | 3    | 5     | 8    | 5.2  | —        | 0%  | ~14/05   | ~20/05 | —   |
| ↳ SUB | AI-043.3 | Ajuste fino RAG basado en feedback usuarios reales | 2    | 3     | 5    | 3.2  | AI-043.1 | 0%  | ~21/05   | ~25/05 | —   |
| ↳ SUB | AI-043.4 | Informe cierre de proyecto y metricas finales      | 0.5  | 1     | 2    | 1.1  | AI-043.3 | 0%  | ~28/05   | ~28/05 | —   |


**Resumen EPIC: 1 tarea, 4 subtareas | Progreso: 0%**

---

## Analisis PERT — Ruta Critica

### Formula

```
Te = (O + 4M + P) / 6
σ  = (P - O) / 6
σ² = varianza de cada tarea
```

### Ruta critica identificada

La ruta critica atraviesa las siguientes tareas principales:


| #   | ID     | Nombre Tarea                        | Te       | σ    | σ²       |
| --- | ------ | ----------------------------------- | -------- | ---- | -------- |
| 1   | AI-004 | Config VectorDB + Platform DB       | 2.1      | 0.25 | 0.063    |
| 2   | AI-005 | Config Pipeline Documentos          | 3.2      | 0.50 | 0.250    |
| 3   | AI-011 | Config pipeline RAG                 | 4.2      | 0.50 | 0.250    |
| 4   | AI-017 | Ajuste y refinamiento RAG           | 5.5      | 1.17 | 1.361    |
| 5   | AI-018 | Pruebas DEV                         | 2.2      | 0.50 | 0.250    |
| 6   | AI-021 | Transporte DEV a QAS                | 2.2      | 0.50 | 0.250    |
| 7   | AI-026 | Pruebas QAS                         | 5.2      | 0.83 | 0.694    |
| 8   | AI-029 | Permisos y seguridad documental (B) | 5.5      | 1.17 | 1.361    |
| 9   | AI-030 | Testing integrado pre-produccion    | 3.2      | 0.50 | 0.250    |
| 10  | AI-031 | Deploy version final PRD            | 2.0      | 0.33 | 0.111    |
| 11  | AI-032 | Migracion datos a PRD               | 2.2      | 0.50 | 0.250    |
| 12  | AI-033 | Smoke test PRD                      | 1.1      | 0.25 | 0.063    |
| 13  | AI-034 | UAT key users CAT                   | 2.0      | 0.33 | 0.111    |
| 14  | AI-036 | Resolucion observaciones UAT        | 2.3      | 0.67 | 0.444    |
| 15  | AI-042 | Go-Live IA en produccion            | 5.0      | 0.67 | 0.444    |
|     | **Σ**  | **Total ruta critica**              | **47.8** | —    | **6.15** |


### Intervalos de confianza


| Nivel confianza   | Multiplicador | Buffer (dias) | Go-Live estimado |
| ----------------- | ------------- | ------------- | ---------------- |
| 50% (Te)          | 0             | 0             | ~08/05           |
| 68% (Te + 1σ)     | 1.00          | 2.5           | ~12/05           |
| 90% (Te + 1.28σ)  | 1.28          | 3.2           | ~13/05           |
| 95% (Te + 1.645σ) | 1.645         | 4.1           | ~14/05           |
| 99% (Te + 2.33σ)  | 2.33          | 5.8           | ~16/05           |


> **σ total ruta critica = √6.15 ≈ 2.48 dias**

### Comparativa Gantt vs PERT


| Escenario          | Go-Live | Fin Soporte | Delta vs Gantt |
| ------------------ | ------- | ----------- | -------------- |
| Gantt original     | 28/04   | 15/05       | —              |
| PERT Te (50%)      | ~08/05  | ~28/05      | +7 dias hab.   |
| PERT 95% confianza | ~14/05  | ~02/06      | +11 dias hab.  |


### Tareas de mayor riesgo (σ > 0.8)


| ID     | Nombre Tarea                   | Te  | σ    | Riesgo                                           |
| ------ | ------------------------------ | --- | ---- | ------------------------------------------------ |
| AI-017 | Ajuste y refinamiento RAG      | 5.5 | 1.17 | Depende de calidad dataset y expectativas banco  |
| AI-029 | Permisos documental (Bloque B) | 5.5 | 1.17 | Depende de xECM (DEP-009) + complejidad permisos |
| AI-026 | Pruebas QAS                    | 5.2 | 0.83 | Volumen de errores impredecible                  |


**Mitigacion:** Estas 3 tareas concentran el **56% de la varianza total** de la ruta critica (σ² = 3.42 de 6.15). Mitigar cualquiera de ellas reduce significativamente la incertidumbre del proyecto.

---

## Resumen Consolidado

### Por Etapa y Epic


| Etapa                | Epic                                              | Tareas | Subtareas | Te Total | % Promedio |
| -------------------- | ------------------------------------------------- | ------ | --------- | -------- | ---------- |
| 1. Conexion          | Instalacion Servidores IA                         | 3      | 0         | 4.0d     | **100%**   |
| 2. Realizacion       | Configuracion Infraestructura y Plataforma IA DEV | 6      | 14        | 12.1d    | ~40%       |
| 2. Realizacion       | Desarrollo y Entrenamiento Pipeline RAG           | 9      | 27        | 26.8d    | ~25%       |
| 2. Realizacion       | Validacion Escenarios IA con xECM                 | 3      | 7         | 8.6d     | 0%         |
| 2. Realizacion       | Pruebas QAS y Capacitacion Key Users IA           | 5      | 5         | 9.5d     | 0%         |
| 3. Preparacion Final | Preproduccion y Seguridad IA                      | 4      | 14        | 16.1d    | 0%         |
| 3. Preparacion Final | Cutover IA a Produccion                           | 3      | 6         | 5.3d     | 0%         |
| 3. Preparacion Final | Pruebas de Aceptacion Pre Go-Live                 | 3      | 0         | 6.3d     | 0%         |
| 3. Preparacion Final | Capacitacion Usuarios Finales                     | 5      | 0         | 5.0d     | 0%         |
| 4. Lanzamiento       | Go-Live BC+IA                                     | 1      | 4         | 5.0d     | 0%         |
| 5. Soporte           | Soporte Post-Go Live BC+IA                        | 1      | 4         | 10.3d    | 0%         |
| **TOTAL**            | **11 Epics**                                      | **43** | **81**    | **109d** | —          |


### Totales


| Concepto                              | Cantidad  |
| ------------------------------------- | --------- |
| Etapas                                | 5         |
| Epics                                 | 11        |
| Tareas ejecutables (IA)               | 43        |
| Subtareas                             | 81        |
| Dependencias externas ([DEP])         | 9         |
| Tareas recomendadas adicionales ([+]) | 7         |
| **Total items backlog**               | **134**   |
| **Te total ruta critica**             | **47.8d** |
| **σ ruta critica**                    | **2.48d** |


---

## Dependencias Externas Consolidadas


| ID      | Dependencia                                        | Equipo | Fecha Comprometida | Estado    | Bloquea                | Ref Gantt |
| ------- | -------------------------------------------------- | ------ | ------------------ | --------- | ---------------------- | --------- |
| DEP-001 | xECM instalado y operativo                         | xECM   | 20-24/02           | ~50%      | AI-007                 | 14        |
| DEP-002 | Config xECM completa (carpetas, categorias, roles) | xECM   | Sem. 9-10 (~Mar)   | 0%        | AI-008, AI-009, AI-019 | 34        |
| DEP-003 | Dataset documentos para entrenamiento IA           | Banco  | Pendiente          | 0%        | AI-016                 | 62        |
| DEP-004 | Personalidad y tono del agente                     | Banco  | Reunion 24/02      | Pendiente | AI-014.1               | —         |
| DEP-005 | Mensajes fallback aprobados                        | Banco  | Reunion 24/02      | Pendiente | AI-014.2               | —         |
| DEP-006 | Lista temas prohibidos (Compliance)                | Banco  | Reunion 24/02      | Pendiente | AI-013.3               | —         |
| DEP-007 | Consultas reales con respuestas esperadas          | Banco  | Reunion 26/02      | Pendiente | AI-017.3, AI-019       | —         |
| DEP-008 | Branding y assets visuales (logo, colores, nombre) | Banco  | Reunion 24/02      | Pendiente | AI-014.3               | —         |
| DEP-009 | xECM con permisos listos para sincronizar          | xECM   | Sem. 12-13 (~Abr)  | 0%        | AI-029                 | —         |


---

## Riesgos y Observaciones

### 1. Go-Live: Gantt vs PERT

El Gantt original estima go-live el **28/04**. El analisis PERT con Te situa el go-live en **~08/05** (+7 dias habiles). Con un **95% de confianza**, el go-live se estima en **~14/05** (+11 dias habiles). La diferencia se debe al efecto acumulado de la asimetria pesimista en tareas de alta incertidumbre (AI-017, AI-029, AI-026).

### 2. Preproduccion: Bloques B y D

El Gantt asigna **5 dias** para "Tareas de preproduccion IA" (Id 89). Nuestro backlog incluye los **Bloques B (permisos documentales, Te=5.5d, σ=1.17d) y D (filtros seguridad avanzados, Te=5.2d, σ=0.83d)** que se ejecutan en paralelo.

**Mitigacion:** Ejecucion paralela de Bloques B y D limita el impacto a la duracion del bloque mas largo (B, Te=5.5d). El testing integrado post-bloques (AI-030, Te=3.2d) no puede comenzar hasta completar ambos.

### 3. Frontend no contemplado en Gantt

El Gantt compartido no tiene una tarea especifica para el **desarrollo del frontend** (Next.js: login + chat UI). Lo incluimos como **AI-012 (Te=5.3d, σ=0.67d)** dentro de la etapa de Realizacion. No esta en la ruta critica si se ejecuta en paralelo con el pipeline RAG.

### 4. Dependencias del Banco sin confirmar

Las reuniones del **24/02 y 26/02** debian entregar insumos criticos:

- Personalidad y tono del agente (DEP-004)
- Mensajes fallback (DEP-005)
- Lista temas prohibidos (DEP-006)
- Consultas reales con respuestas esperadas (DEP-007)
- Branding (DEP-008)

**Si no se recibieron**, las tareas AI-013.3, AI-014 y AI-019 estan **bloqueadas**. Se recomienda escalar en la proxima reunion de seguimiento.

### 5. xECM Permisos (DEP-009) — Riesgo Critico

El Bloque B de permisos documentales depende de que xECM tenga los permisos configurados para **Sem. 12-13**. AI-029 esta en la **ruta critica** con σ=1.17d (la mayor varianza junto con AI-017). Si DEP-009 se retrasa, impacta directamente la fecha de go-live sin workaround posible.

### 6. Concentracion de varianza

Tres tareas (AI-017, AI-029, AI-026) concentran el **56% de la varianza total** del proyecto. Reducir la incertidumbre en cualquiera de ellas (por ej. con sesiones tempranas de validacion, prototipos de permisos, o pruebas QAS incrementales) tiene el mayor impacto en la predecibilidad del timeline.

---

## Hitos Clave del Equipo IA (ajustados PERT)


| Fecha PERT | Fecha Gantt | Hito                                                 | Dependencia Critica     |
| ---------- | ----------- | ---------------------------------------------------- | ----------------------- |
| 24/02      | 24/02       | Servidores IA instalados y operativos                | —                       |
| ~07/03     | ~06/03      | Configuracion infraestructura DEV completada         | DEP-001 (xECM)          |
| ~14/03     | ~13/03      | Frontend (login + chat) listo para pruebas internas  | —                       |
| ~21/03     | ~20/03      | Pipeline RAG configurado y funcional                 | DEP-003 (dataset)       |
| ~26/03     | ~25/03      | Testing plataforma interna completado                | DEP-002 (config xECM)   |
| ~03/04     | ~01/04      | Transporte DEV a QAS completado                      | —                       |
| ~15/04     | ~13/04      | **Fin Etapa Realizacion** — Pruebas QAS completadas  | —                       |
| ~23/04     | ~20/04      | Bloques B y D completados (seguridad pre-produccion) | DEP-009 (permisos xECM) |
| ~28/04     | ~23/04      | Testing integrado pre-produccion aprobado            | —                       |
| ~02/05     | ~25/04      | Cutover a produccion completado                      | —                       |
| **~08/05** | **~28/04**  | **Go-Live IA en produccion**                         | Aprobacion banco        |
| ~14/05     | —           | Go-Live al 95% confianza PERT                        | Buffer varianza         |
| ~28/05     | ~15/05      | Fin soporte post-go live                             | —                       |


