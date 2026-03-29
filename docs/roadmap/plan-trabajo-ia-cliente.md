# Plan de Trabajo — Componente Inteligencia Artificial

## Proyecto BC+AI

> Fecha: 26/02/2026
> Equipo: Celula Agentica (ITMind)
> Alcance: Plataforma de consulta inteligente sobre corpus documental gestionado por OpenText Content Server

---

## Resumen Ejecutivo

El componente de Inteligencia Artificial del proyecto BC+AI implementa una plataforma de consulta inteligente que permite a los usuarios del banco realizar preguntas sobre documentos gestionados en OpenText Content Server, obteniendo respuestas precisas con citacion de fuentes, permisos documentales y controles de seguridad bancaria.

### Fechas clave


| Hito | Fecha |
| ---- | ----- |
| Inicio desarrollo | 25/02/2026 |
| Infraestructura DEV configurada | ~06/03/2026 |
| Interfaz usuario lista para pruebas internas | ~13/03/2026 |
| Sistema calibrado y funcional | ~23/03/2026 |
| Pruebas QAS finalizadas | ~10/04/2026 |
| Seguridad pre-produccion validada | ~17/04/2026 |
| **Go-Live** | **~24/04/2026** |
| Fin soporte post-go-live | ~07/05/2026 |


---

## Coordinacion Requerida

El avance del componente IA depende de los siguientes entregables del proyecto. Los retrasos en estos entregables impactan directamente las fechas de las tareas dependientes.


| # | Entregable | Responsable | Fecha Requerida | Impacta |
| - | ---------- | ----------- | --------------- | ------- |
| 1 | OpenText Content Server instalado y operativo | Equipo xECM | ~10/03 | Integracion IA-xECM |
| 2 | Configuracion xECM completa (carpetas, categorias, roles) | Equipo xECM | ~20/03 | Validacion con escenarios reales |
| 3 | Corpus documental representativo para entrenamiento | Banco | ~12/03 | Procesamiento y calibracion del sistema |
| 4 | Definiciones funcionales (personalidad del asistente, temas permitidos, mensajes, branding) | Banco | ~07/03 | Configuracion seguridad y experiencia de usuario |
| 5 | Escenarios de prueba (consultas reales con respuestas esperadas) | Banco | ~17/03 | Calibracion y validacion de calidad |
| 6 | Permisos documentales configurados en xECM | Equipo xECM | ~11/04 | Seguridad pre-produccion |


---

## Plan de Trabajo por Etapa

### ETAPA 1: CONEXION — Completada

#### EPIC: Instalacion Servidores IA

> Provision y despliegue de servicios de infraestructura IA en Google Cloud.
> Estado: **COMPLETADA**


| ID    | Tarea                                            | Descripcion                                             | Dur. | Comienzo | Fin   | Predecesores | Coordinacion | Estado     |
| ----- | ------------------------------------------------ | ------------------------------------------------------- | ---- | -------- | ----- | ------------ | ------------ | ---------- |
| IA-01 | Instalacion y configuracion servidores IA en GCP | Airflow + Langfuse; VectorDB + Platform DB; IA Platform | 2d   | 23/02    | 24/02 | —            | —            | Completada |


---

### ETAPA 2: REALIZACION (~25/02 - ~10/04)

#### EPIC: Configuracion Infraestructura y Plataforma IA DEV

> Configuracion tecnica de infraestructura, bases de datos, pipeline e integracion con xECM en ambiente DEV.
> Comienzo: ~02/03 | Fin estimado: ~26/03


| ID    | Tarea                                          | Descripcion                                                                                | Dur. | Comienzo | Fin    | Predecesores   | Coordinacion  | Estado    |
| ----- | ---------------------------------------------- | ------------------------------------------------------------------------------------------ | ---- | -------- | ------ | -------------- | ------------- | --------- |
| IA-02 | Configuracion bases de datos                   | Config pgvector HNSW; Migraciones Alembic; Carga datos base; Verificacion rendimiento      | 2d   | ~02/03   | ~03/03 | IA-01          | —             | En curso  |
| IA-03 | Configuracion pipeline de documentos           | Config adaptive chunker; Gemini embedding 768d; Procesamiento completo; Validacion calidad  | 3d   | ~04/03   | ~06/03 | IA-02          | —             | En curso  |
| IA-04 | Configuracion plataforma IA y despliegue       | Endpoints API; Middleware seguridad (CORS, JWT, rate limit); Despliegue Docker + Helm; Langfuse; Monitoreo GCP | 3d   | ~02/03   | ~04/03 | IA-02          | —             | En curso  |
| IA-05 | Conexion con OpenText Content Server           | Cliente API Content Server; Prueba conectividad y acceso documentos                        | 2d   | ~10/03   | ~11/03 | —              | Entregable #1 | Pendiente |
| IA-06 | Sincronizacion metadata y permisos xECM        | Tablas sincronizacion permisos; Sincronizacion roles y permisos xECM                       | 1d   | ~20/03   | ~21/03 | IA-03, IA-04   | Entregable #2 | Pendiente |
| IA-07 | Testing interno plataforma                     | Pruebas integracion DEV; Pruebas auth; Correccion errores                                  | 1d   | ~25/03   | ~26/03 | IA-06          | —             | Pendiente |


