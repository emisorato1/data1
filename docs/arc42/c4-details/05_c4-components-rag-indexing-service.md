# Enterprise AI Platform – RAG Indexing Service

## 1. Visión General

**Diagrama de referencia:** `docs/arc42/diagrams/05-c4-components-rag-indexing-service.drawio.svg`

Este documento describe la arquitectura y el flujo completo del **servicio de RAG Indexing**, integrando:

* El **proceso end-to-end de indexación** desde Content Server (ECM) hasta la base de datos vectorial.
* La **separación en dos pipelines paralelos**: Data y Metadata.
* La **estrategia de chunking** como decisión arquitectónica central de la indexación.

Usamos la arquitectura medallion para transformación de datos. Esta nos permite identificar correctamente las etapas de procesamiento, la cual nos da un mayor control sobre lo que ocurre en cada etapa y permite auditabilidad de los pipelines.

En cada etapa realizamos de manera general lo siguiente:

- La capa **Bronze** almacena los datos en su estado original, sin transformaciones, manteniendo un historial completo y permitiendo la trazabilidad, auditoría y reprocesamiento sin necesidad de volver a extraerlos de la fuente.
- La capa **Silver**, los datos se limpian, validan, estandarizan y enriquecen.
- La capa **Gold** contiene datos altamente estructurados, optimizados para consumo, con agregaciones y desnormalizaciones.

Adaptamos esta perspectiva para el manejo de datos estructurados (metadata) y no estructurados (data).

El objetivo es documentar un pipeline **controlado, reproducible y auditable**, alineado con entornos regulados y de alta criticidad.

---

## 2. Principios y Decisiones de Diseño

El servicio ha sido diseñado considerando los siguientes principios fundamentales:

* **Trazabilidad completa**: Cada documento y transformación es rastreable desde el origen hasta el destino.
* **Reproducibilidad**: El mismo input produce el mismo output en cualquier momento.
* **Segregación de datos**: Los pipelines de metadata y data operan de forma independiente.
* **Control de acceso**: La seguridad se hereda del ECM y se propaga a la base vectorial.
* **Retención y auditoría**: Todos los estados intermedios son persistidos para propósitos de auditoría.

---

## 3. Inicio y Fin del Flujo

* **Inicio**: Content Server (ECM)

  * Tablas y metadatos estructurados SQL.
  * Archivos no estructurados almacenados en EFS (Archive Center).

* **Fin**: Base de Datos Vectorial (PostgreSQL + pgvector)

  * Embeddings indexados.
  * Metadata validada y asociada.

---

## 4. Trazabilidad y Linaje de Datos (Data Lineage)

Cada registro en el sistema mantiene información de linaje que permite rastrear su origen y transformaciones:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| `source_id` | Identificador único del documento en el ECM | `CS-DOC-2024-001234` |
| `source_version` | Versión del documento en el sistema origen | `3.2` |
| `run_id` | Identificador único de ejecución del pipeline | `RUN-20240115-143052-A7B3` |
| `stage` | Capa actual del dato (bronze/silver/gold) | `silver` |
| `stage_timestamp` | Marca temporal de entrada a la capa actual | `2024-01-15T14:32:15.234Z` |
| `previous_stage_id` | Referencia al registro en la capa anterior | `BRZ-2024-001234-v3.2` |
| `transformation_hash` | Hash de la configuración de transformación aplicada | `sha256:a3f2...` |
| `processor_version` | Versión del componente que procesó el registro | `rag-indexer:2.1.4` |

Este modelo de linaje permite:

* Reconstruir el historial completo de cualquier embedding.
* Identificar el impacto de cambios en configuración.
* Auditar transformaciones específicas.
* Reprocesar selectivamente desde cualquier punto.

---

## 5. Metadata Pipeline (Datos Estructurados)

Pipeline encargado del procesamiento de metadata asociada a documentos, seguridad y atributos necesarios para gobernanza y control de acceso.

En esta etapa se consultan directamente las **tablas del ECM (Content Server)** necesarias para la estructura documental, las versiones, la seguridad y la ubicación física de los archivos.

### Metadata Bronze

1. Consulta al ECM para obtener las **tablas crudas necesarias**.
2. Registro de metadata de extracción:
   * Timestamp de consulta.
   * Cantidad de registros extraídos por tabla.
   * Checksum del resultado de cada consulta.
3. Persistencia en un **estado Bronze** sin transformaciones.

#### Tablas consultadas desde Content Server

