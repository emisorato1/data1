# Roadmap Detallado — Plataforma IA Enterprise

> Ultima actualizacion: 20/02/2026
> Estado general: Sprint 3 en progreso

## Leyenda

- `[x]` Completado
- `[ ]` Pendiente
- Banco — Requiere accion del banco
- xECM — Depende del equipo xECM

## Equipos Involucrados


| Equipo    | Responsabilidad                                                                          |
| --------- | ---------------------------------------------------------------------------------------- |
| **IA**    | Desarrollo, configuracion y puesta en marcha de la plataforma de inteligencia artificial |
| **xECM**  | Instalacion y configuracion de OpenText Content Server                                   |
| **Infra** | Infraestructura cloud (compartido entre IA y xECM)                                       |


---

## Sprint 2 — Semana 6 (09/02 – 13/02) — COMPLETADO

### Aprobacion BBP BC CAT+RRHH

- Aprobacion del Business Blueprint

### Entrega ambientes IA y xECM DEV

- Provision de ambientes cloud para desarrollo
- Configuracion de accesos para equipos IA y xECM
- Validacion de ambientes operativos

### Extractor BC CAT

- Extraccion de catalogo de documentos del banco

**Progreso: 4/4 (100%)**

---

## Sprint 3 — Semanas 7-9 (18/02 – 06/03) — EN PROGRESO

### Semana 7-8: Instalacion Ambientes IA DEV y QAS (18/02 – 27/02)

#### Instalacion Airflow

- Configuracion de infraestructura cloud para Airflow
- Despliegue de Airflow en ambiente DEV
- Verificacion de conectividad y accesos
- Configuracion de pipelines base

#### Instalacion Langfuse

- Configuracion de infraestructura cloud para Langfuse
- Despliegue de Langfuse en ambiente DEV
- Verificacion de metricas y trazabilidad
- Instrumentacion del equipo para monitoreo

#### Conexion interna xECM

- xECM instalado y operativo — *xECM: estimado 20/02 – 24/02*
- Configuracion de conexion entre plataforma IA y xECM
- Prueba de conectividad y acceso a documentos

#### Instalacion VectorDB

- Provision de base de datos vectorial
- Configuracion de indices y esquema base
- Verificacion de rendimiento de busqueda

#### Instalacion Platform DB

- Provision de base de datos de la plataforma
- Esquema de datos disenado y validado
- Aplicacion de esquema completo en ambiente DEV

#### Instalacion IA Platform

- Empaquetado de la aplicacion para despliegue
- Despliegue de la plataforma IA en ambiente DEV
- Verificacion de funcionalidad base (autenticacion, salud del sistema)

**Progreso Sem. 7-8: 6/19 (32%)**

---

### Semana 9: Configuracion IA DEV — Entrenamiento (02/03 – 06/03)

#### Configuracion VectorDB

- Configuracion del modelo de procesamiento de documentos
- Carga inicial de documentos de prueba
- Validacion de busqueda sobre documentos cargados

#### Configuracion Platform DB

- Aplicacion de migraciones finales
- Carga de datos base (roles, usuarios de prueba)

#### Configuracion Pipeline de Documentos

- Configuracion del proceso automatizado de carga de documentos
- Prueba de procesamiento completo de un documento (carga, fragmentacion, almacenamiento)
- Validacion de calidad de fragmentacion y metadatos

#### Configuracion Plataforma IA

- Configuracion del modelo de lenguaje (Gemini)
- Configuracion del sistema de busqueda y generacion de respuestas
- Configuracion de filtros de seguridad (entrada y salida)
- Aplicacion de personalidad y tono del agente — *Banco: reunion 24/02*
- Aplicacion de mensajes de fallback aprobados — *Banco: reunion 24/02*
- Aplicacion de lista de temas prohibidos — *Banco: reunion 24/02*

#### Sincronizacion xECM Roles y Permisos — Metadata

- xECM configurado con categorias, carpetas y roles — *xECM: estimado Sem. 9-10*
- Diseno de tablas de sincronizacion de permisos
- Configuracion de sincronizacion de roles y permisos desde xECM