#### EPIC: Desarrollo y Entrenamiento del Sistema IA

> Desarrollo del sistema completo: modelo de lenguaje, motor de busqueda, interfaz, seguridad, observabilidad y calibracion.
> Comienzo: ~25/02 | Fin estimado: ~28/03


| ID    | Tarea                                                     | Descripcion                                                                                   | Dur. | Comienzo | Fin    | Predecesores   | Coordinacion  | Estado    |
| ----- | --------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ---- | -------- | ------ | -------------- | ------------- | --------- |
| IA-08 | Configuracion modelo de lenguaje (Gemini)                 | Seleccion modelo Gemini; System prompt; Parametros generacion                                 | 2d   | ~25/02   | ~26/02 | IA-01          | —             | En curso  |
| IA-09 | Configuracion pipeline RAG                                | Busqueda hibrida Vector+BM25+RRF; Reranking Vertex AI; Streaming SSE                         | 2d   | ~27/02   | ~03/03 | IA-08, IA-03   | —             | En curso  |
| IA-10 | Integracion y optimizacion pipeline RAG                   | Sistema citaciones; LangGraph state machine; Cache semantico                                  | 2d   | ~04/03   | ~06/03 | IA-09          | —             | En curso  |
| IA-11 | Desarrollo interfaz de usuario — estructura base          | Scaffold Next.js; Login JWT; Chat UI streaming SSE y markdown                                 | 3d   | ~07/03   | ~11/03 | IA-04          | —             | Pendiente |
| IA-12 | Desarrollo interfaz de usuario — integraciones            | Citaciones y feedback; Sidebar conversaciones                                                 | 2d   | ~12/03   | ~13/03 | IA-11          | —             | Pendiente |
| IA-13 | Configuracion seguridad, compliance y personalizacion     | Input guardrails (prompt injection, PII); Output guardrails; Temas prohibidos; Personalidad, tono y branding | 3d   | ~03/03   | ~07/03 | IA-08          | Entregable #4 | En curso  |
| IA-14 | Configuracion observabilidad y monitoreo                  | Instrumentacion traces Langfuse; Metricas RAGAS y costos; Dashboards monitoreo GCP            | 2d   | ~05/03   | ~07/03 | IA-10          | —             | En curso  |
| IA-15 | Procesamiento corpus documental                           | Carga docs prueba; Validacion extraccion; Carga dataset definitivo; Verificacion cobertura indice | 3d   | ~12/03   | ~16/03 | IA-03          | Entregable #3 | Pendiente |
| IA-16 | Calibracion del sistema — parametros y respuestas         | Ajuste parametros busqueda (top-k, similarity, chunk overlap); Optimizacion respuestas segun personalidad | 3d   | ~17/03   | ~19/03 | IA-10, IA-15   | Entregable #5 | Pendiente |
| IA-17 | Calibracion del sistema — validacion y ajustes            | Validacion respuestas vs escenarios esperados; Ajuste filtros seguridad con casos reales      | 2d   | ~20/03   | ~23/03 | IA-16          | Entregable #5 | Pendiente |
| IA-18 | Pruebas integracion DEV                                   | Pruebas e2e pipeline RAG; Rendimiento y latencia; Correccion errores                          | 2d   | ~27/03   | ~28/03 | IA-17          | —             | Pendiente |


#### EPIC: Validacion Escenarios IA con xECM

> Validacion del sistema con datos reales de xECM, escenarios del banco y transporte a QAS.
> Comienzo: ~20/03 | Fin estimado: ~31/03