| Entidad           | Tabla Estándar | Nombre Real (LAB) | Propósito Técnico                                                                   |
| ----------------- | -------------- | ----------------- | ----------------------------------------------------------------------------------- |
| Nodos / Objetos   | DTree          | DTreeCore         | Tabla principal que contiene el árbol de objetos del sistema.                       |
| Versiones         | DVersData      | DVersData         | Detalles técnicos (tamaño, tipo de archivo) de cada versión del documento.          |
| Seguridad (ACL)   | DTreeACL       | DTreeACL          | Matriz de control de acceso (quién tiene qué permiso).                              |
| Usuarios / Grupos | KUAF           | KUAF              | Directorio de usuarios y grupos.                                                    |
| Membresías        | KUAFCHILDREN   | KUAFChildren      | Tabla de relación que indica a qué grupos pertenece cada usuario.                   |
| Almacenamiento    | ProviderData   | ProviderData      | Información sobre la ubicación física del archivo en el servidor de archivos (EFS). |

Estas tablas constituyen la **fuente primaria de metadata estructurada**, y su contenido es estandarizado y almacenado como *staged SQL rows* para su posterior procesamiento en las etapas Silver y Gold.

> Nota: La cantidad de tablas puede aumentar luego de los relevamientos. 

**Estado resultante**:

* Staged SQL Rows con metadata cruda.
* Registro de extracción con checksums para verificación.

### Metadata Silver

1. Estandarización de esquemas y formatos.
2. Normalización de valores (fechas ISO 8601, identificadores, nombres).
3. Limpieza de inconsistencias.
4. Preparación de datos para procesamiento posterior.
5. **Validaciones de integridad**:
   * Verificación de referencias cruzadas entre tablas.
   * Validación de integridad referencial (documentos huérfanos).
   * Detección de ACLs inconsistentes o incompletas.
6. Procesamiento de seguridad:
   * Resolución de roles efectivos por usuario.
   * Cálculo de niveles de acceso por documento.
   * Expansión de membresías de grupos.
7. Unión y consolidación de tablas de metadata.
8. Filtrado de tipos de archivos soportados.
9. **Registro de métricas de calidad**:
   * Registros procesados vs descartados (si es que aplican).
   * Errores de validación por tipo.
   * Cobertura de campos obligatorios.

**Estado resultante**:

* Metadata limpia, coherente y alineada con políticas de acceso.
* Log de validaciones ejecutadas con resultados.

### Metadata Gold

1. Adaptación de la metadata al **esquema esperado por la base vectorial**.
2. Validación de campos obligatorios según contrato de datos.
3. Generación del objeto final de metadata.
4. Cálculo de hash de integridad del registro final.

**Estado resultante**:

* Metadata validada, versionada y lista para ensamblado.
* Hash de integridad para verificación posterior.

---

## 6. Data Pipeline (Datos No Estructurados)

Pipeline responsable del procesamiento de documentos como **PDF, Word, Excel y formatos equivalentes**, hasta la generación de embeddings.

Utilizamos la API de Archive Center para consultar los documentos necesarios para vectorizar.

### Data Bronze

1. Extracción del archivo crudo desde Archive Center.
2. Generación de checksum (SHA-256) del archivo original.
3. Registro de metadata de ingesta:
   * Timestamp de extracción (ISO 8601).
   * Tamaño del archivo en bytes.
   * Formato MIME detectado.
   * Estado de extracción (success/failure).
   * Identificador de correlación con metadata pipeline.
4. Persistencia del archivo en estado Bronze con identificador único.

**Estado resultante**:

* Archivo crudo almacenado con checksum verificable.
* Registro de ingesta para auditoría.

---

### Data Silver

#### Limpieza y conversiones

1. Conversión del archivo a **texto plano**.
2. Registro de metadata de conversión:
   * Herramienta/librería utilizada y versión.
   * Páginas/hojas procesadas.
   * Caracteres extraídos.
3. Procesamiento de limpieza:
   * Eliminación de stopwords.
   * Normalización de caracteres y codificación (UTF-8).
   * Remoción de ruido no semántico.
4. Validación de contenido extraído:
   * Verificación de texto no vacío.
   * Detección de documentos corruptos o ilegibles.
5. Persistencia del texto procesado.

**Estado resultante**:

* Texto limpio y normalizado, listo para segmentación.
* Registro de conversión con métricas.

---

#### Chunking

La segmentación de documentos es una **decisión estructural del servicio**, no un detalle de implementación.

La estrategia de chunking se basa en los siguientes principios:

* Fragmentación respetando la **estructura lógica original** del documento.
* Uso de capítulos, secciones, artículos, incisos y encabezados como unidades naturales.
* Cada chunk representa una unidad semántica coherente y autosuficiente.
* No se cruzan límites conceptuales definidos por el documento.

Cuando una sección supera el tamaño máximo permitido para embeddings:

* Se divide de forma **determinística y reproducible**.
* Se preserva el orden interno y la jerarquía documental.

El mismo documento procesado múltiples veces genera **exactamente los mismos fragmentos**.