#### Testing plataform interna IA

- Pruebas de integracion del sistema completo
- Pruebas de autenticacion y autorizacion
- Pruebas de calidad de respuestas con documentos de muestra
- Correccion de errores detectados
- Validacion interna antes de apertura al banco

**Progreso Sem. 9: 0/18 (0%)**

**Progreso Total Sprint 3: 6/37 (16%)**

---

## Fase MVP — Sprint 4 — Semanas 10-12 (09/03 – 27/03) — PENDIENTE

### Semana 10: Disponibilizacion de Pruebas (09/03 – 13/03)

#### Despliegue en ambiente de pruebas

- Migracion de configuracion DEV a ambiente de pruebas
- Configuracion de monitoreo y alertas
- Validacion de accesos para usuarios del banco
- Verificacion de estabilidad del ambiente

**Progreso Sem. 10: 0/4 (0%)**

---

### Semana 11: Refinamiento y Capacitacion (16/03 – 20/03)

#### Creacion de escenarios BOT IA — Base de Conocimiento

- Consultas reales con respuestas esperadas entregadas — *Banco: reunion 26/02*
- Carga del dataset definitivo de documentos del banco
- Configuracion de escenarios de prueba representativos
- Validacion de cobertura de escenarios

#### Refinamiento Respuestas BOT

- Ajuste de parametros de busqueda con documentos reales
- Optimizacion de respuestas segun personalidad definida
- Validacion de calidad de respuestas contra escenarios esperados
- Ajuste de filtros de seguridad con casos reales
- Aplicacion de branding a la interfaz (logo, colores, nombre) — *Banco: reunion 24/02*

#### Capacitacion a Usuarios

- Preparacion de material de capacitacion
- Sesion de capacitacion al equipo del banco (Franco, Branko)
- Entrega de guia de uso

**Progreso Sem. 11: 0/12 (0%)**

---

### Semana 12: Pruebas UATs (23/03 – 27/03)

#### Pruebas UATs

- Ejecucion de pruebas por parte del banco — *Banco*
- Soporte durante las pruebas UAT (equipo IA)
- Recopilacion y priorizacion de observaciones
- Resolucion de observaciones criticas
- Informe de resultados UAT

**Progreso Sem. 12: 0/5 (0%)**

**Progreso Total MVP (Sprint 4): 0/21 (0%)**

---

## Fase Pre-Produccion — Semanas 13-16 (30/03 – 25/04) — PENDIENTE

> Bloques criticos para go-live: Filtros de Seguridad Avanzados (D) y Permisos Documentales (B).
> Estos bloques deben estar listos antes del despliegue a produccion.

### Semana 13: Buffer UAT + Inicio Bloques Criticos (30/03 – 03/04)

#### Resolucion de observaciones UAT

- [ ] Priorizacion de observaciones criticas vs mejoras
- [ ] Correccion de observaciones criticas detectadas en UAT
- [ ] Re-verificacion de correcciones con el banco

#### Inicio Bloque D: Filtros de Seguridad Avanzados

Deteccion automatica de datos sensibles en respuestas, validacion de fidelidad y control tematico reforzado.

- [ ] Deteccion de datos sensibles (DNI, CUIT, CBU, etc.) en las respuestas del asistente
- [ ] Validacion automatica de fidelidad de respuestas contra documentos fuente
- [ ] Control tematico reforzado (solo dominio bancario autorizado)

#### Inicio Bloque B: Permisos y Seguridad Documental

Replicar los permisos de OpenText para que cada usuario solo vea respuestas basadas en documentos a los que tiene acceso.

- [ ] Sincronizacion de permisos desde OpenText — *xECM: requiere roles y permisos configurados*
- [ ] Filtrado de resultados segun permisos del usuario que consulta

**Progreso Sem. 13: 0/8 (0%)**

---

### Semana 14: Desarrollo Bloques B y D (07/04 – 11/04)