| ID    | Tarea                                                 | Descripcion                                                                                  | Dur. | Comienzo | Fin    | Predecesores   | Coordinacion        | Estado    |
| ----- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------- | ---- | -------- | ------ | -------------- | ------------------- | --------- |
| IA-19 | Configuracion escenarios de prueba con xECM           | Escenarios CAT con docs xECM; Escenarios RRHH con docs xECM; Validacion cobertura           | 3d   | ~20/03   | ~23/03 | —              | Entregables #2 y #5 | Pendiente |
| IA-20 | Validacion con datos reales xECM                      | Consultas con documentos reales Content Server; Ajuste respuestas contexto xECM              | 2d   | ~24/03   | ~26/03 | IA-19, IA-05   | —                   | Pendiente |
| IA-21 | Transporte configuracion DEV a QAS                    | Migracion config, datos y modelos a QAS; Validacion funcional QAS                            | 2d   | ~27/03   | ~31/03 | IA-18, IA-20   | —                   | Pendiente |


#### EPIC: Pruebas QAS y Capacitacion Key Users IA

> Pruebas en ambiente QAS, capacitacion a usuarios clave y entrega de material soporte.
> Comienzo: ~02/04 | Fin estimado: ~10/04


| ID    | Tarea                                                 | Descripcion                                                                                  | Dur. | Comienzo | Fin    | Predecesores | Coordinacion | Estado    |
| ----- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------- | ---- | -------- | ------ | ------------ | ------------ | --------- |
| IA-22 | Capacitacion key users y entrega material soporte     | Script pruebas; Sesiones capacitacion key users CAT y RRHH; Material soporte funcional y tecnico (Draft) | 2d   | ~02/04   | ~03/04 | IA-21        | —            | Pendiente |
| IA-23 | Pruebas QAS — funcionales y no funcionales            | Pruebas funcionales e2e en QAS; Pruebas no funcionales (rendimiento, seguridad basica)       | 3d   | ~04/04   | ~07/04 | IA-22        | —            | Pendiente |
| IA-24 | Pruebas QAS — correccion y estabilizacion             | Correccion errores detectados en QAS; Re-verificacion y estabilizacion                       | 2d   | ~08/04   | ~10/04 | IA-23        | —            | Pendiente |


---

### ETAPA 3: PREPARACION FINAL (~13/04 - ~23/04)

#### EPIC: Preproduccion y Seguridad IA

> Configuracion del ambiente productivo y validacion de componentes de seguridad (permisos documentales y filtros avanzados).
> Comienzo: ~13/04 | Fin estimado: ~21/04


| ID    | Tarea                                                      | Descripcion                                                                                  | Dur. | Comienzo | Fin    | Predecesores   | Coordinacion  | Estado    |
| ----- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ---- | -------- | ------ | -------------- | ------------- | --------- |
| IA-25 | Configuracion ambiente produccion                          | Config infra PRD (GKE, Cloud SQL, secrets); Monitoreo y alertas; Backups y DR                | 2d   | ~13/04   | ~14/04 | IA-24          | —             | Pendiente |
| IA-26 | Seguridad pre-produccion — filtros avanzados               | Deteccion PII (DNI, CUIT, CBU); Validacion fidelidad respuestas vs documentos; Control tematico | 3d   | ~13/04   | ~15/04 | IA-24, IA-13   | —             | Pendiente |
| IA-27 | Seguridad pre-produccion — permisos documentales           | Sync permisos OpenText; Filtrado resultados segun permisos; Sync periodica; Pruebas permisos | 2d   | ~16/04   | ~17/04 | IA-06          | Entregable #6 | Pendiente |
| IA-28 | Testing integrado pre-produccion                           | Pruebas integracion completa; Seguridad OWASP; Rendimiento bajo carga; Correccion criticos   | 2d   | ~20/04   | ~21/04 | IA-26, IA-27   | —             | Pendiente |


#### EPIC: Cutover IA a Produccion

> Despliegue de la version final en ambiente productivo, migracion de datos y verificacion.
> Comienzo: ~20/04 | Fin estimado: ~22/04


| ID    | Tarea                                                 | Descripcion                                                                                  | Dur. | Comienzo | Fin    | Predecesores | Coordinacion | Estado    |
| ----- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------- | ---- | -------- | ------ | ------------ | ------------ | --------- |
| IA-29 | Despliegue, migracion y verificacion en produccion    | Deploy Helm PRD; Validacion post-despliegue; Migracion VectorDB y PlatformDB; Smoke test     | 2d   | ~21/04   | ~22/04 | IA-28        | —            | Pendiente |


#### EPIC: Pruebas de Aceptacion Pre Go-Live

> Pruebas de aceptacion (UAT) por usuarios clave del banco antes del go-live.
> Comienzo: ~22/04 | Fin estimado: ~23/04