Cada chunk incluye metadata explícita:

* Documento y versión.
* Estructura jerárquica (capítulo, sección, subsección).
* Posición relativa (índice del chunk dentro del documento).
* Sistema de origen y clasificación.
* Hash del contenido del chunk.

**Métricas de chunking registradas**:

| Métrica | Descripción |
|---------|-------------|
| `total_chunks` | Número total de chunks generados |
| `avg_chunk_size` | Tamaño promedio en tokens |
| `max_chunk_size` | Tamaño máximo en tokens |
| `min_chunk_size` | Tamaño mínimo en tokens |
| `hierarchy_depth` | Profundidad máxima de jerarquía detectada |

> Nota: El embedding sin contexto no tiene valor operativo en entornos regulados.

---

### Data Gold

1. Generación de embeddings utilizando **Vertex AI**.
2. Registro de metadata de vectorización:
   * Modelo utilizado y versión.
   * Dimensionalidad del vector.
   * Timestamp de generación.
3. Asociación de cada embedding con su chunk y metadata contextual.
4. Validación de embeddings generados:
   * Verificación de dimensionalidad correcta.
   * Detección de vectores nulos o anómalos.
5. Persistencia en un **estado Gold**.

**Estado resultante**:

* Vectores listos para indexación, trazables y versionados.
* Registro completo de generación para auditoría.

---

## 7. Contratos de Datos (Data Contracts)

Los contratos de datos definen las expectativas de schema y calidad entre capas, permitiendo validación automática y detección temprana de anomalías.

### Contrato: Metadata Bronze → Silver

| Campo | Tipo | Obligatorio | Validación |
|-------|------|-------------|------------|
| `node_id` | integer | Sí | > 0 |
| `parent_id` | integer | No | >= 0 o null |
| `name` | string | Sí | No vacío, max 255 chars |
| `create_date` | datetime | Sí | Fecha válida |
| `modify_date` | datetime | Sí | >= create_date |
| `owner_id` | integer | Sí | Referencia válida en KUAF |

### Contrato: Metadata Silver → Gold

| Campo | Tipo | Obligatorio | Validación |
|-------|------|-------------|------------|
| `document_id` | string | Sí | Formato: `DOC-{system}-{id}-v{version}` |
| `title` | string | Sí | No vacío |
| `classification` | string | Sí | Valor de catálogo válido |
| `access_groups` | array[string] | Sí | Al menos un grupo |
| `version` | string | Sí | Formato semántico |
| `effective_date` | datetime | Sí | ISO 8601 |

### Contrato: Data Bronze → Silver

| Campo | Tipo | Obligatorio | Validación |
|-------|------|-------------|------------|
| `file_id` | string | Sí | UUID v4 |
| `raw_content` | binary | Sí | No vacío |
| `checksum` | string | Sí | SHA-256 válido (64 chars hex) |
| `mime_type` | string | Sí | MIME type válido |
| `size_bytes` | integer | Sí | > 0 |
| `ingestion_timestamp` | datetime | Sí | ISO 8601 |

### Contrato: Data Silver → Gold

| Campo | Tipo | Obligatorio | Validación |
|-------|------|-------------|------------|
| `chunk_id` | string | Sí | Formato: `CHK-{doc_id}-{index}` |
| `chunk_content` | string | Sí | No vacío, <= max_tokens |
| `chunk_index` | integer | Sí | >= 0 |
| `parent_document_id` | string | Sí | Referencia válida |
| `hierarchy_path` | string | No | Formato: `cap1/sec2/sub3` |
| `content_hash` | string | Sí | SHA-256 del contenido |

---

## 8. Ensamble + Base de Datos Vectorial

### Ensamblado de pipelines (Merge)

1. Sincronización de estados:
   * Verificación de que ambos pipelines completaron para el documento.
   * Validación de consistencia de versiones.
2. Asociación de:
   * Chunks y embeddings (Data Pipeline).
   * Metadata final validada (Metadata Pipeline).
3. Construcción del **payload completo** por fragmento documental.
4. Validación de integridad del payload ensamblado.

#### Manejo de inconsistencias en el Merge

| Escenario | Comportamiento | Acción |
|-----------|---------------|--------|
| Embeddings sin metadata | Bloqueo | Enviar a DLQ, alertar |
| Metadata sin embeddings | Espera | Reintentar hasta timeout |
| Versiones inconsistentes | Bloqueo | Enviar a DLQ, alertar |
| Timeout de sincronización | Fallo | Enviar a DLQ, notificar |

---

### Estrategia de almacenamiento en la base vectorial

* Separación lógica entre:
  * Datos vectoriales (embeddings).
  * Metadata estructurada.
* Uso de PostgreSQL con **pgvector**.
* Indexación controlada y reproducible.

#### Estrategia de creación de tablas (conceptual)