#### Bloque B: Permisos y Seguridad Documental (continuacion)

- [ ] Sincronizacion automatica periodica de cambios de permisos
- [ ] Soporte de grupos y herencia de permisos
- [ ] Pruebas de permisos con datos reales de xECM

#### Bloque D: Filtros de Seguridad Avanzados (continuacion)

- [ ] Ajuste de filtros con casos reales del banco
- [ ] Pruebas de deteccion de datos sensibles con documentos reales

**Progreso Sem. 14: 0/5 (0%)**

---

### Semana 15: Testing Integrado — Todo Listo (14/04 – 18/04)

> Objetivo: MVP + Bloques B y D integrados y validados. Todo listo para produccion.

#### Testing pre-produccion

- [ ] Pruebas de integracion completa (MVP + permisos + filtros avanzados)
- [ ] Pruebas de seguridad pre-go-live
- [ ] Validacion de rendimiento del sistema completo
- [ ] Correccion de errores detectados
- [ ] Aprobacion interna para go-live

**Progreso Sem. 15: 0/5 (0%)**

---

### Semana 16: Buffer Final + Preparacion Go-Live (21/04 – 25/04)

#### Preparacion para produccion

- [ ] Despliegue de version final en ambiente productivo
- [ ] Validacion de estabilidad post-despliegue
- [ ] Activacion de monitoreo y alertas en produccion
- [ ] Comunicacion de go-live al banco

**Progreso Sem. 16: 0/4 (0%)**

**Progreso Total Pre-Produccion: 0/22 (0%)**

### **Go-Live a Produccion: 26/04/2026**

---

## Fase Post Go-Live — Semana 17+ (28/04 en adelante) — PENDIENTE

> Mejoras incrementales que no bloquean el go-live.
> Se priorizan segun valor de negocio y feedback de usuarios.

#### Bloque A: Gestion de Documentos desde la Interfaz

Subir, ver estado y eliminar documentos directamente desde la plataforma, sin intervenir manualmente en el proceso de carga.

- [ ] Carga de documentos desde la interfaz web
- [ ] Validacion automatica de archivos (tipo, tamano)
- [ ] Vista de estado de procesamiento de documentos
- [ ] Eliminacion de documentos desde la interfaz
- [ ] Disparo automatico del proceso de indexacion al subir un documento

#### Bloque C: Memoria Avanzada

El asistente recuerda conversaciones previas y usa ese contexto para dar mejores respuestas.

- [ ] Extraccion automatica de contexto relevante de conversaciones anteriores
- [ ] Uso de historial en la busqueda de documentos
- [ ] Proteccion de datos sensibles en el historial almacenado

#### Bloque E: Monitoreo y Evaluacion de Calidad

Metricas automaticas de calidad de respuestas, auditoria de uso y seguimiento de costos.

- [ ] Evaluacion automatica periodica de calidad de respuestas
- [ ] Registro de auditoria detallado de uso del sistema
- [ ] Panel de seguimiento de costos de servicios cloud

#### Bloque F: Interfaz de Administracion

Panel de control para administradores con metricas de uso, gestion de documentos y feedback de usuarios.

- [ ] Panel de metricas de uso del asistente
- [ ] Vista de gestion de documentos para administradores
- [ ] Sistema de feedback por respuesta (util / no util)
- [ ] Modo visual oscuro

#### Bloque G: Automatizacion de Procesos

Re-indexacion programada de documentos, sincronizacion con OpenText y limpieza automatica de datos.

- [ ] Re-indexacion programada de documentos (semanal/diaria)
- [ ] Sincronizacion automatica de documentos desde OpenText
- [ ] Limpieza automatica de datos segun politica de retencion

#### Bloque H: Endurecimiento para Produccion

Pruebas de seguridad, pruebas de carga, despliegue automatizado y gestion multi-ambiente.

- [ ] Pruebas de seguridad (OWASP Top 10 + vulnerabilidades especificas de IA)
- [ ] Pruebas de carga y rendimiento
- [ ] Despliegue automatizado (push a produccion sin intervencion manual)
- [ ] Gestion de configuracion por ambiente (dev, staging, produccion)