| ID    | Tarea                                                 | Descripcion                                                                                  | Dur. | Comienzo | Fin    | Predecesores | Coordinacion | Estado    |
| ----- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------- | ---- | -------- | ------ | ------------ | ------------ | --------- |
| IA-30 | Pruebas de aceptacion con key users y ajustes         | UAT key users CAT y RRHH; Resolucion observaciones criticas                                  | 2d   | ~22/04   | ~23/04 | IA-29        | —            | Pendiente |


#### EPIC: Capacitacion Usuarios Finales

> Entrega de material de soporte definitivo y capacitacion a usuarios finales del banco.
> Comienzo: ~22/04 | Fin estimado: ~23/04


| ID    | Tarea                                                 | Descripcion                                                                                  | Dur. | Comienzo | Fin    | Predecesores | Coordinacion | Estado    |
| ----- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------- | ---- | -------- | ------ | ------------ | ------------ | --------- |
| IA-31 | Entrega material definitivo y capacitacion usuarios   | Material soporte funcional y tecnico definitivo; Capacitacion usuarios CAT, RRHH e IT        | 2d   | ~22/04   | ~23/04 | IA-30        | —            | Pendiente |


---

### ETAPA 4: LANZAMIENTO (~24/04)

#### EPIC: Go-Live BC+IA

> Puesta en produccion y activacion del sistema para usuarios finales.


| ID    | Tarea                                                 | Descripcion                                                                                  | Dur. | Comienzo | Fin    | Predecesores   | Coordinacion     | Estado    |
| ----- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------- | ---- | -------- | ------ | -------------- | ---------------- | --------- |
| IA-32 | Go-Live componente IA en produccion                   | Comunicacion go-live; Activacion accesos usuarios finales; Monitoreo inicial                  | 1d   | ~24/04   | ~24/04 | IA-30, IA-31   | Aprobacion banco | Pendiente |


---

### ETAPA 5: SOPORTE Y MEJORAS (~24/04 - ~07/05)

#### EPIC: Soporte Post-Go Live BC+IA

> Soporte activo, estabilizacion y ajuste fino post-lanzamiento.


| ID    | Tarea                                                 | Descripcion                                                                                  | Dur. | Comienzo | Fin    | Predecesores | Coordinacion | Estado    |
| ----- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------- | ---- | -------- | ------ | ------------ | ------------ | --------- |
| IA-33 | Monitoreo activo y resolucion incidencias             | Monitoreo rendimiento y calidad respuestas; Resolucion incidencias reportadas por usuarios    | 3d   | ~24/04   | ~28/04 | IA-32        | —            | Pendiente |
| IA-34 | Soporte continuo y estabilizacion                     | Continuacion soporte usuarios; Estabilizacion sistema produccion                              | 3d   | ~29/04   | ~01/05 | IA-33        | —            | Pendiente |
| IA-35 | Ajuste fino RAG con feedback usuarios                 | Ajuste fino RAG basado en feedback usuarios reales; Optimizacion parametros produccion         | 2d   | ~02/05   | ~05/05 | IA-34        | —            | Pendiente |
| IA-36 | Informe cierre y metricas finales                     | Informe cierre proyecto; Metricas finales y transferencia conocimiento                        | 2d   | ~06/05   | ~07/05 | IA-35        | —            | Pendiente |


---

## Hitos Principales


| Fecha      | Hito                                            | Coordinacion                 |
| ---------- | ----------------------------------------------- | ---------------------------- |
| 24/02      | Servidores IA instalados y operativos           | —                            |
| ~06/03     | Infraestructura DEV configurada                 | —                            |
| ~13/03     | Interfaz de usuario lista para pruebas internas | —                            |
| ~23/03     | Sistema IA calibrado y funcional                | Entregables #3 y #5          |
| ~26/03     | Validacion con datos reales xECM completada     | Entregable #2                |
| ~31/03     | Transporte a QAS completado                     | —                            |
| ~10/04     | **Fin pruebas QAS**                             | —                            |
| ~17/04     | Seguridad pre-produccion validada               | Entregable #6                |
| ~22/04     | Cutover a produccion completado                 | —                            |
| ~23/04     | UAT y capacitacion completados                  | —                            |
| **~24/04** | **Go-Live**                                     | Aprobacion banco             |
| ~07/05     | Fin soporte post-go-live                        | —                            |


---

## Resumen del Plan


| Concepto                    | Valor         |
| --------------------------- | ------------- |
| Etapas                      | 5             |
| Epics                       | 11            |
| Total tareas                | 36            |
| Duracion estimada           | ~9 semanas    |
| Go-Live estimado            | ~24/04/2026   |
| Fin soporte                 | ~07/05/2026   |
| Coordinaciones externas     | 6 entregables |