* Tabla de documentos y versiones.
* Tabla de chunks con referencias a documentos.
* Tabla de embeddings con referencias a chunks.
* Tabla de auditoría de operaciones.
* Relaciones explícitas para trazabilidad y auditoría.

---

## 9. Observabilidad y Métricas de Integridad

### Métricas por capa

| Capa | Métrica | Descripción | Umbral de alerta |
|------|---------|-------------|------------------|
| Bronze | `ingestion_count` | Documentos/registros ingestados | - |
| Bronze | `ingestion_error_rate` | % de fallos de extracción | > 5% |
| Bronze | `checksum_validation_failures` | Fallos de verificación de checksum | > 0 |
| Silver | `validation_pass_rate` | % de registros que pasan validación | < 95% |
| Silver | `transformation_error_rate` | % de errores de transformación | > 2% |
| Silver | `chunk_count` | Número de chunks generados | - |
| Silver | `avg_chunks_per_document` | Promedio de chunks por documento | - |
| Gold | `embedding_success_rate` | % de chunks vectorizados exitosamente | < 99% |
| Gold | `embedding_latency_p95` | Latencia P95 de generación | > 5s |
| Merge | `merge_completeness` | % de chunks con metadata asociada | < 100% |
| Merge | `orphan_embeddings` | Embeddings sin metadata | > 0 |

### Métricas de calidad de datos

| Dimensión | Métrica | Cálculo |
|-----------|---------|---------|
| **Completitud** | `field_completeness` | % de campos no nulos vs esperados |
| **Consistencia** | `referential_integrity` | % de referencias válidas |
| **Exactitud** | `format_compliance` | % de valores en formato correcto |
| **Unicidad** | `duplicate_rate` | % de registros duplicados |
| **Frescura** | `data_age` | Tiempo desde última actualización |

### Dashboards

1. **Pipeline Health**: Estado general de cada pipeline y capa.
2. **Data Quality**: Métricas de calidad por dimensión.
3. **Processing Latency**: Tiempos de procesamiento por etapa.
4. **Error Analysis**: Desglose de errores por tipo y causa.

> Nota: Estos dashboards son internos para tener un control de los procesos.
---

## 10. Manejo de Errores y Recuperación

### Estrategia de Dead Letter Queue (DLQ)

Los registros que fallan validación o procesamiento se envían a una cola de errores para:

* Análisis posterior por el equipo de operaciones.
* Reprocesamiento manual después de corrección.
* Generación de alertas según severidad.
* Preservación de evidencia para auditoría.

#### Clasificación de errores

| Severidad | Tipo | Ejemplo | Acción |
|-----------|------|---------|--------|
| **Crítico** | Integridad | Checksum inválido | Alerta inmediata, bloqueo |
| **Alto** | Seguridad | ACL no resuelto | Alerta, envío a DLQ |
| **Medio** | Calidad | Campo opcional vacío | Log, continuar |
| **Bajo** | Formato | Encoding no estándar | Log, normalizar |

### Idempotencia

Todos los pipelines son idempotentes:

* El reprocesamiento de un documento genera los mismos resultados.
* Los identificadores son determinísticos basados en contenido y versión.
* Las operaciones de escritura utilizan upsert con verificación de versión.

### Política de reintentos

| Tipo de error | Reintentos | Backoff | Timeout |
|---------------|------------|---------|---------|
| Transitorio (red, timeout) | 3 | Exponencial (1s, 2s, 4s) | 30s |
| Recurso no disponible | 5 | Lineal (5s) | 60s |
| Error de validación | 0 | - | - |
| Error de integridad | 0 | - | - |

---

## 11. Principios Arquitectónicos

* **Chunking determinístico y gobernado**: La segmentación es predecible y auditable.
* **Versionado como concepto de primer nivel**: Cada cambio genera una nueva versión rastreable.
* **Independencia del modelo de lenguaje**: El pipeline no depende de un modelo específico de embeddings.
* **Retrieval completamente controlado por el sistema**: No hay componentes de caja negra.
* **Auditabilidad y reproducibilidad completas**: Cualquier estado puede ser reconstruido.
* **Segregación de responsabilidades**: Metadata y Data se procesan independientemente.
* **Fail-safe por diseño**: Los errores no propagan datos inconsistentes.

> Se descartan enfoques de chunking semántico automático basados en embeddings o LLMs para producción. Aunque pueden resultar atractivos en prototipos, introducen variabilidad, dificultan la explicación del proceso y rompen la reproducibilidad. En un contexto auditado, no es aceptable que la segmentación dependa de heurísticas opacas o cambios en el comportamiento del modelo.

---

## 12. Referencias

- Para definiciones de términos técnicos, consultar el glosario en `docs/arc42/12_glossary.md`.