**Progreso Total Post Go-Live: 0/22 (0%)**

---

## Dependencias Externas

### Del Banco


| Dependencia                                        | Fecha           | Estado     | Impacta a                                    |
| -------------------------------------------------- | --------------- | ---------- | -------------------------------------------- |
| Personalidad y tono del agente                     | 24/02 (reunion) | Programado | Configuracion Plataforma IA (Sem. 9)         |
| Mensajes de fallback aprobados                     | 24/02 (reunion) | Programado | Configuracion Plataforma IA (Sem. 9)         |
| Branding y assets visuales (logo, colores, nombre) | 24/02 (reunion) | Programado | Interfaz de usuario (Sem. 11)                |
| Lista de temas prohibidos (Compliance)             | 24/02 (reunion) | Programado | Filtros de seguridad (Sem. 9)                |
| Consultas reales con respuestas esperadas          | 26/02 (reunion) | Programado | Escenarios BOT y refinamiento (Sem. 11)      |
| Usuarios piloto para UAT                           | Sem. 10         | Pendiente  | Pruebas UAT (Sem. 12)                        |
| Aprobacion de go-live                              | Sem. 15         | Pendiente  | Go-Live a produccion (26/04)                 |


### Del Equipo xECM


| Dependencia                               | Fecha estimada | Estado      | Impacta a                                           |
| ----------------------------------------- | -------------- | ----------- | --------------------------------------------------- |
| xECM instalado y operativo                | 20/02 – 24/02  | En progreso | Conexion interna xECM (Sem. 7-8)                    |
| Categorias, carpetas y roles configurados | Sem. 9-10      | Pendiente   | Sincronizacion permisos (Sem. 9)                     |
| Esquema de permisos documentado           | Sem. 9         | Pendiente   | Diseno tablas de sincronizacion                       |
| xECM con permisos listos para sincronizar | Sem. 12-13     | Pendiente   | Bloque B — Permisos Documentales (Sem. 13-14)        |


---

## Reuniones Programadas


| Fecha     | Tema                                          | Asistentes        |
| --------- | --------------------------------------------- | ----------------- |
| **24/02** | Personalidad del agente, branding, compliance | ITmind IA + Banco |
| **26/02** | Documentos de prueba y consultas esperadas    | ITmind IA + Banco |


---

## Hitos Clave


| Fecha     | Hito                                                       | Estado      |
| --------- | ---------------------------------------------------------- | ----------- |
| 13/02     | Ambientes DEV entregados                                   | Completado  |
| 27/02     | Instalacion completa de servicios IA en DEV                | En progreso |
| 06/03     | Configuracion y testing interno completado                 | Pendiente   |
| 13/03     | Ambiente de pruebas disponible para el banco               | Pendiente   |
| 20/03     | Capacitacion a usuarios completada                         | Pendiente   |
| 27/03     | **MVP listo — Pruebas UAT finalizadas**                    | Pendiente   |
| 18/04     | **Todo listo para produccion** (MVP + Bloques B y D)       | Pendiente   |
| **26/04** | **Go-Live a Produccion**                                   | Pendiente   |


---

## Resumen de Progreso


| Fase                              | Tareas | Completadas | Progreso |
| --------------------------------- | ------ | ----------- | -------- |
| Sprint 2 (Sem. 6)                 | 4      | 4           | 100%     |
| Sprint 3 (Sem. 7-9)               | 37     | 6           | 16%      |
| Sprint 4 — MVP (Sem. 10-12)       | 21     | 0           | 0%       |
| **Total MVP**                     | **62** | **10**      | **16%**  |
| Pre-Produccion B+D (Sem. 13-16)   | 22     | 0           | 0%       |
| **Total Go-Live**                 | **84** | **10**      | **12%**  |
| Post Go-Live (Sem. 17+)           | 22     | 0           | 0%       |
| **Total Proyecto**                | **106**| **10**      | **9%**   |


