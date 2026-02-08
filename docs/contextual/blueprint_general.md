<div align="center">

# 🏢 ARQUITECTURA DE BASE DE DATOS VECTORIAL PARA SISTEMA RAG EMPRESARIAL

## Guía de Dimensionamiento, Optimización y Operación

---

**Proyecto:** Enterprise AI Platform  
**Versión:** 3.0 | **Fecha:** Enero 2026

---

| Metadato | Valor |
|:---------|:------|
| **Autor** | Equipo de Arquitectura |
| **Clasificación** | Documento Técnico de Referencia |
| **Audiencia Primaria** | Arquitectos de Soluciones, Ingenieros ML/AI, DevOps/SRE |
| **Audiencia Secundaria** | Stakeholders Ejecutivos, Equipo de Finanzas |
| **Estado** | Versión Final |
| **Próxima Revisión** | Abril 2026 (3 meses) |

</div>

---

# 📋 ÍNDICE

## RESUMEN EJECUTIVO
- [Contexto del Proyecto](#contexto-del-proyecto)
- [Decisión Tecnológica Principal](#decisión-tecnológica-principal)
- [Métricas Clave de Dimensionamiento](#métricas-clave-de-dimensionamiento)
- [TCO Resumido (3 Escenarios)](#tco-resumido-3-escenarios)
- [Recomendación y Próximos Pasos](#recomendación-y-próximos-pasos)

---

## SECCIÓN I: FUNDAMENTOS Y DIMENSIONAMIENTO

- **Capítulo 1:** [Contexto y Requerimientos](#capítulo-1-contexto-y-requerimientos)
  - 1.1 Descripción del Proyecto
  - 1.2 Fuentes de Datos
  - 1.3 Requerimientos Funcionales
  - 1.4 Requerimientos No Funcionales
  - 1.5 Audiencia del Documento

- **Capítulo 2:** [Dimensionamiento BASE (Sin Optimizar)](#capítulo-2-dimensionamiento-base-sin-optimizar)
  - 2.1 Metodología de Cálculo
  - 2.2 Tabla A: Volumen de Datos (Pasos 1-18)
  - 2.3 Tabla B: Memoria y Cómputo (Pasos 19-26)
  - 2.4 Resumen del Escenario Base

- **Capítulo 3:** [Glosario de Variables](#capítulo-3-glosario-de-variables)
  - 3.1 Variables de Entrada
  - 3.2 Variables Derivadas
  - 3.3 Tabla de Impacto de Variaciones

---

## SECCIÓN II: SELECCIÓN DE TECNOLOGÍA

- **Capítulo 4:** Evaluación de Bases de Datos Vectoriales
  - 4.1 Candidatos Evaluados
  - 4.2 Criterios de Evaluación y Pesos
  - 4.3 Matriz Comparativa
  - 4.4 Score Ponderado Final
  - 4.5 Decisión y Justificación

- **Capítulo 5:** Arquitectura de Referencia
  - 5.1 Diagrama de Arquitectura General
  - 5.2 Componentes del Sistema
  - 5.3 Flujo de Datos

---

## SECCIÓN III: TÉCNICAS DE OPTIMIZACIÓN

- **Capítulo 6:** Compresión de Embeddings (Matryoshka, halfvec)
  - 6.1 Matryoshka Representation Learning
  - 6.2 halfvec (Float16) en pgvector
  - 6.3 Combinación Óptima
  - 6.4 Impacto en Costos y Calidad

- **Capítulo 7:** Particionamiento de Datos
  - 7.1 Estrategia por Área/Dominio
  - 7.2 Implementación SQL
  - 7.3 Beneficios de Performance

- **Capítulo 8:** Cacheo Semántico
  - 8.1 Arquitectura Multi-Nivel
  - 8.2 Implementación con Redis
  - 8.3 Políticas de Eviction

---

## SECCIÓN IV: TÉCNICAS AVANZADAS DE RAG

- **Capítulo 9:** Estrategias de Chunking
  - 9.1 Técnicas Básicas y Avanzadas
  - 9.2 Matriz de Decisión por Tipo de Documento
  - 9.3 Impacto del Overlap en Costos

- **Capítulo 10:** Modelos de Embedding
  - 10.1 Comparativa de Modelos 2024-2025
  - 10.2 Bi-Encoder vs Cross-Encoder vs Late Interaction
  - 10.3 Recomendación para el Proyecto

- **Capítulo 11:** Técnicas de Búsqueda
  - 11.1 Búsqueda Híbrida (Vector + BM25)
  - 11.2 Reranking con Cross-Encoder
  - 11.3 HyDE y Multi-Query
  - 11.4 Pipeline Recomendado

---

## SECCIÓN V: ANÁLISIS DE ESCENARIOS Y COSTOS

- **Capítulo 12:** Escenario Baseline (Sin Optimizar)
  - 12.1 Configuración
  - 12.2 Costos Mensuales y Anuales
  - 12.3 Limitaciones

- **Capítulo 13:** Escenario Optimizado (RECOMENDADO)
  - 13.1 Optimizaciones Aplicadas
  - 13.2 Costos Mensuales y Anuales
  - 13.3 ROI de Optimizaciones

- **Capítulo 14:** Escenario Ultra-Optimizado (Open Source)
  - 14.1 Stack Open Source
  - 14.2 Costos y Trade-offs

- **Capítulo 15:** Comparativa y Decisión Final
  - 15.1 Tabla Comparativa de TCO a 3 Años
  - 15.2 Punto de Inflexión para Migración
  - 15.3 Cronograma de Implementación

---

## SECCIÓN VI: OPERACIONES Y PRODUCCIÓN

- **Capítulo 16:** Framework de Evaluación de Calidad
  - 16.1 Métricas de Retrieval
  - 16.2 Métricas de Generación
  - 16.3 Implementación con RAGAS
  - 16.4 Dashboard de Métricas

- **Capítulo 17:** Estrategia de Actualización de Datos
  - 17.1 Pipeline de Actualización (CDC)
  - 17.2 SLAs de Freshness por Área
  - 17.3 Costos de Re-indexación

- **Capítulo 18:** Alta Disponibilidad y Disaster Recovery
  - 18.1 Arquitectura de HA
  - 18.2 RTO/RPO
  - 18.3 Procedimiento de Failover

- **Capítulo 19:** Observabilidad y Monitoreo
  - 19.1 Stack de Observabilidad
  - 19.2 Métricas Críticas y Alertas
  - 19.3 Dashboards Recomendados

- **Capítulo 20:** Degradación Graceful
  - 20.1 Fallback por Componente
  - 20.2 Circuit Breaker Pattern
  - 20.3 Mensajes de Usuario

---

## ANEXOS

- **Anexo A:** [Checklist Pre-Producción](#anexo-a-checklist-pre-producción)
- **Anexo B:** [Configuraciones SQL](#anexo-b-configuraciones-sql)
- **Anexo C:** [Código de Referencia](#anexo-c-código-de-referencia)
- **Anexo D:** [Referencias y Fuentes](#anexo-d-referencias-y-fuentes)
- **Anexo E:** [Glosario de Términos](#anexo-e-glosario-de-términos)

---
---

# RESUMEN EJECUTIVO

## Contexto del Proyecto

El proyecto **Enterprise AI Platform** requiere implementar un sistema RAG (Retrieval-Augmented Generation) empresarial capaz de responder consultas sobre un corpus documental de **17 TB** almacenado actualmente en OpenText.

### La Pregunta Central

> **"Tenemos 17 TB de documentos. ¿Cuánta infraestructura necesitamos para que el sistema de IA pueda buscar respuestas en todos ellos de manera instantánea?"**

### Analogía para Stakeholders No Técnicos

> 🍊 **La Analogía de la Biblioteca**
> 
> Imagina que tienes una biblioteca de 17 millones de libros (17 TB). Para que alguien encuentre una respuesta en segundos, no puedes simplemente guardar los libros en estantes. Necesitas:
> 
> 1. **Un catálogo inteligente** (los "vectores" o embeddings)
> 2. **Un sistema de búsqueda rápida** (el índice HNSW)
> 3. **Espacio en memoria** para tener el catálogo "a mano" (RAM)
> 
> Este documento calcula exactamente cuánto de cada cosa necesitamos.

---

## Decisión Tecnológica Principal

<div align="center">

| Decisión | Elección | Justificación |
|:---------|:---------|:--------------|
| **Motor Año 1-2** | PostgreSQL + pgvector | Simplicidad, costo, expertise existente |
| **Hosting** | Cloud SQL Enterprise (GCP) | HA nativo, backups automáticos, escalabilidad |
| **Cuantización** | halfvec (float16) | 50% ahorro RAM, pérdida <0.1% recall |
| **Target Año 2+** | Vertex AI Vector Search | Escalabilidad ilimitada (si se supera 400M vectores) |

</div>

### Razones de la Elección de pgvector

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DECISIÓN: PostgreSQL + pgvector                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ✅ RAZONES PRINCIPALES:                                                     │
│                                                                              │
│  1. COSTO: 60-70% más barato que alternativas managed                       │
│     • $1,500/mes vs. $4,000/mes (Pinecone)                                  │
│                                                                              │
│  2. EXPERTISE: El equipo ya conoce PostgreSQL                               │
│     • Menor curva de aprendizaje                                            │
│     • Debugging familiar                                                     │
│                                                                              │
│  3. FLEXIBILIDAD: Sin vendor lock-in                                        │
│     • Migración a otra infra es posible                                     │
│     • Open source, comunidad activa                                         │
│                                                                              │
│  4. FEATURES: Hybrid search nativo                                          │
│     • Vector + BM25 en una sola query                                       │
│     • No requiere servicios adicionales                                     │
│                                                                              │
│  5. ESCALA: Suficiente para 244M-500M vectores                              │
│     • Con optimizaciones cubre el roadmap de 3 años                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Métricas Clave de Dimensionamiento

### Resumen de Recursos Calculados

| Lo que Tenemos | Lo que Necesitamos (Baseline) | Lo que Necesitamos (Optimizado) |
|:---------------|:------------------------------|:--------------------------------|
| 17 TB de documentos en OpenText | **~3.0-5.0 TB** de disco SSD | **~1.0 TB** de disco SSD |
| — | **~240-300 GB** de RAM | **~90 GB** de RAM |
| — | **~244 M vectores** | **~244 M vectores** |
| — | ~$3,200/mes | **~$1,500/mes** |

### Proceso de Transformación

```
📁 17 TB de archivos en OpenText
     ↓ (extracción: 10% es texto)
📝 1.7 TB de texto bruto
     ↓ (limpieza: 30% es redundante)
📄 1.19 TB de texto útil
     ↓ (fragmentación en chunks de 4KB + 15% overlap)
🔢 244 millones de vectores
     ↓ (almacenamiento + índice HNSW + overhead 30%)
💾 ~3-5 TB de disco SSD + ~240-300 GB RAM (sin optimizar)
     ↓ (con Matryoshka 768d + halfvec)
💾 ~1.0 TB de disco SSD + ~90 GB RAM (optimizado)
     ↓ (traducido a Cloud SQL Enterprise)
💰 ~$1,500 - $3,200 / mes (según nivel de optimización)
```

---


## TCO Resumido (3 Escenarios)

> 💡 **¿Qué es TCO?**
> 
> **TCO (Total Cost of Ownership)** o "Costo Total de Propiedad" es la suma de **todos los costos de infraestructura** asociados a un sistema durante su vida útil. Incluye implementación inicial, operación mensual y actualizaciones.

### Componentes del Costo

Para entender la tabla, es importante conocer qué incluye cada columna:

| Componente | Qué Incluye | Cuándo se Paga |
|:-----------|:------------|:---------------|
| **Ingestión (Año 0)** | Generar embeddings de los 244M chunks, procesamiento OCR/parsing, carga inicial a Cloud SQL | Una sola vez al inicio |
| **Operación Mensual** | Cloud SQL, APIs de IA (embeddings, LLM), Redis cache, Cloud Run, networking, monitoreo | Cada mes mientras el sistema esté activo |
| **TCO 3 Años** | Ingestión + (Operación Mensual × 36 meses) | Acumulado en 3 años |

> ⚠️ **Nota:** Estos costos son **solo infraestructura**. No incluyen horas de desarrollo del equipo interno.

### Tabla Comparativa de Costos

| Escenario | Ingestión (Año 0) | Operación Mensual | TCO 3 Años | Viabilidad |
|:----------|:-----------------:|:-----------------:|:----------:|:----------:|
| **A: Baseline (Sin Optimizar)** | ~$5,500 | ~$8,050 | **~$295,300** | ⚠️ Costoso |
| **B: Optimizado (RECOMENDADO)** | ~$5,500 | ~$3,600 | **~$135,100** | ✅ Viable |
| **C: Ultra-Optimizado (OSS)** | ~$1,000 | ~$2,850 | **~$103,600** | ✅ Viable (requiere expertise GPU) |

> 📊 **Interpretación rápida:**
> - El **Escenario A** tiene el mismo costo de ingestión pero paga ~$8K/mes por infraestructura sobredimensionada.
> - El **Escenario B** optimiza la infraestructura con halfvec y cache, reduciendo 55% el costo mensual.
> - El **Escenario C** usa embeddings open source (BGE-M3), eliminando el costo de APIs de embedding.

### Desglose del Costo de Ingestión

| Componente | Escenarios A/B | Escenario C |
|:-----------|:--------------:|:-----------:|
| Embeddings (244M chunks) | ~$4,900 (Gemini API) | ~$350 (BGE-M3 en GPU spot) |
| Procesamiento OCR/Parsing | ~$300 | ~$300 |
| Carga inicial Cloud SQL | ~$200 | ~$200 |
| Construcción índices HNSW | ~$100 | ~$100 |
| **TOTAL** | **~$5,500** | **~$950** |

### Visualización de TCO Acumulado

```
Costo Acumulado (miles USD)
     │
300k ┤                                          ╱─── Escenario A ($295k) 
     │                                        ╱
250k ┤                                      ╱
     │                                    ╱
200k ┤                                  ╱
     │                                ╱
150k ┤                              ╱
     │                            ╱───────────────── Escenario B ($135k) ⭐ RECOMENDADO
100k ┤                          ╱
     │                        ╱───────────────────── Escenario C ($104k)
 50k ┤                      ╱
     │                    ╱
   0 ┼──────────────────────────────────────────────────────────────────► Tiempo
        Año 0          Año 1          Año 2          Año 3
```


---

## Recomendación y Próximos Pasos

### Estrategia Recomendada: Escenario B (Optimizado)

| Ventaja | Explicación |
|:--------|:------------|
| **Menor riesgo MVP** | Usamos tecnología conocida (PostgreSQL) para validar el producto |
| **Menor costo inicial** | Ahorramos ~$90,000 vs. Baseline en el primer año |
| **Migración planificada** | Tenemos tiempo de preparar el equipo y procesos |
| **Ahorro total 3 años** | ~$250,000 menos que el escenario Baseline |

### Cronograma de Alto Nivel

```
2026
────────────────────────────────────────────────────────────────────────
ENE  FEB  MAR  ABR  MAY  JUN  JUL  AGO  SEP  OCT  NOV  DIC
 │    │    │    │    │    │    │    │    │    │    │    │
 └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
 │─ Sem 1-4: Ingestión Inicial ───│
                                   │─── Sem 5-8: Optimizaciones ───│
                                                              │── PoC Vertex AI ──►

2027
────────────────────────────────────────────────────────────────────────
ENE  FEB  MAR  ABR  MAY  JUN
 │    │    │    │    │    │
 └────┴────┴────┴────┴────┘
 │── Evaluación (si >300M vectores) ──│
                                       │── Migración Gradual (si aplica) ──►
```

### Próximos Pasos Inmediatos

1. **Semana 1-2:** Validar $f_{text}$ y $r_{clean}$ con muestra de 500 documentos
   - *Procesar una muestra representativa para confirmar que el 10% de los archivos es texto extraíble y el 30% son duplicados. Ajustar las variables si los valores reales difieren.*

2. **Semana 3-4:** Provisionar Cloud SQL Enterprise y configurar networking
   - *Crear la instancia de base de datos con pgvector, configurar VPC, Private IP, y probar conectividad desde los servicios de aplicación.*

3. **Semana 5-8:** Implementar pipeline de ingestión con Matryoshka + halfvec
   - *Desarrollar el flujo completo: extracción de texto → chunking → generación de embeddings (768d truncados) → carga en Cloud SQL con tipo halfvec.*

4. **Semana 9-10:** Configurar monitoreo y alertas
   - *Implementar dashboards en Cloud Monitoring, configurar alertas para métricas críticas (latencia, errores, uso de recursos) y conectar con PagerDuty/Slack.*

5. **Semana 11-12:** Testing de calidad con golden set y ajustes
   - *Evaluar el sistema con un conjunto de ~100 queries anotadas por expertos, medir Recall@10 y Faithfulness, y ajustar parámetros (ef_search, weights de RRF) según resultados.*

---
---

# SECCIÓN I: FUNDAMENTOS Y DIMENSIONAMIENTO

---

## Capítulo 1: Contexto y Requerimientos

### 1.1 Descripción del Proyecto

**Enterprise AI Platform** es una plataforma de inteligencia artificial empresarial diseñada para permitir a los usuarios internos de la organización realizar consultas en lenguaje natural sobre el corpus documental corporativo completo.

El sistema implementa una arquitectura **RAG (Retrieval-Augmented Generation)** que:
1. Recibe una pregunta del usuario en lenguaje natural
2. Busca los fragmentos de documentos más relevantes (retrieval)
3. Genera una respuesta utilizando un LLM con el contexto recuperado (generation)
4. Cita las fuentes utilizadas para la respuesta

### 1.2 Fuentes de Datos

| Fuente | Volumen | Tipo de Contenido | Frecuencia de Actualización |
|:-------|:-------:|:------------------|:----------------------------|
| **OpenText** | ~17 TB | Documentos corporativos mixtos | Diaria |
| **SharePoint** | ~500 GB | Presentaciones, manuales | Semanal |
| **Confluence** | ~200 GB | KB técnica | Diaria |
| **Email Archives** | ~2 TB | Correspondencia histórica | Batch mensual |

**Características del Corpus:**
- **Idiomas:** Español (90%), Inglés (10%)
- **Formatos:** PDF (60%), Office (30%), Texto plano (10%)
- **Antigüedad:** 1-15 años
- **Tenants:** Multi-tenant con aislamiento por área funcional

### 1.3 Requerimientos Funcionales

| ID | Requerimiento | Prioridad |
|:---|:--------------|:---------:|
| RF-01 | Búsqueda semántica en todo el corpus | Alta |
| RF-02 | Filtrado por área funcional (RRHH, Legal, etc.) | Alta |
| RF-03 | Control de acceso basado en permisos | Alta |
| RF-04 | Citación de fuentes en respuestas | Media |
| RF-05 | Búsqueda híbrida (semántica + keywords) | Media |
| RF-06 | Soporte multilingüe (español/inglés) | Media |

### 1.4 Requerimientos No Funcionales

| Métrica | Target | Justificación |
|:--------|:------:|:--------------|
| **Latencia búsqueda P95** | < 50 ms | Para mantener latencia total E2E < 3 seg |
| **Latencia E2E P95** | < 3 seg | Experiencia de usuario aceptable |
| **QPS** | 30 queries/seg | Pico estimado de uso concurrente |
| **Disponibilidad** | 99.9% | SLA empresarial estándar |
| **Downtime anual máximo** | < 8.76 horas | Derivado del 99.9% |
| **Recall@10** | > 90% | Calidad mínima de retrieval |
| **RPO** | < 5 min | Máxima pérdida de datos aceptable |
| **RTO** | < 60 seg | Tiempo máximo de recuperación |

### 1.5 Audiencia del Documento

| Audiencia | Secciones Relevantes | Nivel de Detalle |
|:----------|:--------------------|:-----------------|
| **Arquitectos de Soluciones** | Todas | Completo |
| **Ingenieros ML/AI** | I, III, IV | Técnico profundo |
| **DevOps/SRE** | I, II, VI | Operativo |
| **Stakeholders Ejecutivos** | Resumen Ejecutivo, V | Alto nivel |
| **Equipo de Finanzas** | Resumen Ejecutivo, V | Costos y TCO |

---

## Capítulo 2: Dimensionamiento BASE (Sin Optimizar)

Este capítulo presenta el dimensionamiento **baseline** asumiendo que no se aplican optimizaciones (ni Matryoshka, ni halfvec, ni compresión). Representa el **escenario conservador** y el punto de partida para medir el impacto de las optimizaciones.

### 2.1 Metodología de Cálculo

El dimensionamiento sigue una metodología de **26 pasos** organizados en dos tablas:

- **Tabla A (Pasos 1-18):** Transformación de documentos brutos a requerimientos de almacenamiento
- **Tabla B (Pasos 19-26):** Cálculo de memoria RAM y cómputo necesarios

Cada paso incluye:
- ✅ **Valor calculado** en unidades amigables
- 📊 **Rango típico** de la industria con fuentes
- 📍 **Origen** de cada valor (input, fórmula, constante)
- 🔗 **Dependencias** entre pasos

### 2.2 Tabla A: Volumen de Datos (Pasos 1-18)

> 💡 **Para no técnicos:** Esta tabla muestra cómo 17 TB de documentos se transforman en ~3.0 TB de base de datos.

#### Fase 1: Extracción de Texto (Pasos 1-5)

| # | Variable | Fórmula | Valor | Descripción |
|:-:|:---------|:--------|:-----:|:------------|
| 1 | $S_{raw}$ | *input* | **17 TB** | Documentos brutos en OpenText |
| 2 | $f_{text}$ | *input* | 0.10 | Proporción de texto extraíble. **Rango: 5-20%** |
| 3 | $S_{text}$ | $S_{raw} \times f_{text}$ | 1.7 TB | Texto crudo extraído |
| 4 | $r_{clean}$ | *input* | 0.30 | Texto descartado por duplicados. **Rango: 20-50%** |
| 5 | $S_{clean}$ | $S_{text} \times (1 - r_{clean})$ | **1.19 TB** | ⭐ Texto limpio para vectorizar |

> 📊 **Resumen Fase 1:** De 17 TB de archivos, solo **1.19 TB es texto útil**. El resto son imágenes, formatos y duplicados.

#### Fase 2: Chunking y Embeddings (Pasos 6-9)

| # | Variable | Fórmula | Valor | Descripción |
|:-:|:---------|:--------|:-----:|:------------|
| 6 | $C_{chunk}$ | *input* | **4 KB** | Tamaño de cada fragmento (~1000 tokens). **Rango: 1-8 KB** |
| 7 | $f_{overlap}$ | *input* | **1.15** | Factor de solapamiento (15%). **Rango: 1.0-1.5** |
| 8 | $N$ | $(S_{clean} \times f_{overlap}) / C_{chunk}$ | **~244 M** | ⭐ **Cantidad total de vectores** |
| 9 | $d$ | *input* | **1024** | Dimensión del embedding. **Rango: 768-1536** |

> 📊 **Resumen Fase 2:** Tendremos **~244 millones de vectores**. Este número determina todo: almacenamiento, RAM y costos.

#### Fase 3: Almacenamiento por Vector (Pasos 10-14)

| # | Variable | Fórmula | Valor | Descripción |
|:-:|:---------|:--------|:-----:|:------------|
| 10 | $B_{vec}$ | $(4 \times d) + 8$ | **4,104 B** | Bytes por vector (pgvector float32) |
| 11 | $S_{meta}$ | *input* | **200 GB** | Metadata del corpus (IDs, rutas, permisos) |
| 12 | $B_{meta}$ | $S_{meta} / N$ | **~820 B** | Metadata promedio por fila |
| 13 | $B_{overhead}$ | *constante* | **32 B** | Overhead de PostgreSQL por fila |
| 14 | $B_{row}$ | $B_{vec} + B_{meta} + B_{overhead}$ | **~4,956 B** | ⭐ Bytes totales por fila (~4.8 KB) |

#### Fase 4: Almacenamiento Total en Disco (Pasos 15-18)

| # | Variable | Fórmula | Valor | Descripción |
|:-:|:---------|:--------|:-----:|:------------|
| 15 | $S_{table}$ | $N \times B_{row}$ | **~1.1 TB** | Tabla de vectores sin índices |
| 16 | $S_{index}$ | $N \times (4d + M \times 8)$ | **~1.2 TB** | Índice HNSW (M=16) |
| 17 | $f_{over}$ | *input* | **0.30** | Margen para WAL, vacuum. **Rango: 10-30%** |
| 18 | $S_{total}$ | $(S_{table} + S_{index}) \times (1 + f_{over})$ | **~3.0 TB** | ⭐ **Disco total (sin TOAST texto)** |

> 📊 **Resumen Fase 3-4:** Sin texto original: **~3.0 TB**. Con TOAST de texto adicional: **~4.5-5.0 TB total**.

### 2.3 Tabla B: Memoria y Cómputo (Pasos 19-26)

> 💡 **Para no técnicos:** Esta tabla calcula cuánta RAM y CPU necesita el servidor.

#### Fase 5: Dimensionamiento de Memoria RAM (Pasos 19-24)

| # | Variable | Fórmula | Valor | Descripción |
|:-:|:---------|:--------|:-----:|:------------|
| 19 | $N_{batch}$ | *valor ancla* | **5 M** | Vectores por lote al indexar. **Rango: 1-10M** |
| 20 | $RAM_{min}$ | $RAM_{base} + (N_{batch} \times 4 \times d)$ | **~52 GB** | RAM mínima para construcción de índices |
| 21 | $p_{hot}$ | *input* | **0.20** | Fracción del índice en RAM. **Rango: 5-30%** |
| 22 | $RAM_{phot}$ | $p_{hot} \times S_{index}$ | **~240 GB** | RAM para mantener índice caliente |
| 23 | $RAM_{ideal}$ | $\max(RAM_{min}, RAM_{phot})$ | **~240 GB** | ⭐ **RAM recomendada** |
| 24 | $RAM_{buffers}$ | $0.25 \times RAM_{ideal}$ | **~60 GB** | Configuración shared_buffers |

#### Fase 6: Capacidad de Cómputo (Pasos 25-26)

| # | Variable | Fórmula | Valor | Descripción |
|:-:|:---------|:--------|:-----:|:------------|
| 25 | $cpu_{ms}$ | *estimado* | **~20 ms** | Tiempo CPU por consulta (índice caliente) |
| 26 | $vCPU$ | $(QPS \times cpu_{ms}) / 1000 \times 1.5$ | **~2** | vCPUs para queries vectoriales |

### 2.4 Resumen del Escenario Base

#### Tabla Consolidada de Recursos

| Recurso | Valor Calculado | Con TOAST texto | Cloud SQL Tier |
|:--------|:---------------:|:---------------:|:---------------|
| **Vectores totales** | **~244 M** | — | — |
| **Disco SSD** | **~3.0 TB** | **~4.5-5.0 TB** | 5 TB SSD |
| **RAM** | **~240-300 GB** | — | db-custom-48-307200 |
| **vCPU** | **~2 dedicadas** | — | Incluido en tier |
| **Costo estimado** | **~$3,000-3,500/mes** | — | Cloud SQL Enterprise |

#### Diagrama: Composición del Espacio por Fila

```
┌─────────────────────────────────────────────────────────────────┐
│                    POR CADA VECTOR (1 fila ≈ 4,956 B)           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────┐           │
│  │ VECTOR (embedding float32)               4,104 B │ ███████  │  82.8%
│  │ Representación matemática del texto               │          │
│  └──────────────────────────────────────────────────┘           │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐           │
│  │ METADATA                                   820 B │ █        │  16.5%
│  │ doc_id, chunk_id, tenant_id, rutas, permisos      │          │
│  └──────────────────────────────────────────────────┘           │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐           │
│  │ OVERHEAD PostgreSQL                         32 B │          │  0.6%
│  │ Headers, punteros, alineación de fila             │          │
│  └──────────────────────────────────────────────────┘           │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  NOTA: El texto original del chunk (~4 KB) se almacena          │
│  en TOAST separadamente y añade ~1.0-1.5 TB adicionales.        │
└─────────────────────────────────────────────────────────────────┘
```

> ⚠️ **Importante:** Este es el escenario **sin optimizaciones**. En los capítulos posteriores se mostrará cómo reducir estos valores en un 60-70% mediante técnicas de compresión y optimización.

---

## Capítulo 3: Glosario de Variables

### 3.1 Variables de Entrada

Estas son las variables que el equipo debe definir o medir. Modificar estos valores impacta directamente en el dimensionamiento final.

---

#### 📦 $C_{chunk}$ - Tamaño del Chunk (Fragmento)

> **¿Qué es?** El tamaño en bytes de cada fragmento de texto que se convertirá en un vector.

| Aspecto | Descripción |
|:--------|:------------|
| **Origen** | Decisión de diseño RAG. Depende del modelo de embeddings y la naturaleza del contenido. |
| **Rango típico** | 512 bytes - 8 KB (equivale a ~100-2000 tokens) |
| **Valor recomendado** | **4 KB** (~1000 tokens) para documentos técnicos |

| Si $C_{chunk}$ es... | Impacto | Trade-off |
|:---------------------|:--------|:----------|
| **Muy pequeño** (512 B) | Más vectores, mejor precisión de búsqueda | Mayor costo (más almacenamiento, RAM) |
| **Muy grande** (8 KB) | Menos vectores, menor costo | Menor precisión (respuestas menos focalizadas) |

> 💡 **Regla:** Chunks pequeños = más caro pero más preciso. Chunks grandes = más barato pero menos preciso.

---

#### 🔄 $f_{overlap}$ - Factor de Solapamiento

> **¿Qué es?** Cuánto texto se repite entre fragmentos consecutivos para evitar "cortar" ideas a la mitad.

| Aspecto | Descripción |
|:--------|:------------|
| **Origen** | Técnica estándar en RAG para preservar contexto entre chunks. |
| **Rango típico** | 1.0 (sin overlap) a 1.5 (50% overlap) |
| **Valor recomendado** | **1.15** (15% de solapamiento) |

| Si $f_{overlap}$ es... | Impacto | Trade-off |
|:-----------------------|:--------|:----------|
| **1.0** (sin overlap) | Mínimo costo, pero riesgo de perder contexto | Respuestas pueden quedar "cortadas" |
| **1.15-1.25** (15-25%) | Balance óptimo calidad/costo | Recomendado para la mayoría de casos |
| **1.50** (50% overlap) | Máxima calidad, pero 50% más vectores | Solo para documentos muy técnicos/legales |

> 💡 **Regla:** Cada 10% de overlap añade ~10% más vectores y por tanto ~10% más costo.

---

#### 📐 $d$ - Dimensión del Embedding

> **¿Qué es?** La cantidad de números (coordenadas) que representan el significado semántico de cada fragmento.

| Aspecto | Descripción |
|:--------|:------------|
| **Origen** | Definido por el modelo de embeddings elegido (NO es configurable por el usuario). |
| **Valores comunes** | 384, 512, 768, 1024, 1536, 3072 |
| **Nuestro valor base** | **1024** (para modelos como Vertex AI gecko) |
| **Valor optimizado** | **768** (con Matryoshka truncation) |

| Modelo | Dimensión $d$ | Tamaño por vector |
|:-------|:-------------:|:-----------------:|
| Sentence-BERT | 384 | 1.5 KB |
| **Gemini text-embedding-004** | **768-3072** | **3-12 KB** |
| OpenAI text-embedding-3-small | 1536 | 6 KB |
| OpenAI text-embedding-3-large | 3072 | 12 KB |
| Cohere embed-v3 | 1024 | 4 KB |

> 💡 **Regla:** Elegir $d$ es elegir el modelo de embeddings. No se puede cambiar después sin re-vectorizar todo el corpus.

---

#### 📈 $f_{text}$ - Fracción de Texto Extraíble

> **¿Qué es?** Qué proporción del tamaño de los archivos originales es realmente texto (vs. imágenes, formato, binarios).

| Aspecto | Descripción |
|:--------|:------------|
| **Origen** | Medición empírica sobre muestra de documentos. |
| **Rango típico** | 5% - 20% |
| **Valor usado** | **10%** (asunción conservadora) |

| Tipo de documento | $f_{text}$ típico |
|:------------------|:-----------------:|
| PDFs escaneados (imágenes) | 2-5% |
| PDFs con texto seleccionable | 10-15% |
| Documentos Word/Excel | 15-30% |
| Archivos de texto plano | 90-100% |

> ⚠️ **CRÍTICO:** Este valor puede **duplicar o reducir a la mitad** el dimensionamiento. **Validar con muestra real de 500+ documentos antes del despliegue.**

---

#### 🧹 $r_{clean}$ - Ratio de Limpieza

> **¿Qué es?** Qué proporción del texto extraído se descarta por ser duplicados, headers repetidos, o contenido no útil.

| Aspecto | Descripción |
|:--------|:------------|
| **Origen** | Medición empírica durante proceso de limpieza. |
| **Rango típico** | 20% - 50% |
| **Valor usado** | **30%** (asunción moderada) |

| Si $r_{clean}$ es... | Significa... |
|:---------------------|:-------------|
| **20%** (pocos duplicados) | Corpus muy limpio, más vectores resultantes |
| **30%** (moderado) | Situación típica en corporativos |
| **50%** (muchos duplicados) | Documentos con mucha redundancia, menos vectores |

---

### 3.2 Variables Derivadas

Estas variables se calculan a partir de las variables de entrada y constantes del sistema.

---

#### 💾 $B_{vec}$ - Bytes por Vector

> **¿Qué es?** El espacio en disco que ocupa cada vector en pgvector.

| Aspecto | Descripción |
|:--------|:------------|
| **Fórmula** | $(4 \times d) + 8$ bytes |
| **Componentes** | 4 bytes por dimensión (float32) + 8 bytes de header |
| **Valor base (d=1024)** | $(4 \times 1024) + 8 = $ **4,104 bytes** |
| **Valor optimizado (d=768, halfvec)** | $(2 \times 768) + 8 = $ **1,544 bytes** |

> 📚 **Fuente:** [pgvector docs](https://github.com/pgvector/pgvector)

---

#### 🏷️ $B_{meta}$ - Bytes de Metadata por Fila

> **¿Qué es?** Información adicional que guardamos junto a cada vector.

| Metadata incluida | Tamaño aproximado |
|:------------------|:-----------------:|
| Solo IDs (doc_id, chunk_id) | ~50-100 bytes |
| + Ruta del documento | +200-500 bytes |
| + Permisos, tenant_id | +50-100 bytes |
| + Timestamps, scores | +50-100 bytes |
| **Total típico** | **200-800 bytes** |

---

#### 🗄️ $S_{table}$ y $S_{index}$ - Almacenamiento

| Variable | Fórmula | Significado |
|:---------|:--------|:------------|
| **$S_{table}$** | $N \times B_{row}$ | Espacio de la tabla de datos |
| **$S_{index}$** | $N \times (4d + M \times 8)$ | Espacio del índice HNSW |

> 💡 **¿Por qué el índice es casi tan grande como la tabla?**
> 
> El índice HNSW guarda:
> - Una copia de los vectores para calcular distancias
> - M conexiones por cada nivel del grafo (típicamente M=16)
> - Información de niveles jerárquicos
>
> **Resultado:** $S_{index} \approx S_{table}$ (a veces incluso más grande)

---

### 3.3 Tabla de Impacto de Variaciones

Esta tabla muestra cómo cambios en las variables de entrada afectan el dimensionamiento:

| Variable | Cambio | Impacto en $N$ (vectores) | Impacto en Costo |
|:---------|:-------|:-------------------------:|:----------------:|
| $f_{text}$ = 5% (menos texto) | -50% | **-50%** | Ahorro ~$1,500/mes |
| $f_{text}$ = 20% (más texto) | +100% | **+100%** | Aumento ~$3,000/mes |
| $r_{clean}$ = 20% (pocos duplicados) | +14% | **+14%** | Aumento ~$450/mes |
| $r_{clean}$ = 50% (muchos duplicados) | -29% | **-29%** | Ahorro ~$900/mes |
| $C_{chunk}$ = 2 KB (chunks pequeños) | +100% | **+100%** | Aumento ~$3,000/mes |
| $C_{chunk}$ = 8 KB (chunks grandes) | -50% | **-50%** | Ahorro ~$1,500/mes |
| $f_{overlap}$ = 0% (sin overlap) | -13% | **-13%** | Ahorro ~$400/mes |
| $f_{overlap}$ = 25% (overlap alto) | +9% | **+9%** | Aumento ~$270/mes |
| $d$ = 768 (Matryoshka) | 0% vectores | **-25% disco/RAM** | Ahorro ~$800/mes |
| halfvec (float16) | 0% vectores | **-50% disco/RAM** | Ahorro ~$1,000/mes |
| **Combinado (768 + halfvec)** | 0% vectores | **-62% disco/RAM** | **Ahorro ~$1,700/mes** |

> 💡 **Insight Clave:** Las optimizaciones de compresión (Matryoshka + halfvec) tienen el **mayor ROI** porque reducen recursos sin reducir el número de vectores ni la calidad de retrieval significativamente.

---

#### Mapa de Dependencias de Variables

```
                              INPUTS
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
    ┌───────┐              ┌───────┐              ┌───────┐
    │S_raw  │──────┐       │C_chunk│              │  d    │
    │(17 TB)│      │       │(4 KB) │              │(1024) │
    └───────┘      │       └───┬───┘              └───┬───┘
        │          │           │                      │
        ▼          │           │                      ▼
    ┌───────┐      │           │               ┌──────────┐
    │f_text │      │           │               │  B_vec   │
    │(0.10) │      │           │               │(4,104 B) │
    └───┬───┘      │           │               └────┬─────┘
        │          │           │                    │
        ▼          │           │                    │
    ┌───────┐      │           │                    │
    │S_text │◄─────┘           │                    │
    │(1.7TB)│                  │                    │
    └───┬───┘                  │                    │
        │                      │                    │
        ▼                      │                    │
    ┌───────┐                  │                    │
    │r_clean│                  │                    │
    │(0.30) │                  │                    │
    └───┬───┘                  │                    │
        │                      │                    │
        ▼                      │                    │
    ┌───────┐  ┌───────┐       │                    │
    │S_clean│  │f_over │       │                    │
    │(1.19TB│  │(1.15) │       │                    │
    └───┬───┘  └───┬───┘       │                    │
        │          │           │                    │
        └────┬─────┘           │                    │
             │                 │                    │
             ▼                 │                    │
        ┌─────────┐            │                    │
        │    N    │◄───────────┘                    │
        │(244 M)  │                                 │
        └────┬────┘                                 │
             │                                      │
             │    ┌──────────┐                      │
             ├───►│ S_table  │◄─────────────────────┤
             │    │ (1.1 TB) │                      │
             │    └──────────┘                      │
             │                                      │
             │    ┌──────────┐                      │
             └───►│ S_index  │◄─────────────────────┘
                  │ (1.2 TB) │
                  └────┬─────┘
                       │
                       ▼
                  ┌──────────┐
                  │ S_total  │
                  │ (3.0 TB) │
                  └──────────┘
```

---
---

# SECCIÓN II: SELECCIÓN DE TECNOLOGÍA

---

## Capítulo 4: Evaluación de Bases de Datos Vectoriales

### 4.1 Candidatos Evaluados

Se evaluaron las siguientes bases de datos vectoriales, considerando tanto soluciones managed como self-hosted:

| Solución | Tipo | Descripción |
|:---------|:-----|:------------|
| **pgvector** | Extensión PostgreSQL | Extensión open source para PostgreSQL. Soporta HNSW e IVFFlat. |
| **Pinecone** | Serverless Managed | Base de datos vectorial fully-managed. Líder de mercado. |
| **Weaviate** | Open Source / Cloud | BD vectorial con GraphQL. Excelente para búsqueda híbrida. |
| **Vertex AI Vector Search** | GCP Managed | Servicio de Google Cloud optimizado para escala masiva. |
| **Qdrant** | Open Source / Cloud | BD vectorial en Rust. Alto rendimiento y eficiencia. |
| **Milvus** | Open Source | BD vectorial distribuida. Muy escalable pero compleja. |
| **Chroma** | Open Source | Ligera, ideal para desarrollo. No apta para producción a escala. |

### 4.2 Criterios de Evaluación y Pesos

Los criterios fueron definidos según las prioridades del proyecto y las restricciones organizacionales:

| Criterio | Peso | Justificación |
|:---------|:----:|:--------------|
| **Costo Total** | 25% | Presupuesto limitado, necesidad de TCO bajo |
| **Rendimiento** | 20% | Latencia <50ms es un requisito no funcional crítico |
| **Escalabilidad** | 15% | Crecimiento proyectado a 2x en 3 años |
| **Expertise del equipo** | 15% | El equipo ya tiene experiencia con PostgreSQL |
| **Vendor lock-in** | 10% | Preferencia organizacional por flexibilidad |
| **Features** | 10% | Búsqueda híbrida (vector + BM25) es crítica |
| **Soporte y comunidad** | 5% | Enterprise support disponible para las opciones evaluadas |

### 4.3 Benchmarks Comparativos

Los siguientes datos provienen de benchmarks de la industria y documentación oficial de cada proveedor.

#### Latencia de Búsqueda (ms) - Top-K = 10, d = 1024

> **💡 Para no técnicos:** Esta tabla muestra cuántos milisegundos tarda cada sistema en encontrar los 10 documentos más relevantes. Menos es mejor.

| Base de Datos | 1M vectores | 10M vectores | 100M vectores | 500M+ vectores |
|:--------------|:-----------:|:------------:|:-------------:|:--------------:|
| **Vertex AI Vector Search** | 2-5 ms | 3-8 ms | 5-10 ms | 8-15 ms |
| **Pinecone** | 3-8 ms | 5-10 ms | 8-15 ms | 10-20 ms |
| **Qdrant** | 5-10 ms | 10-20 ms | 20-40 ms | 50-100 ms |
| **Milvus** | 5-15 ms | 10-25 ms | 25-50 ms | 50-100 ms |
| **Weaviate** | 8-15 ms | 15-30 ms | 30-60 ms | 80-150 ms |
| **pgvector (HNSW)** | 10-25 ms | 25-50 ms | 50-100 ms | ❌ **Degradado** |
| **Chroma** | 15-30 ms | 50-100 ms | ❌ N/A | ❌ N/A |

> **💡 Por qué Vertex AI y Pinecone son más rápidos:**
> - Índices distribuidos nativamente (sharding automático)
> - Optimización a nivel de hardware (TPUs/GPUs para ANN)
> - Algoritmos propietarios optimizados para escala

#### Throughput (QPS) - Con 1 réplica estándar

> **💡 Para no técnicos:** Cuántas preguntas puede responder el sistema por segundo. Más es mejor.

| Base de Datos | 1M vectores | 10M vectores | 100M vectores | Notas |
|:--------------|:-----------:|:------------:|:-------------:|:------|
| **Vertex AI Vector Search** | 5,000+ | 3,000+ | 1,500+ | Auto-escalado incluido |
| **Pinecone** | 4,000+ | 2,500+ | 1,000+ | Pods serverless |
| **Milvus** | 3,000+ | 2,000+ | 800+ | Requiere tuning |
| **Qdrant** | 2,500+ | 1,500+ | 500+ | Rust, muy eficiente |
| **Weaviate** | 2,000+ | 1,000+ | 400+ | Go, búsqueda híbrida |
| **pgvector** | 500-1,000 | 200-400 | 50-100 | Limitado por PostgreSQL |
| **Chroma** | 100-300 | N/A | N/A | Solo desarrollo |

> **⚠️ Insight:** pgvector tiene **5-10x menos throughput** que soluciones especializadas porque PostgreSQL no fue diseñado para operaciones vectoriales masivas. Sin embargo, nuestro requisito de 30 QPS está muy por debajo de este límite.

#### RAM por Millón de Vectores (d = 1024)

> **💡 Para no técnicos:** Cuánta memoria necesita cada sistema por cada millón de vectores almacenados.

| Base de Datos | RAM/1M Vectores | Incluye Índice | Notas |
|:--------------|:---------------:|:--------------:|:------|
| **Vertex AI Vector Search** | ~4 GB | ✅ Managed | Optimizado internamente |
| **Pinecone** | ~4-5 GB | ✅ Managed | Serverless abstrae esto |
| **Qdrant** | ~5-6 GB | ✅ | HNSW con quantization opcional |
| **Milvus** | ~6-8 GB | ✅ | Depende del índice (IVF vs HNSW) |
| **Weaviate** | ~6-8 GB | ✅ | HNSW + filtros |
| **pgvector (HNSW)** | ~8-12 GB | ⚠️ Parcial | Índice en memoria, datos en disco |
| **Chroma** | ~10-15 GB | ✅ | No optimizado para escala |

#### Costo Mensual por Escala de Vectores (USD/mes)

| Base de Datos | 10M vectores | 100M vectores | 244M vectores | 500M vectores | 1B vectores |
|:--------------|:------------:|:-------------:|:-------------:|:-------------:|:-----------:|
| **pgvector (Cloud SQL)** | $300 | $1,500 | **~$1,500** | $8,000+ ⚠️ | ❌ No viable |
| **Vertex AI Vector Search** | $800 | $3,500 | ~$5,000 | $6,000 | $12,000 |
| **Pinecone Serverless** | $500 | $2,000 | ~$4,500 | $5,000 | $10,000 |
| **Milvus (GKE self-hosted)** | $400 | $1,500 | ~$3,000 | $4,000 | $8,000 |
| **Qdrant Cloud** | $500 | $2,000 | ~$4,500 | $5,000 | $10,000 |

> 💡 **Punto de inflexión económico:** A partir de ~400M vectores, las soluciones managed (Vertex AI, Pinecone) son **más baratas** que escalar pgvector a su máxima capacidad.

---

### 4.4 Matriz Comparativa con Evaluación

| Criterio (Peso) | pgvector | Pinecone | Weaviate | Vertex AI VS | Qdrant |
|:----------------|:--------:|:--------:|:--------:|:------------:|:------:|
| **Costo (25%)** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Rendimiento (20%)** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Escalabilidad (15%)** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Expertise equipo (15%)** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Vendor lock-in (10%)** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Features (10%)** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Soporte (5%)** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

#### Leyenda de Calificación

| Estrellas | Significado |
|:---------:|:------------|
| ⭐⭐⭐⭐⭐ | Excelente - Cumple plenamente con las expectativas |
| ⭐⭐⭐⭐ | Muy bueno - Cumple expectativas con minor trade-offs |
| ⭐⭐⭐ | Bueno - Cumple expectativas básicas |
| ⭐⭐ | Regular - Tiene limitaciones significativas |
| ⭐ | Deficiente - No cumple con las expectativas |

---

### 4.5 Score Ponderado Final

| Solución | Score Ponderado | Costo/mes (244M vec) | Recomendación |
|:---------|:---------------:|:--------------------:|:--------------|
| **pgvector (Cloud SQL)** | **4.25/5** | ~$1,500 | ⭐ **RECOMENDADO** |
| Qdrant Cloud | 3.85/5 | ~$4,500 | Alternativa viable |
| Weaviate Cloud | 3.70/5 | ~$5,000 | Feature-rich pero caro |
| Vertex AI Vector Search | 3.65/5 | ~$5,000 | Bueno si todo es GCP |
| Pinecone | 3.40/5 | ~$4,500 | Muy caro para este volumen |

#### Cálculo del Score (ejemplo pgvector)

```
Score = (5×0.25) + (4×0.20) + (3×0.15) + (5×0.15) + (5×0.10) + (4×0.10) + (4×0.05)
      = 1.25 + 0.80 + 0.45 + 0.75 + 0.50 + 0.40 + 0.20
      = 4.35/5 ≈ 4.25/5 (ajustado por consideraciones cualitativas)
```

---

### 4.6 Decisión: PostgreSQL + pgvector

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DECISIÓN: PostgreSQL + pgvector                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ✅ RAZONES PRINCIPALES:                                                     │
│                                                                              │
│  1. COSTO: 60-70% más barato que alternativas managed                       │
│     • $1,500/mes vs. $4,500/mes (Pinecone/Qdrant)                           │
│     • Ahorro proyectado: ~$36,000/año                                       │
│                                                                              │
│  2. EXPERTISE: El equipo ya conoce PostgreSQL                               │
│     • Menor curva de aprendizaje                                            │
│     • Debugging familiar (EXPLAIN ANALYZE, pg_stat_*)                       │
│     • Integración con herramientas existentes (pg_dump, etc.)               │
│                                                                              │
│  3. FLEXIBILIDAD: Sin vendor lock-in                                        │
│     • Migración a otra infra es posible (on-prem, cualquier cloud)          │
│     • Open source con comunidad activa (>8K GitHub stars)                   │
│     • Formato de datos estándar                                             │
│                                                                              │
│  4. FEATURES: Búsqueda híbrida nativa                                       │
│     • Vector + BM25 (tsvector) en una sola query SQL                        │
│     • No requiere servicios adicionales                                     │
│     • Filtrado por permisos con SQL estándar                                │
│                                                                              │
│  5. ESCALA: Suficiente para 244M-500M vectores                              │
│     • Con optimizaciones (halfvec, Matryoshka) cubre roadmap de 3 años      │
│     • Cloud SQL Enterprise soporta hasta 64 TB y 624 GB RAM                 │
│                                                                              │
│  6. COMPLIANCE: Ya aprobado por el área de seguridad                        │
│     • PostgreSQL ya está en el stack aprobado                               │
│     • Cloud SQL Enterprise tiene certificaciones SOC2, ISO 27001            │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ⚠️ LIMITACIONES ACEPTADAS:                                                 │
│                                                                              │
│  • Escalabilidad manual (vs. auto-scale de Pinecone)                        │
│    → Mitigación: Monitoreo proactivo, alertas en 70% capacidad              │
│                                                                              │
│  • Requiere tuning de índices HNSW                                          │
│    → Mitigación: Configuración documentada, runbooks preparados             │
│                                                                              │
│  • No hay UI de administración visual                                       │
│    → Mitigación: pgAdmin, Cloud SQL Studio, queries SQL                     │
│                                                                              │
│  • Throughput limitado (~200-400 QPS para 244M vectores)                    │
│    → Mitigación: Nuestro requisito es solo 30 QPS (margen 10x)              │
│                                                                              │
│  • Límite de escala: ~500M vectores máximo práctico                         │
│    → Mitigación: Plan de migración a Vertex AI si >400M                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.7 Punto de Inflexión: ¿Cuándo Migrar a Vertex AI?

Calculamos el momento óptimo de migración basado en tres criterios:

#### Criterio 1: Técnico (RAM)

```
¿Cuándo el índice supera la RAM máxima de Cloud SQL?

RAM máxima Cloud SQL = 624 GB
Índice al 20% caliente = 624 / 0.20 = 3.1 TB máximo de índice
Vectores correspondientes = 3.1 TB / 5 KB ≈ 600 M vectores

→ Límite técnico: ~600 M vectores
```

#### Criterio 2: Performance (Latencia)

```
¿Cuándo la latencia P95 supera 50 ms?

Basado en nuestro modelo, esto ocurre cuando:
- Solo 10% del índice está en RAM
- Equivale a ~400 M vectores con 250 GB RAM

→ Límite de performance: ~400 M vectores
```

#### Criterio 3: Económico (Costo)

```
¿Cuándo Vertex AI es más barato que pgvector?

Cloud SQL db-custom-96-614400 (máximo) = $8,500/mes
Vertex AI para 400M vectores = $6,000/mes

→ Punto de inflexión económico: ~400 M vectores
```

#### Conclusión del Punto de Inflexión

$$
\boxed{
\text{Punto de Inflexión} = \min(600M, 400M, 400M) = 400M \text{ vectores}
}
$$

> **Recomendación:** Iniciar PoC de Vertex AI cuando alcancemos **300 M vectores** (~mes 12-15), y migrar completamente antes de alcanzar **400 M vectores** (~mes 18).

---

## Capítulo 5: Arquitectura de Referencia

### 5.1 Diagrama de Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           ENTERPRISE AI PLATFORM - ARQUITECTURA RAG                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                              CAPA DE PRESENTACIÓN                                   │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                     │ │
│  │  │   Web App       │  │   API REST      │  │   Chatbot       │                     │ │
│  │  │   (Next.js)     │  │   (FastAPI)     │  │   (Slack/Teams) │                     │ │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘                     │ │
│  │           └───────────────────┬───────────────────────┘                             │ │
│  └───────────────────────────────┼─────────────────────────────────────────────────────┘ │
│                                  ▼                                                       │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                              CAPA DE ORQUESTACIÓN                                   │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                         RAG Orchestrator (LangChain/LlamaIndex)              │   │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │   │ │
│  │  │  │   Query     │  │  Retrieval  │  │  Reranking  │  │    Generation       │ │   │ │
│  │  │  │ Processing  │─▶│   Engine    │─▶│   (Cohere)  │─▶│   (Gemini Pro)      │ │   │ │
│  │  │  └─────────────┘  └──────┬──────┘  └─────────────┘  └─────────────────────┘ │   │ │
│  │  │                          │                                                   │   │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐│   │ │
│  │  │  │                    Semantic Cache (Redis)                                ││   │ │
│  │  │  └─────────────────────────────────────────────────────────────────────────┘│   │ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────┼───────────────────────────────────────────────────┘ │
│                                   ▼                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                              CAPA DE DATOS                                          │ │
│  │                                                                                      │ │
│  │  ┌─────────────────────────────────────────┐  ┌─────────────────────────────────┐  │ │
│  │  │        VECTOR STORE (Principal)          │  │      DOCUMENT STORE             │  │ │
│  │  │  ┌─────────────────────────────────────┐ │  │  ┌─────────────────────────────┐│  │ │
│  │  │  │    Cloud SQL Enterprise (pgvector)  │ │  │  │    Cloud Storage (GCS)      ││  │ │
│  │  │  │                                     │ │  │  │                             ││  │ │
│  │  │  │    • 244M vectores                  │ │  │  │    • 17 TB documentos       ││  │ │
│  │  │  │    • halfvec(768) + HNSW            │ │  │  │    • PDFs, Office, texto    ││  │ │
│  │  │  │    • Particionado por área          │ │  │  │    • Versionados            ││  │ │
│  │  │  │    • Hybrid search (vec + BM25)     │ │  │  │                             ││  │ │
│  │  │  └─────────────────────────────────────┘ │  │  └─────────────────────────────┘│  │ │
│  │  │                                          │  │                                  │  │ │
│  │  │  ┌─────────────────────────────────────┐ │  │  ┌─────────────────────────────┐│  │ │
│  │  │  │    Read Replicas (2x)               │ │  │  │    Metadata Store           ││  │ │
│  │  │  │    • Distribución de carga          │ │  │  │    (Cloud SQL PostgreSQL)  ││  │ │
│  │  │  │    • HA Zone-redundant              │ │  │  │    • Permisos, tenants      ││  │ │
│  │  │  └─────────────────────────────────────┘ │  │  │    • Audit logs             ││  │ │
│  │  └─────────────────────────────────────────┘  │  └─────────────────────────────┘│  │ │
│  │                                                └─────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                              CAPA DE INGESTIÓN                                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │ │
│  │  │  OpenText   │  │  Document   │  │  Chunking   │  │  Embedding  │                │ │
│  │  │  Connector  │─▶│  Parser     │─▶│  Engine     │─▶│  Service    │────────────┐   │ │
│  │  │             │  │  (Unstructured)│ (LangChain) │  │  (Gemini)   │            │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │   │ │
│  │                                                                                 │   │ │
│  │         ┌───────────────────────────────────────────────────────────────────────┘   │ │
│  │         ▼                                                                           │ │
│  │  ┌─────────────────────┐                                                            │ │
│  │  │  Cloud Pub/Sub      │  (Cola de procesamiento asíncrono)                         │ │
│  │  │  + Cloud Functions  │                                                            │ │
│  │  └─────────────────────┘                                                            │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Componentes del Sistema

#### Componentes Principales

| Componente | Tecnología | Responsabilidad | Ubicación GCP |
|:-----------|:-----------|:----------------|:--------------|
| **Vector Store** | Cloud SQL Enterprise + pgvector | Almacenamiento y búsqueda de embeddings | southamerica-east1 |
| **Embedding Service** | Gemini text-embedding-004 | Generación de embeddings 768d | Vertex AI API |
| **LLM** | Gemini 1.5 Pro | Generación de respuestas | Vertex AI API |
| **Reranker** | Cohere Rerank v3 | Reordenamiento de resultados | API externa |
| **Semantic Cache** | Memorystore for Redis | Cache de queries y respuestas | southamerica-east1 |
| **Document Store** | Cloud Storage | Documentos originales (17 TB) | southamerica-east1 |
| **Orchestrator** | Cloud Run | Lógica de negocio RAG | southamerica-east1 |
| **Message Queue** | Cloud Pub/Sub | Cola de ingestión asíncrona | Global |

#### Componentes de Soporte

| Componente | Tecnología | Responsabilidad |
|:-----------|:-----------|:----------------|
| **Logging** | Cloud Logging | Logs centralizados |
| **Monitoring** | Cloud Monitoring | Métricas y dashboards |
| **Tracing** | Cloud Trace | Distributed tracing |
| **Secrets** | Secret Manager | Gestión de credenciales |
| **IAM** | Cloud IAM | Control de acceso |

---

### 5.3 Flujo de Datos: Ingestión

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           PIPELINE DE INGESTIÓN (Batch/Streaming)                        │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  FUENTE                 EXTRACCIÓN              PROCESAMIENTO              ALMACENAMIENTO│
│  ──────                 ──────────              ─────────────              ──────────────│
│                                                                                          │
│  ┌─────────┐           ┌─────────┐            ┌─────────────┐            ┌─────────────┐│
│  │OpenText │──────────▶│ Document│───────────▶│  Chunking   │───────────▶│  Embedding  ││
│  │ (17 TB) │  CDC      │ Parser  │  Texto     │  Recursive  │  Chunks    │  Gemini 768d││
│  └─────────┘  Hourly   └─────────┘  Limpio    │  4KB + 15%  │  244M      └──────┬──────┘│
│                        (Unstructured)          └─────────────┘                   │       │
│  ┌─────────┐                                                                     │       │
│  │SharePoint│                                                                    ▼       │
│  │ (500GB) │──────────────────────────────────────────────────────────▶ ┌─────────────┐│
│  └─────────┘                                                             │   Cloud     ││
│                                                                          │   Pub/Sub   ││
│  ┌─────────┐                                                             │   Queue     ││
│  │Confluence                                                             └──────┬──────┘│
│  │ (200GB) │────────────────────────────────────────────────────────────────────│       │
│  └─────────┘                                                                     │       │
│                                                                                  ▼       │
│                         ┌──────────────────────────────────────────────────────────────┐│
│                         │                    UPSERT BATCH                               ││
│                         │  ┌────────────────────────────────────────────────────────┐  ││
│                         │  │ Cloud SQL Enterprise (pgvector)                        │  ││
│                         │  │                                                        │  ││
│                         │  │  INSERT INTO embeddings (doc_id, chunk_id, area,       │  ││
│                         │  │                          embedding, metadata)          │  ││
│                         │  │  VALUES (...)                                          │  ││
│                         │  │  ON CONFLICT (doc_id, chunk_id) DO UPDATE;             │  ││
│                         │  │                                                        │  ││
│                         │  │  → Particionado por área (RRHH, Legal, Ops, ...)       │  ││
│                         │  │  → Índice HNSW reconstruido post-batch                 │  ││
│                         │  └────────────────────────────────────────────────────────┘  ││
│                         └──────────────────────────────────────────────────────────────┘│
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Pasos del Pipeline de Ingestión

| Paso | Componente | Acción | Output |
|:----:|:-----------|:-------|:-------|
| 1 | **CDC Connector** | Detecta documentos nuevos/modificados en OpenText | Lista de doc_ids |
| 2 | **Document Parser** | Extrae texto de PDF, Office, etc. | Texto plano limpio |
| 3 | **Deduplicator** | Elimina contenido duplicado/redundante | Texto único |
| 4 | **Chunker** | Fragmenta en chunks de 4KB con 15% overlap | ~244M chunks |
| 5 | **Embedder** | Genera embedding 768d con Gemini | Vectors halfvec(768) |
| 6 | **Queue** | Encola para procesamiento asíncrono | Pub/Sub messages |
| 7 | **Loader** | Inserta en pgvector con UPSERT | Rows en DB |
| 8 | **Indexer** | Actualiza índice HNSW (batch nocturno) | Índice optimizado |

---

### 5.4 Flujo de Datos: Búsqueda (Query)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           PIPELINE DE BÚSQUEDA (Online, <3seg E2E)                       │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  USUARIO              CACHE                RETRIEVAL              GENERATION             │
│  ───────              ─────                ─────────              ──────────             │
│                                                                                          │
│  ┌─────────┐        ┌─────────┐          ┌───────────────────────────────────────────┐  │
│  │ "¿Cuál  │───────▶│ Redis   │───HIT───▶│ Respuesta cacheada (latencia ~5ms)        │  │
│  │  es la  │        │ Cache   │          └───────────────────────────────────────────┘  │
│  │  política│        │ Semántico         │ MISS                                          │
│  │  de     │        └────┬────┘          ▼                                              │
│  │  vacaciones?"         │        ┌─────────────┐                                       │
│  └─────────┘             │        │  Query      │                                       │
│                          │        │  Embedding  │                                       │
│                          │        │  (Gemini)   │ ~50ms                                 │
│                          │        └──────┬──────┘                                       │
│                          │               ▼                                              │
│                          │        ┌─────────────────────────────────────────────────┐   │
│                          │        │           HYBRID SEARCH (pgvector)              │   │
│                          │        │  ┌─────────────────┐  ┌─────────────────────┐   │   │
│                          │        │  │ Vector Search   │  │  BM25 Search        │   │   │
│                          │        │  │ (HNSW cosine)   │  │  (tsvector)         │   │   │
│                          │        │  │ → Top 30        │  │  → Top 30           │   │   │
│                          │        │  └────────┬────────┘  └──────────┬──────────┘   │   │
│                          │        │           └──────────┬───────────┘              │   │
│                          │        │                      ▼                          │   │
│                          │        │        ┌─────────────────────────┐              │   │
│                          │        │        │  RRF (Reciprocal Rank   │  ~25ms      │   │
│                          │        │        │  Fusion) → Top 50       │              │   │
│                          │        │        └─────────────────────────┘              │   │
│                          │        └──────────────────────┬──────────────────────────┘   │
│                          │                               ▼                              │
│                          │        ┌─────────────────────────────────────────────────┐   │
│                          │        │         RERANKING (Cohere Rerank)               │   │
│                          │        │         Top 50 → Top 10 (~80ms)                 │   │
│                          │        └──────────────────────┬──────────────────────────┘   │
│                          │                               ▼                              │
│                          │        ┌─────────────────────────────────────────────────┐   │
│                          │        │         LLM GENERATION (Gemini Pro)             │   │
│                          │        │         Context: Top 10 chunks (~1500ms)        │   │
│                          │        │         Response + Citations                    │   │
│                          │        └──────────────────────┬──────────────────────────┘   │
│                          │                               ▼                              │
│                          │        ┌─────────────────────────────────────────────────┐   │
│                          └───────▶│         CACHE UPDATE (Redis)                    │   │
│                                   │         TTL: 24 horas, LRU eviction             │   │
│                                   └──────────────────────┬──────────────────────────┘   │
│                                                          ▼                              │
│                                   ┌─────────────────────────────────────────────────┐   │
│                                   │              RESPUESTA AL USUARIO               │   │
│                                   │  "Los empleados tienen 15 días hábiles..."     │   │
│                                   │  📎 Fuentes: politica_rrhh_2024.pdf (p.12)      │   │
│                                   └─────────────────────────────────────────────────┘   │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Latencia por Componente

| Componente | Latencia P50 | Latencia P95 | Notas |
|:-----------|:------------:|:------------:|:------|
| **Cache Check** | 1 ms | 3 ms | Redis local |
| **Query Embedding** | 30 ms | 50 ms | Gemini API |
| **Hybrid Search** | 15 ms | 25 ms | pgvector HNSW + BM25 |
| **Reranking** | 60 ms | 100 ms | Cohere API (opcional) |
| **LLM Generation** | 1,200 ms | 2,000 ms | Gemini Pro |
| **Total (sin cache)** | ~1,300 ms | ~2,200 ms | Dentro del SLO de 3s |
| **Total (cache hit)** | 3 ms | 5 ms | 67% hit rate esperado |

---

### 5.5 Integraciones con GCP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SERVICIOS GCP UTILIZADOS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        COMPUTE & RUNTIME                                 ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │ Cloud Run   │  │ Cloud       │  │ GKE         │  │ Cloud       │    ││
│  │  │ (API/Web)   │  │ Functions   │  │ (Opcional)  │  │ Scheduler   │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        DATA & STORAGE                                    ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │ Cloud SQL   │  │ Memorystore │  │ Cloud       │  │ BigQuery    │    ││
│  │  │ (pgvector)  │  │ (Redis)     │  │ Storage     │  │ (Analytics) │    ││
│  │  │ PRINCIPAL   │  │ CACHE       │  │ DOCS        │  │ OPCIONAL    │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        AI & ML                                           ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────────┐  ││
│  │  │ Vertex AI   │  │ Vertex AI   │  │ (Futuro) Vertex AI              │  ││
│  │  │ Embeddings  │  │ Gemini Pro  │  │ Vector Search                   │  ││
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        MESSAGING & INTEGRATION                           ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     ││
│  │  │ Cloud       │  │ Cloud       │  │ Eventarc    │                     ││
│  │  │ Pub/Sub     │  │ Tasks       │  │ (Triggers)  │                     ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘                     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        SECURITY & GOVERNANCE                             ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │ Cloud IAM   │  │ Secret      │  │ Cloud       │  │ VPC Service │    ││
│  │  │             │  │ Manager     │  │ Armor       │  │ Controls    │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        OBSERVABILITY                                     ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │ Cloud       │  │ Cloud       │  │ Cloud       │  │ Error       │    ││
│  │  │ Monitoring  │  │ Logging     │  │ Trace       │  │ Reporting   │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Resumen de Servicios GCP

| Categoría | Servicio | Propósito | SKU/Tier |
|:----------|:---------|:----------|:---------|
| **Compute** | Cloud Run | API RAG | Gen2, 4 vCPU, 8GB RAM |
| **Database** | Cloud SQL Enterprise | Vector Store | db-custom-48-307200 |
| **Cache** | Memorystore Redis | Semantic Cache | Standard, 8GB |
| **Storage** | Cloud Storage | Documentos | Standard, 17TB |
| **AI** | Vertex AI Embeddings | text-embedding-004 | Pay-per-use |
| **AI** | Vertex AI Generative | Gemini 1.5 Pro | Pay-per-use |
| **Messaging** | Cloud Pub/Sub | Cola ingestión | Standard |
| **Observability** | Cloud Operations Suite | Logs, metrics, traces | Standard |

---
---

# SECCIÓN III: TÉCNICAS DE OPTIMIZACIÓN

> **Nota:** Esta sección explica QUÉ son las técnicas y CÓMO funcionan. El impacto en costos se calculará en detalle en la Sección V (Análisis de Escenarios y Costos).

---

## Capítulo 6: Compresión de Embeddings

### 6.1 Matryoshka Representation Learning

#### ¿Qué es Matryoshka?

> **Analogía: Muñecas Rusas 🪆**
> 
> Las muñecas Matryoshka (muñecas rusas) tienen una característica única: cada muñeca contiene versiones más pequeñas de sí misma dentro.
> 
> Los **Matryoshka embeddings** funcionan igual: un embedding de 3072 dimensiones contiene dentro de sí un embedding válido de 1536, 768, 512, 256... dimensiones.
> 
> | Dimensión | Información contenida |
> |:---------:|:---------------------|
> | 3072d | 100% del significado |
> | 1536d | ~99% del significado |
> | 768d | ~98% del significado ← **Punto óptimo** |
> | 512d | ~95% del significado |
> | 256d | ~90% del significado |

#### ¿Cómo funciona?

Los modelos entrenados con Matryoshka Representation Learning (MRL) organizan la información de forma jerárquica:

```
┌─────────────────────────────────────────────────────────────────┐
│                ESTRUCTURA MATRYOSHKA                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Embedding completo (3072 dimensiones):                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │[d1,d2,d3,...,d256│d257,...,d512│d513,...,d768│...│...,d3072]││
│  └─────────────────────────────────────────────────────────────┘│
│       ▲               ▲              ▲                          │
│       │               │              │                          │
│       │               │              └── Dimensiones 513-768:   │
│       │               │                  Detalles finos         │
│       │               │                                         │
│       │               └── Dimensiones 257-512:                  │
│       │                   Contexto adicional                    │
│       │                                                         │
│       └── Dimensiones 1-256:                                    │
│           Significado esencial (tópicos, conceptos clave)       │
│                                                                  │
│  ✂️ TRUNCATION: Solo tomamos las primeras N dimensiones         │
│                                                                  │
│  [d1,d2,d3,...,d768] ← 768d contiene el 98% del significado     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Modelos Compatibles con Matryoshka

| Modelo | Dimensión Nativa | Dimensiones Soportadas | Multilingüe | Recomendado |
|:-------|:----------------:|:----------------------:|:-----------:|:-----------:|
| **Gemini text-embedding-004** | 768-3072 | 256, 512, 768, 1536, 3072 | ✅ | ⭐ **Sí** |
| OpenAI text-embedding-3-small | 1536 | 256, 512, 1024, 1536 | ✅ | Alternativa |
| OpenAI text-embedding-3-large | 3072 | 256, 512, 1024, 1536, 3072 | ✅ | Alternativa |
| Cohere embed-v3 | 1024 | 256, 512, 1024 | ✅ | Alternativa |
| nomic-embed-text-v1.5 | 768 | 64, 128, 256, 512, 768 | ❌ | Solo inglés |
| mxbai-embed-large-v1 | 1024 | 256, 512, 768, 1024 | ❌ | Solo inglés |

> ⚠️ **Importante:** No todos los modelos soportan Matryoshka. Verificar en la documentación del proveedor antes de usar truncation.

#### Configuración de Gemini para Matryoshka

```python
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel

# Inicializar modelo
model = TextEmbeddingModel.from_pretrained("text-embedding-004")

# Solicitar embeddings con dimensión reducida (Matryoshka)
embeddings = model.get_embeddings(
    texts=["Tu texto aquí para vectorizar"],
    output_dimensionality=768  # ← Matryoshka truncation a 768d
)

# Extraer el vector
vector_768d = embeddings[0].values  # Lista de 768 floats
print(f"Dimensiones: {len(vector_768d)}")  # Output: 768
```

---

### 6.2 halfvec (Float16) en pgvector

#### ¿Qué es halfvec?

> **Analogía: Redondear Precios 💵**
> 
> Cuando guardas precios, ¿necesitas todos los decimales?
> 
> | Precio exacto (float32) | Redondeado (float16) | ¿Se nota? |
> |:-----------------------:|:--------------------:|:---------:|
> | $45.3729847 | $45.37 | No |
> | $1,234.56789 | $1,234.57 | No |
> | $0.000012345 | $0.00001 | Sí (pero raro) |
> 
> En búsquedas vectoriales, pequeñas diferencias decimales casi nunca cambian cuál es el "documento más similar".

#### Comparación de Precisiones

| Tipo | Bytes/número | Rango | Precisión | Uso típico |
|:-----|:------------:|:------|:----------|:-----------|
| **float32** | 4 | ±3.4×10³⁸ | ~7 dígitos | Precisión estándar |
| **float16 (halfvec)** | 2 | ±65,504 | ~3.3 dígitos | ⭐ Recomendado |
| **bfloat16** | 2 | ±3.4×10³⁸ | ~3.3 dígitos | ML training (no en pgvector) |
| **int8** | 1 | -128 a 127 | Enteros | Cuantización agresiva |

#### Soporte en pgvector

| Versión pgvector | halfvec | Índices HNSW | Operadores |
|:-----------------|:-------:|:------------:|:-----------|
| < 0.7.0 | ❌ | — | — |
| **0.7.0+** | ✅ | ✅ | `halfvec_cosine_ops`, `halfvec_l2_ops`, `halfvec_ip_ops` |

#### Implementación SQL

```sql
-- ============================================================
-- PASO 1: Verificar versión de pgvector
-- ============================================================
SELECT extversion FROM pg_extension WHERE extname = 'vector';
-- Debe ser >= 0.7.0

-- ============================================================
-- PASO 2: Crear tabla con halfvec
-- ============================================================
CREATE TABLE embeddings_optimized (
    id BIGSERIAL PRIMARY KEY,
    doc_id UUID NOT NULL,
    chunk_id INTEGER NOT NULL,
    area VARCHAR(50) NOT NULL,
    chunk_text TEXT,
    
    -- 💡 halfvec(768) usa solo 1,544 bytes vs 3,080 de vector(768)
    embedding halfvec(768),
    
    -- Metadata
    file_path TEXT,
    page_number INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraint para evitar duplicados
    UNIQUE(doc_id, chunk_id)
);

-- ============================================================
-- PASO 3: Crear índice HNSW para halfvec
-- ============================================================
CREATE INDEX idx_embeddings_hnsw ON embeddings_optimized 
USING hnsw (embedding halfvec_cosine_ops)
WITH (
    m = 16,              -- Conexiones por nodo (balance memoria/calidad)
    ef_construction = 64 -- Calidad de construcción del índice
);

-- ============================================================
-- PASO 4: Query de búsqueda con halfvec
-- ============================================================
SELECT 
    doc_id,
    chunk_text,
    1 - (embedding <=> $1::halfvec) AS similarity
FROM embeddings_optimized
WHERE area = 'RRHH'  -- Partition pruning
ORDER BY embedding <=> $1::halfvec
LIMIT 10;

-- ============================================================
-- PASO 5: Migración de float32 a halfvec (si hay datos existentes)
-- ============================================================
-- Crear nueva tabla
CREATE TABLE embeddings_new (LIKE embeddings_optimized);

-- Migrar con conversión de tipo
INSERT INTO embeddings_new (doc_id, chunk_id, area, chunk_text, embedding, ...)
SELECT doc_id, chunk_id, area, chunk_text, 
       embedding::halfvec,  -- ← Conversión automática
       ...
FROM embeddings_original;

-- Renombrar tablas
ALTER TABLE embeddings_original RENAME TO embeddings_backup;
ALTER TABLE embeddings_new RENAME TO embeddings_optimized;
```

---

### 6.3 Combinación Óptima: Pipeline de Compresión

La estrategia de mayor impacto combina Matryoshka (reducción de dimensiones) con halfvec (reducción de precisión):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PIPELINE DE COMPRESIÓN                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ENTRADA                                                                     │
│  ───────                                                                     │
│  "La política de vacaciones establece que los empleados..."                 │
│                                                                              │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     PASO 1: EMBEDDING (Gemini API)                       ││
│  │                                                                          ││
│  │  model.get_embeddings(texts, output_dimensionality=768)                  ││
│  │                                                                          ││
│  │  Output: [0.123, -0.456, 0.789, ..., 0.234]  ← 768 floats (float32)      ││
│  │  Tamaño: 768 × 4 bytes = 3,072 bytes                                     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     PASO 2: QUANTIZATION (Python)                        ││
│  │                                                                          ││
│  │  import numpy as np                                                      ││
│  │  embedding_f16 = np.array(embedding, dtype=np.float16)                   ││
│  │                                                                          ││
│  │  Output: [0.123, -0.456, 0.789, ..., 0.234]  ← 768 half-precision       ││
│  │  Tamaño: 768 × 2 bytes = 1,536 bytes                                     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     PASO 3: STORAGE (pgvector)                           ││
│  │                                                                          ││
│  │  INSERT INTO embeddings_optimized (embedding, ...)                       ││
│  │  VALUES ($1::halfvec, ...);                                              ││
│  │                                                                          ││
│  │  Almacenado: halfvec(768) = 1,544 bytes (con header)                     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  RESULTADO                                                                   │
│  ─────────                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                                                                          ││
│  │  BASELINE (1024d float32):    4,104 bytes/vector                         ││
│  │  OPTIMIZADO (768d halfvec):   1,544 bytes/vector                         ││
│  │                                                                          ││
│  │  REDUCCIÓN: 62% menos almacenamiento                                     ││
│  │  CALIDAD:   ~97.5% del recall original                                   ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Código Python Completo del Pipeline

```python
import numpy as np
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
import psycopg2

class OptimizedEmbeddingPipeline:
    """Pipeline de embeddings optimizado con Matryoshka + halfvec."""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    
    def embed(self, texts: list[str]) -> list[np.ndarray]:
        """Genera embeddings Matryoshka + float16."""
        
        # Paso 1: Obtener embeddings con dimensión reducida (Matryoshka)
        embeddings = self.model.get_embeddings(
            texts=texts,
            output_dimensionality=self.dimension  # ← Matryoshka
        )
        
        # Paso 2: Convertir a float16 (halfvec)
        vectors = [
            np.array(emb.values, dtype=np.float16)  # ← Quantization
            for emb in embeddings
        ]
        
        return vectors
    
    def insert_batch(self, conn, records: list[dict]):
        """Inserta batch de vectores optimizados en pgvector."""
        
        with conn.cursor() as cur:
            for record in records:
                # Convertir numpy array a formato pgvector
                vector_str = "[" + ",".join(map(str, record["embedding"])) + "]"
                
                cur.execute("""
                    INSERT INTO embeddings_optimized 
                    (doc_id, chunk_id, area, chunk_text, embedding)
                    VALUES (%s, %s, %s, %s, %s::halfvec)
                    ON CONFLICT (doc_id, chunk_id) DO UPDATE
                    SET embedding = EXCLUDED.embedding,
                        chunk_text = EXCLUDED.chunk_text;
                """, (
                    record["doc_id"],
                    record["chunk_id"],
                    record["area"],
                    record["chunk_text"],
                    vector_str
                ))
            
            conn.commit()

# Uso
pipeline = OptimizedEmbeddingPipeline(dimension=768)
vectors = pipeline.embed(["Texto del chunk 1", "Texto del chunk 2"])
```

---

### 6.4 Tabla de Impacto Teórico por Estrategia

| Estrategia | Dimensión | Precisión | Bytes/vector | Disco (244M vec) | RAM (20% hot) | Costo/mes | Retención Calidad |
|:-----------|:---------:|:---------:|:------------:|:----------------:|:-------------:|:---------:|:-----------------:|
| **Baseline** (1024d float32) | 1024 | float32 | 4,104 B | ~3.0 TB | ~240 GB | ~$3,200 | 100% |
| Matryoshka 768d | 768 | float32 | 3,080 B | ~2.3 TB | ~180 GB | ~$2,400 | ~98% |
| Matryoshka 512d | 512 | float32 | 2,056 B | ~1.5 TB | ~120 GB | ~$1,800 | ~95% |
| halfvec (1024d float16) | 1024 | float16 | 2,056 B | ~1.5 TB | ~120 GB | ~$1,800 | ~99.9% |
| **Matryoshka 768d + halfvec** | **768** | **float16** | **1,544 B** | **~1.1 TB** | **~90 GB** | **~$1,500** | **~97.5%** |
| Matryoshka 512d + halfvec | 512 | float16 | 1,032 B | ~0.8 TB | ~65 GB | ~$1,100 | ~94% |

> ⭐ **Recomendación:** Usar **Matryoshka 768d + halfvec** como configuración por defecto. Ofrece el mejor balance entre ahorro (53% menos disco/RAM) y calidad (97.5% recall).

---

### 6.5 Otras Estrategias de Compresión

Existen técnicas adicionales más agresivas que pueden considerarse para casos específicos:

| Técnica | Descripción | Reducción | Pérdida Calidad | Cuándo usar |
|:--------|:------------|:---------:|:---------------:|:------------|
| **Binary Quantization** | Vectores binarios (1 bit/dim) | 97% | 5-15% | Filtrado rápido + rerank |
| **Product Quantization (PQ)** | Divide vector en sub-vectores | 90-95% | 2-5% | Billones de vectores |
| **Scalar Quantization (SQ)** | int8 por dimensión | 75% | 1-2% | Alternativa a halfvec |
| **Coarse Quantization** | Clustering + residuos | Variable | 1-3% | IVF-based indexes |

> ⚠️ **Nota:** pgvector 0.7+ soporta nativamente `halfvec`. Para estrategias más agresivas como PQ, considerar Faiss o Milvus.

---

## Capítulo 7: Particionamiento de Datos

### 7.1 Concepto y Beneficios

> **Analogía: Biblioteca con Catálogos Separados 📚**
> 
> Imagina una biblioteca con UN solo catálogo gigante de 17 millones de libros vs. catálogos separados por sección:
> 
> | Enfoque | Buscar "contratos de trabajo" |
> |:--------|:------------------------------|
> | **1 catálogo gigante** | Revisar 17M entradas, encontrar en sección RRHH |
> | **Catálogos por sección** | Ir directo a catálogo RRHH, revisar solo 2.5M entradas |
> 
> El particionamiento por área funcional permite a PostgreSQL "saltar" directamente a la partición relevante.

#### ¿Qué es Partition Pruning?

Cuando PostgreSQL ejecuta una query con filtro por área:

```sql
SELECT * FROM embeddings WHERE area = 'RRHH' AND embedding <=> $1 < 0.3;
```

El **Partition Pruning** automáticamente:
1. Identifica que solo la partición `embeddings_rrhh` es relevante
2. Ignora completamente las demás particiones
3. Ejecuta la búsqueda HNSW solo en ~37M vectores (no en 244M)

### 7.2 Particionamiento Nativo PostgreSQL vs. Tablas Separadas

| Aspecto | Particionamiento Nativo | Tablas Separadas |
|:--------|:-----------------------:|:----------------:|
| **Complejidad** | Media | Baja |
| **Queries cross-área** | ✅ Automático | ❌ Requiere UNION ALL manual |
| **Índices** | Un índice por partición (automático) | Índices independientes |
| **Mantenimiento** | ✅ Comandos estándar | Manual por tabla |
| **Escalabilidad** | Hasta ~100 particiones | Ilimitado |
| **Recomendado** | ⭐ Para la mayoría de casos | Solo si >100 áreas |

### 7.3 Implementación SQL

```sql
-- ============================================================
-- ESQUEMA PARTICIONADO POR ÁREA FUNCIONAL
-- ============================================================

-- Paso 1: Crear tabla padre particionada
CREATE TABLE embeddings (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    doc_id UUID NOT NULL,
    chunk_id INTEGER NOT NULL,
    area VARCHAR(50) NOT NULL,
    chunk_text TEXT,
    embedding halfvec(768),
    file_path TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (id, area)  -- ← área debe estar en la PK
) PARTITION BY LIST (area);

-- Paso 2: Crear particiones por área
CREATE TABLE embeddings_rrhh 
    PARTITION OF embeddings FOR VALUES IN ('RRHH');

CREATE TABLE embeddings_callcenter 
    PARTITION OF embeddings FOR VALUES IN ('CALL_CENTER');

CREATE TABLE embeddings_legal 
    PARTITION OF embeddings FOR VALUES IN ('LEGAL');

CREATE TABLE embeddings_operaciones 
    PARTITION OF embeddings FOR VALUES IN ('OPERACIONES');

CREATE TABLE embeddings_finanzas 
    PARTITION OF embeddings FOR VALUES IN ('FINANZAS');

CREATE TABLE embeddings_otros 
    PARTITION OF embeddings FOR VALUES IN ('OTROS');

-- Paso 3: Crear índices HNSW en cada partición
-- (PostgreSQL crea índices automáticamente en cada partición)
CREATE INDEX idx_embeddings_hnsw ON embeddings 
USING hnsw (embedding halfvec_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Esto crea automáticamente:
-- idx_embeddings_hnsw_rrhh
-- idx_embeddings_hnsw_callcenter
-- idx_embeddings_hnsw_legal
-- ... etc

-- Paso 4: Índice BM25 para búsqueda híbrida (opcional)
CREATE INDEX idx_embeddings_fts ON embeddings 
USING gin (to_tsvector('spanish', chunk_text));

-- ============================================================
-- EJEMPLO DE QUERY CON PARTITION PRUNING
-- ============================================================

EXPLAIN (ANALYZE, BUFFERS) 
SELECT doc_id, chunk_text, 
       1 - (embedding <=> $1::halfvec) AS similarity
FROM embeddings
WHERE area = 'RRHH'  -- ← Partition pruning aquí
ORDER BY embedding <=> $1::halfvec
LIMIT 10;

-- Output del EXPLAIN mostrará:
-- "Partition Pruning: RRHH"
-- Solo escanea embeddings_rrhh (37M vectores)
-- Ignora las otras 5 particiones (207M vectores)
```

### 7.4 Estimación de Tamaño por Partición

Basado en la distribución estimada del corpus documental:

| Área | % Docs | Vectores | $S_{table}$ | $S_{index}$ | RAM (20% hot) | Uso típico |
|:-----|:------:|:--------:|:-----------:|:-----------:|:-------------:|:-----------|
| **RRHH** | 15% | ~37 M | ~56 GB | ~62 GB | ~12 GB | Políticas, manuales empleado |
| **Call Center** | 25% | ~61 M | ~93 GB | ~103 GB | ~21 GB | KB, scripts, procedimientos |
| **Legal** | 10% | ~24 M | ~37 GB | ~41 GB | ~8 GB | Contratos, normativas |
| **Operaciones** | 20% | ~49 M | ~75 GB | ~83 GB | ~17 GB | Procesos, técnicos |
| **Finanzas** | 15% | ~37 M | ~56 GB | ~62 GB | ~12 GB | Reportes, políticas |
| **Otros** | 15% | ~36 M | ~55 GB | ~61 GB | ~12 GB | Misceláneos |
| **TOTAL** | 100% | **~244 M** | **~372 GB** | **~412 GB** | **~82 GB** | — |

> 💡 **Nota:** Con halfvec(768) + particionamiento, el tamaño total es ~784 GB de disco (mucho menor que los ~3 TB baseline).

### 7.5 Consideraciones para Queries Cross-Área

Cuando un usuario necesita buscar en múltiples áreas:

```sql
-- Opción 1: Query directa (PostgreSQL escanea particiones necesarias)
SELECT * FROM embeddings
WHERE area IN ('RRHH', 'LEGAL')  -- Escanea 2 particiones
ORDER BY embedding <=> $1::halfvec
LIMIT 10;

-- Opción 2: UNION ALL con límites por partición (más eficiente para top-K)
WITH ranked AS (
    SELECT *, 
           ROW_NUMBER() OVER (PARTITION BY area ORDER BY embedding <=> $1) as rn
    FROM embeddings
    WHERE area IN ('RRHH', 'LEGAL')
)
SELECT * FROM ranked WHERE rn <= 20  -- 20 por área
ORDER BY embedding <=> $1::halfvec
LIMIT 10;

-- Opción 3: Federated search desde aplicación
-- (ejecutar queries paralelas y fusionar en código Python)
```

| Patrón de consulta | Recomendación |
|:-------------------|:--------------|
| 80%+ queries son single-area | ✅ Particionamiento altamente recomendado |
| 50-80% queries son single-area | ✅ Particionamiento recomendado |
| <50% queries son single-area | ⚠️ Evaluar cuidadosamente |

---

## Capítulo 8: Cacheo Semántico

### 8.1 Arquitectura Multi-Nivel

> **¿Por qué cache "semántico"?**
> 
> El cache tradicional requiere coincidencia **exacta** de la query.
> El cache semántico reconoce queries **semánticamente similares**.
> 
> | Query | Cache Tradicional | Cache Semántico |
> |:------|:-----------------:|:---------------:|
> | "¿Cuál es la política de vacaciones?" | ✅ Hit | ✅ Hit |
> | "Política de vacaciones" | ❌ Miss | ✅ Hit (similar) |
> | "¿Cuántos días libres tengo?" | ❌ Miss | ✅ Hit (similar) |
> | "Dime sobre los días de descanso" | ❌ Miss | ✅ Hit (similar) |

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ARQUITECTURA DE CACHE MULTI-NIVEL                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐                                                        │
│  │   Query Usuario  │  "¿Cuál es la política de vacaciones?"                │
│  └────────┬─────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    NIVEL 1: EXACT MATCH CACHE                          │ │
│  │                                                                         │ │
│  │  Key: hash(query)                                                       │ │
│  │  Backend: Redis String                                                  │ │
│  │  Latencia: ~1-3 ms                                                      │ │
│  │  Hit Rate esperado: ~30%                                                │ │
│  │                                                                         │ │
│  │  ┌─ HIT ─────────────────────────────────────────────────────────────┐ │ │
│  │  │ Retornar respuesta cacheada inmediatamente                         │ │ │
│  │  └────────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│           │ MISS                                                             │
│           ▼                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    NIVEL 2: SEMANTIC CACHE                              │ │
│  │                                                                         │ │
│  │  1. Generar embedding de la query                                       │ │
│  │  2. Buscar queries similares en cache (similitud > 0.95)                │ │
│  │  Backend: Redis Vector Search (RediSearch)                              │ │
│  │  Latencia: ~10-20 ms                                                    │ │
│  │  Hit Rate esperado: ~40%                                                │ │
│  │                                                                         │ │
│  │  ┌─ HIT (similitud > 0.95) ──────────────────────────────────────────┐ │ │
│  │  │ Retornar respuesta de query similar                                │ │ │
│  │  └────────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│           │ MISS                                                             │
│           ▼                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    NIVEL 3: EMBEDDING CACHE                             │ │
│  │                                                                         │ │
│  │  Reutilizar embedding de query para evitar llamada a API               │ │
│  │  (ya lo generamos en Nivel 2)                                          │ │
│  │  Ahorro: ~$0.0001/query × 10K queries/día = ~$30/mes                   │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│           │                                                                  │
│           ▼                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    NIVEL 4: FULL RAG PIPELINE                           │ │
│  │                                                                         │ │
│  │  1. Buscar en pgvector (~25ms)                                          │ │
│  │  2. Reranking con Cohere (~80ms)                                        │ │
│  │  3. Generar respuesta con Gemini (~1500ms)                              │ │
│  │  4. ⬇️ Guardar en cache (Nivel 1 + Nivel 2)                             │ │
│  │                                                                         │ │
│  │  Latencia total: ~1,600 ms                                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  RESULTADO                                                                   │
│  ─────────                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Hit Rate Combinado: 30% (L1) + 40% (L2) = ~67% de queries cacheadas    │ │
│  │ Latencia Promedio: 0.67 × 15ms + 0.33 × 1600ms = ~538 ms               │ │
│  │ Ahorro en LLM: ~67% menos llamadas = ~$500-800/mes                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Implementación con Redis

#### Configuración de Redis para Vector Search

```python
import redis
import numpy as np
from redis.commands.search.field import TextField, VectorField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from typing import Optional
import hashlib

class SemanticCache:
    """
    Cache semántico multi-nivel con Redis.
    Implementa exact match + similarity search.
    """
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        embedding_dim: int = 768,
        similarity_threshold: float = 0.95,
        ttl_seconds: int = 86400,  # 24 horas
    ):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=False)
        self.embedding_dim = embedding_dim
        self.similarity_threshold = similarity_threshold
        self.ttl = ttl_seconds
        self.index_name = "semantic_cache_idx"
        
        self._create_index()
    
    def _create_index(self):
        """Crea índice de búsqueda vectorial en Redis."""
        try:
            # Verificar si el índice ya existe
            self.redis.ft(self.index_name).info()
        except:
            # Crear índice
            schema = (
                TextField("query"),
                TextField("response"),
                TagField("area"),
                VectorField(
                    "embedding",
                    "HNSW",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": self.embedding_dim,
                        "DISTANCE_METRIC": "COSINE",
                    }
                )
            )
            
            definition = IndexDefinition(
                prefix=["cache:"],
                index_type=IndexType.HASH
            )
            
            self.redis.ft(self.index_name).create_index(
                fields=schema,
                definition=definition
            )
    
    def _hash_query(self, query: str) -> str:
        """Genera hash determinístico de la query."""
        return hashlib.sha256(query.lower().strip().encode()).hexdigest()[:16]
    
    def get(self, query: str, query_embedding: np.ndarray, area: str = None) -> Optional[dict]:
        """
        Busca en cache: primero exact match, luego semantic.
        
        Returns:
            dict con 'response', 'source' (exact/semantic), 'similarity'
            None si no hay hit
        """
        query_hash = self._hash_query(query)
        
        # Nivel 1: Exact match
        exact_key = f"exact:{query_hash}"
        cached = self.redis.get(exact_key)
        if cached:
            return {
                "response": cached.decode(),
                "source": "exact",
                "similarity": 1.0
            }
        
        # Nivel 2: Semantic search
        vector_bytes = query_embedding.astype(np.float32).tobytes()
        
        q = (
            Query(f"*=>[KNN 1 @embedding $vec AS score]")
            .return_fields("query", "response", "score")
            .dialect(2)
        )
        
        if area:
            q = Query(f"@area:{{{area}}}=>[KNN 1 @embedding $vec AS score]")
        
        results = self.redis.ft(self.index_name).search(
            q,
            query_params={"vec": vector_bytes}
        )
        
        if results.docs:
            doc = results.docs[0]
            similarity = 1 - float(doc.score)  # Cosine distance → similarity
            
            if similarity >= self.similarity_threshold:
                return {
                    "response": doc.response,
                    "source": "semantic",
                    "similarity": similarity,
                    "original_query": doc.query
                }
        
        return None
    
    def set(
        self,
        query: str,
        response: str,
        query_embedding: np.ndarray,
        area: str = "general"
    ):
        """Guarda query/response en ambos niveles de cache."""
        query_hash = self._hash_query(query)
        
        # Nivel 1: Exact match (string simple)
        exact_key = f"exact:{query_hash}"
        self.redis.setex(exact_key, self.ttl, response)
        
        # Nivel 2: Semantic cache (hash con vector)
        semantic_key = f"cache:{query_hash}"
        vector_bytes = query_embedding.astype(np.float32).tobytes()
        
        self.redis.hset(
            semantic_key,
            mapping={
                "query": query,
                "response": response,
                "area": area,
                "embedding": vector_bytes
            }
        )
        self.redis.expire(semantic_key, self.ttl)
    
    def invalidate_by_area(self, area: str):
        """Invalida todas las entradas de un área (ej: cuando cambian documentos)."""
        # Buscar todas las keys del área
        q = Query(f"@area:{{{area}}}").return_fields("query")
        results = self.redis.ft(self.index_name).search(q)
        
        for doc in results.docs:
            self.redis.delete(doc.id)
            query_hash = self._hash_query(doc.query)
            self.redis.delete(f"exact:{query_hash}")
```

#### Uso del Cache en el Pipeline RAG

```python
from semantic_cache import SemanticCache
from embedding_pipeline import OptimizedEmbeddingPipeline

class RAGPipeline:
    def __init__(self):
        self.cache = SemanticCache(
            redis_host="redis.internal",
            similarity_threshold=0.95,
            ttl_seconds=86400  # 24 horas
        )
        self.embedder = OptimizedEmbeddingPipeline(dimension=768)
    
    def query(self, user_query: str, area: str = None) -> dict:
        # Paso 1: Generar embedding de la query
        query_embedding = self.embedder.embed([user_query])[0]
        
        # Paso 2: Buscar en cache
        cached = self.cache.get(user_query, query_embedding, area)
        if cached:
            return {
                "response": cached["response"],
                "cached": True,
                "cache_source": cached["source"],
                "similarity": cached.get("similarity", 1.0)
            }
        
        # Paso 3: Cache miss → ejecutar RAG completo
        response = self._full_rag_pipeline(user_query, query_embedding, area)
        
        # Paso 4: Guardar en cache
        self.cache.set(user_query, response, query_embedding, area or "general")
        
        return {
            "response": response,
            "cached": False
        }
    
    def _full_rag_pipeline(self, query: str, embedding: np.ndarray, area: str) -> str:
        # 1. Vector search en pgvector
        # 2. Reranking con Cohere
        # 3. Generación con Gemini
        # ... implementación completa
        pass
```

---

### 8.3 Políticas de Eviction

| Política | Descripción | Configuración Redis | Cuándo usar |
|:---------|:------------|:--------------------|:------------|
| **TTL (Time To Live)** | Expira después de N segundos | `EXPIRE key 86400` | Datos que cambian frecuentemente |
| **LRU (Least Recently Used)** | Elimina los menos usados recientemente | `maxmemory-policy allkeys-lru` | Memoria limitada |
| **LFU (Least Frequently Used)** | Elimina los menos usados en total | `maxmemory-policy allkeys-lfu` | Patrones estables de uso |
| **TTL + LRU** | Combina ambas estrategias | TTL por key + LRU global | ⭐ **Recomendado** |

#### Configuración Redis Recomendada

```conf
# redis.conf para cache semántico

# Memoria máxima para cache (8 GB)
maxmemory 8gb

# Política de eviction: LRU cuando se llena
maxmemory-policy allkeys-lru

# Samples para LRU (más = más preciso, más lento)
maxmemory-samples 10

# Módulo de búsqueda vectorial
loadmodule /path/to/redisearch.so
```

---

### 8.4 Impacto Teórico en Latencia

| Escenario | Sin Cache | Con Cache L1+L2 | Mejora |
|:----------|:---------:|:---------------:|:------:|
| **Latencia P50** | ~1,400 ms | ~15 ms | **-99%** |
| **Latencia P95 (cache hit)** | — | ~25 ms | — |
| **Latencia P95 (cache miss)** | ~2,200 ms | ~2,200 ms | Sin cambio |
| **Latencia promedio** | ~1,600 ms | ~538 ms | **-67%** |
| **Hit Rate esperado** | — | ~67% | — |

#### Impacto en Costos de API

| Métrica | Sin Cache | Con Cache | Ahorro |
|:--------|:---------:|:---------:|:------:|
| **Llamadas LLM/día** | ~10,000 | ~3,300 | -67% |
| **Costo LLM/mes** | ~$800 | ~$264 | **-$536** |
| **Llamadas Embedding/día** | ~10,000 | ~3,300 | -67% |
| **Costo Embedding/mes** | ~$300 | ~$99 | **-$201** |
| **Total ahorro/mes** | — | — | **~$737** |

> 💡 **Nota:** El cache semántico es una de las optimizaciones con **mejor ROI** porque reduce costos recurrentes de APIs sin impactar la calidad de las respuestas.

---
---

# SECCIÓN IV: TÉCNICAS AVANZADAS DE RAG

Esta sección presenta las técnicas más actualizadas (2024-2025) para cada etapa del pipeline RAG, explicando cuándo y por qué aplicar cada una según la naturaleza de los documentos.

---

## Capítulo 9: Estrategias de Chunking

El chunking determina cómo se fragmenta el texto antes de vectorizarlo. La elección correcta depende de la **naturaleza de los documentos** y tiene impacto directo en la calidad del retrieval y los costos.

### 9.1 Comparativa de Técnicas de Chunking

| Técnica | Descripción | Complejidad | Cuándo Usar |
|:--------|:------------|:-----------:|:------------|
| **Fixed Size** | Cortar cada N caracteres/tokens | Baja | Baseline, documentos homogéneos |
| **Recursive** | Separadores jerárquicos (párrafo → oración → palabra) | Media | ⭐ **Recomendado general** |
| **Sentence** | Una o más oraciones por chunk | Media | Documentos narrativos |
| **Semantic** | Detectar cambios de tema con embeddings | Alta | Máxima calidad, documentos complejos |
| **Agentic** | LLM decide cómo segmentar | Muy Alta | Documentos muy heterogéneos |
| **Late Chunking** | Embeber primero, chunkear después | Alta | Documentos largos con contexto global |
| **Contextual** | Agregar resumen/contexto a cada chunk | Alta | Reducir fallos de retrieval |
| **Parent Document** | Chunks pequeños para buscar, doc grande para generar | Media | Balance precisión/contexto |

---

### 9.2 Chunking Semántico

> **¿Qué es?** Usa embeddings para detectar "cambios de tema" en el texto y cortar en esos puntos naturales de transición semántica.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHUNKING SEMÁNTICO                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Documento:                                                      │
│  "La política de vacaciones establece... (tema A)                │
│   Los empleados pueden solicitar... (tema A)                     │
│   En cuanto a las licencias médicas... (tema B) ← CAMBIO        │
│   El procedimiento para licencias... (tema B)"                   │
│                                                                  │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Calcular embeddings de cada oración                       │   │
│  │ Detectar donde similitud_coseno(sent_i, sent_i+1) < umbral│   │
│  └──────────────────────────────────────────────────────────┘   │
│           │                                                      │
│           ▼                                                      │
│  Chunk 1: "La política de vacaciones... pueden solicitar..."    │
│  Chunk 2: "En cuanto a las licencias médicas... procedimiento..."│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Implementación

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_google_vertexai import VertexAIEmbeddings

# Configurar chunker semántico con Gemini
embeddings = VertexAIEmbeddings(model_name="text-embedding-004")

splitter = SemanticChunker(
    embeddings=embeddings,
    breakpoint_threshold_type="percentile",  # o "standard_deviation", "interquartile"
    breakpoint_threshold_amount=95  # Umbral de corte (percentil 95)
)

# Aplicar chunking
chunks = splitter.split_text(document_text)
print(f"Generados {len(chunks)} chunks semánticos")
```

#### Dependencias e Impacto

| Depende de... | Impacto |
|:--------------|:--------|
| **Coherencia del documento** | Funciona mejor en textos bien estructurados |
| **Modelo de embeddings** | Modelos más grandes detectan mejor los cambios |
| **Umbral de corte** | Umbral alto = chunks grandes, bajo = chunks pequeños |

**Cuándo usarlo:**
- ✅ Documentos técnicos con secciones claras
- ✅ Cuando la calidad es prioritaria sobre el costo
- ❌ NO usar en documentos muy cortos o conversacionales

---

### 9.3 Agentic Chunking

> **¿Qué es?** Un LLM analiza el documento y decide cómo segmentarlo, como lo haría un humano experto al organizar información.

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENTIC CHUNKING                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Documento complejo ─────────┐                                   │
│  (contrato legal mixto)      │                                   │
│                              ▼                                   │
│                    ┌──────────────────┐                          │
│                    │       LLM        │                          │
│                    │  (Gemini/GPT-4)  │                          │
│                    │                  │                          │
│                    │ "Analiza este    │                          │
│                    │  documento y     │                          │
│                    │  divídelo en     │                          │
│                    │  secciones       │                          │
│                    │  lógicas..."     │                          │
│                    └────────┬─────────┘                          │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Chunk 1: "Definiciones y partes del contrato"               ││
│  │ Chunk 2: "Obligaciones del empleador"                       ││
│  │ Chunk 3: "Obligaciones del empleado"                        ││
│  │ Chunk 4: "Cláusulas de confidencialidad"                    ││
│  │ Chunk 5: "Términos de terminación"                          ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Implementación

```python
import json
from vertexai.generative_models import GenerativeModel

def agentic_chunk(document: str, max_chunks: int = 20) -> list[dict]:
    """
    Usa un LLM para segmentar inteligentemente un documento.
    Retorna chunks con metadata sobre el tema de cada uno.
    """
    model = GenerativeModel("gemini-1.5-pro")
    
    prompt = f"""
    Analiza el siguiente documento y divídelo en secciones lógicas.
    
    Reglas:
    1. Cada sección debe tratar UN solo tema coherente
    2. Cada sección debe ser autocontenida (comprensible sin el resto)
    3. Máximo {max_chunks} secciones
    4. Incluye un título descriptivo para cada sección
    
    Responde en JSON con este formato:
    [
        {{"titulo": "...", "contenido": "...", "tema_principal": "..."}},
        ...
    ]
    
    Documento:
    {document[:50000]}  # Limitar a 50K chars
    """
    
    response = model.generate_content(prompt)
    
    # Parsear JSON de la respuesta
    try:
        chunks = json.loads(response.text)
        return chunks
    except json.JSONDecodeError:
        # Fallback: retornar documento completo
        return [{"titulo": "Documento", "contenido": document, "tema_principal": "general"}]

# Uso
chunks = agentic_chunk(contract_text)
for chunk in chunks:
    print(f"[{chunk['tema_principal']}] {chunk['titulo'][:50]}...")
```

#### Dependencias e Impacto

| Depende de... | Impacto |
|:--------------|:--------|
| **Calidad del LLM** | Modelos más capaces producen mejor segmentación |
| **Costo** | Cada documento requiere una llamada al LLM (~$0.01-0.10/doc) |
| **Latencia de ingestión** | Significativamente más lenta (2-10s/documento) |

**Cuándo usarlo:**
- ✅ Documentos muy heterogéneos (contratos, informes mixtos)
- ✅ Ingestión batch donde latencia no importa
- ❌ NO usar para millones de documentos (muy costoso)

---

### 9.4 Late Chunking

> **¿Qué es?** En lugar de chunkear y luego embeber, primero se procesa el documento completo con un modelo de contexto largo, preservando la información global en cada chunk.

```
┌─────────────────────────────────────────────────────────────────┐
│                      LATE CHUNKING                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MÉTODO TRADICIONAL:                                             │
│  ────────────────────                                            │
│  Documento ──→ [Chunk1, Chunk2, Chunk3] ──→ [Emb1, Emb2, Emb3]   │
│                    (chunking primero)      (embeddings después)  │
│                                                                  │
│      ⚠️ Problema: Cada chunk pierde el contexto del documento   │
│                                                                  │
│  LATE CHUNKING:                                                  │
│  ──────────────                                                  │
│  Documento ──→ Encoder (contexto largo) ──→ [Token embeddings]   │
│                      (8K-32K tokens)         (por cada token)    │
│                            │                                     │
│                            ▼                                     │
│               Pooling por regiones del texto                     │
│                            │                                     │
│                            ▼                                     │
│            [Emb1+contexto, Emb2+contexto, Emb3+contexto]         │
│                                                                  │
│      ✅ Beneficio: Cada chunk "sabe" del documento completo      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Dependencias e Impacto

| Depende de... | Impacto |
|:--------------|:--------|
| **Longitud del documento** | Ideal para documentos >8K tokens |
| **Modelo de embeddings** | Requiere modelos con contexto largo (Jina-v3, etc.) |
| **RAM disponible** | Procesar documentos largos consume más memoria |

**Cuándo usarlo:**
- ✅ Documentos largos donde el contexto global importa (informes, papers)
- ✅ Cuando un chunk puede perder significado sin el resto
- ❌ NO usar para documentos cortos (overhead innecesario)

---

### 9.5 Parent Document Retriever

> **¿Qué es?** Usa chunks pequeños para la búsqueda (más precisa), pero devuelve el documento padre (más contexto) para la generación.

```
┌─────────────────────────────────────────────────────────────────┐
│                   PARENT DOCUMENT RETRIEVER                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INGESTIÓN:                                                      │
│  ──────────                                                      │
│                                                                  │
│  Documento completo (10 páginas, 15K tokens)                     │
│       │                                                          │
│       ├──→ Guardar en Document Store (GCS)                       │
│       │         doc_id: "DOC001"                                 │
│       │                                                          │
│       └──→ Crear chunks pequeños para búsqueda:                  │
│             ├── Chunk 1 (500 tok) → embedding → pgvector         │
│             │   metadata: {parent_id: "DOC001", position: 0}     │
│             ├── Chunk 2 (500 tok) → embedding → pgvector         │
│             │   metadata: {parent_id: "DOC001", position: 1}     │
│             └── Chunk 3 (500 tok) → embedding → pgvector         │
│                 metadata: {parent_id: "DOC001", position: 2}     │
│                                                                  │
│  BÚSQUEDA:                                                       │
│  ─────────                                                       │
│                                                                  │
│  Query: "política de licencias"                                  │
│       │                                                          │
│       ▼                                                          │
│  Vector Search ──→ Match: Chunk 2 (score: 0.92)                  │
│       │                                                          │
│       ▼                                                          │
│  Recuperar parent_id: "DOC001"                                   │
│       │                                                          │
│       ▼                                                          │
│  Cargar documento completo desde GCS                             │
│       │                                                          │
│       ▼                                                          │
│  Enviar documento completo (15K tok) al LLM                      │
│                                                                  │
│  ✅ Beneficio: Búsqueda precisa + Contexto completo              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Dependencias e Impacto

| Depende de... | Impacto |
|:--------------|:--------|
| **Ventana de contexto del LLM** | Documentos padres deben caber en el contexto |
| **Precisión vs. contexto** | Chunks más pequeños = mejor match, docs padres = mejor respuesta |
| **Almacenamiento** | Requiere guardar chunks + referencias a padres |

**Cuándo usarlo:**
- ✅ Cuando la precisión de búsqueda Y el contexto son importantes
- ✅ Documentos con estructura jerárquica (manuales, libros)
- ❌ NO usar si los documentos son muy cortos

---

### 9.6 Matriz de Decisión: ¿Qué Chunking Usar?

| Tipo de Documento | Estrategia Recomendada | Tamaño Chunk | Overlap |
|:------------------|:----------------------:|:------------:|:-------:|
| **FAQs, Q&A** | Fixed/Sentence | 256-512 tokens | 0% |
| **Emails, tickets** | Sentence | 128-256 tokens | 10% |
| **Manuales técnicos** | Recursive | 512-1024 tokens | 15% |
| **Políticas, normativas** | Semantic | 512-1024 tokens | 20% |
| **Contratos legales** | Agentic + Parent | 256 (child) / Full (parent) | 25% |
| **Informes largos** | Late Chunking | 1024-2048 tokens | 15% |
| **Papers científicos** | Semantic + Contextual | 512-1024 tokens | 20% |
| **Presentaciones (PPT)** | Page-based | 1 slide | 0% |
| **Documentos mixtos** | Agentic | Variable | Variable |

---

### 9.7 Impacto del Overlap en Costos

El overlap (solapamiento entre chunks) mejora el contexto pero aumenta el número de vectores:

| Overlap | Factor de Vectores | Vectores (17 TB) | Impacto en Costo |
|:-------:|:------------------:|:----------------:|:----------------:|
| **0%** | 1.00x | ~220 M | Baseline |
| **10%** | 1.11x | ~244 M | +11% almacenamiento |
| **15%** | 1.18x | ~260 M | +18% almacenamiento |
| **20%** | 1.25x | ~275 M | +25% almacenamiento |
| **25%** | 1.33x | ~293 M | +33% almacenamiento |
| **50%** | 2.00x | ~440 M | ⚠️ +100% almacenamiento |

> 💡 **Recomendación:** Usar **10-15% overlap** como default. Solo aumentar a 20-25% para documentos donde el contexto entre chunks es crítico (legal, técnico).

---

## Capítulo 10: Modelos de Embedding

La elección del modelo de embedding impacta directamente en la calidad de búsqueda, costos y latencia.

### 10.1 Comparativa de Modelos 2024-2025

| Modelo | Proveedor | Dimensión | Multilingüe | Matryoshka | Contexto | Costo | Cuándo Usar |
|:-------|:----------|:---------:|:-----------:|:----------:|:--------:|:-----:|:------------|
| **Gemini text-embedding-004** | Google | 768-3072 | ✅ | ✅ | 2K | $ | ⭐ Ecosistema GCP |
| OpenAI text-embedding-3-large | OpenAI | 3072 | ✅ | ✅ | 8K | $$ | Máxima calidad |
| OpenAI text-embedding-3-small | OpenAI | 1536 | ✅ | ✅ | 8K | $ | Balance costo/calidad |
| **Cohere embed-v3** | Cohere | 1024 | ✅ 100+ | ✅ | 512 | $ | ⭐ Multilingüe |
| Voyage AI voyage-3 | Voyage | 1024 | ✅ | ✅ | 32K | $$ | Contexto muy largo |
| BGE-M3 | BAAI | 1024 | ✅ 100+ | ❌ | 8K | Gratis | Open source |
| E5-mistral-7b-instruct | Intfloat | 4096 | ✅ | ❌ | 32K | Gratis | Local, alta calidad |
| NV-Embed-v2 | NVIDIA | 4096 | ✅ | ✅ | 32K | Gratis | GPU local |
| Jina-embeddings-v3 | Jina AI | 1024 | ✅ | ✅ | 8K | $ | Late chunking |

#### MTEB Leaderboard (Referencia)

> El [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) es el benchmark estándar para comparar modelos de embeddings. Los modelos listados arriba están entre los top performers.

---

### 10.2 Tipos de Interacción en Embeddings

| Tipo | Descripción | Ejemplos | Trade-off |
|:-----|:------------|:---------|:----------|
| **Bi-Encoder** | Query y Doc se embeben por separado | OpenAI, Cohere, Gemini, BGE | Rápido (~5ms), menos preciso |
| **Cross-Encoder** | Query + Doc se procesan juntos | Cohere Rerank, BGE-reranker | Lento (~100ms), muy preciso |
| **Late Interaction** | Tokens embebidos separados, comparación token-a-token | ColBERT, Jina-ColBERT | Balance velocidad/precisión |

```
┌─────────────────────────────────────────────────────────────────┐
│              COMPARACIÓN DE ARQUITECTURAS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  BI-ENCODER (single vector):                                     │
│  ───────────────────────────                                     │
│  Query ──→ [Encoder] ──→ [1 vector] ←──cosine──→ [1 vector]     │
│  Doc   ──→ [Encoder] ──→ [1 vector]              (precomputado) │
│                                                                  │
│  ✅ Rápido: O(1) comparación                                     │
│  ❌ Menos preciso para queries complejas                         │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  CROSS-ENCODER (attention jointly):                              │
│  ──────────────────────────────────                              │
│  [Query + Doc] ──→ [Transformer completo] ──→ Relevance Score    │
│                                                                  │
│  ✅ Muy preciso: considera interacciones query-doc               │
│  ❌ Lento: no se puede precomputar                               │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  LATE INTERACTION (multi-vector):                                │
│  ─────────────────────────────────                               │
│  Query ──→ [n vectores] ←──MaxSim──→ [m vectores] ← Doc         │
│            (por token)               (por token)                 │
│                                                                  │
│  ✅ Balance: más preciso que bi-encoder, más rápido que cross    │
│  ❌ Más almacenamiento (~10-100x más vectores)                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 10.3 ColBERT y Multi-Vector

> **¿Qué es ColBERT?** En lugar de un solo vector por documento, genera un vector por cada token. La similitud se calcula comparando todos los tokens de la query con todos los del documento usando MaxSim.

```
┌─────────────────────────────────────────────────────────────────┐
│                        ColBERT / MaxSim                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Query: "política vacaciones"                                    │
│         ↓                                                        │
│  Query Tokens: ["política", "vacaciones"]                        │
│         ↓                                                        │
│  Query Embeddings: [v_pol, v_vac]  (2 vectores)                  │
│                                                                  │
│  Document: "Los empleados tienen derecho a vacaciones anuales"   │
│         ↓                                                        │
│  Doc Tokens: ["empleados", "derecho", "vacaciones", "anuales"]   │
│         ↓                                                        │
│  Doc Embeddings: [v_emp, v_der, v_vac, v_anu]  (4 vectores)      │
│                                                                  │
│  MaxSim Score:                                                   │
│  ─────────────                                                   │
│  Para cada query token, encontrar el doc token más similar:      │
│                                                                  │
│  score = max_sim(v_pol, doc_vectors) + max_sim(v_vac, doc_vectors)│
│        = sim(v_pol, v_emp) + sim(v_vac, v_vac)                   │
│        = 0.3 + 1.0 = 1.3                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Dependencias e Impacto

| Depende de... | Impacto |
|:--------------|:--------|
| **Almacenamiento** | ~10-100x más espacio que bi-encoder (un vector por token) |
| **Latencia** | Más lento en búsqueda, pero reranking es rápido |
| **Precisión** | +5-15% vs. bi-encoder en tareas difíciles |

**Cuándo usarlo:**
- ✅ Cuando la precisión es crítica (legal, médico)
- ✅ Como segunda etapa después de bi-encoder
- ❌ NO usar como única etapa para millones de documentos

---

### 10.4 Matriz de Decisión: ¿Qué Modelo Usar?

| Escenario | Modelo Recomendado | Dimensión | Razón |
|:----------|:-------------------|:---------:|:------|
| **Producción en GCP** | Gemini text-embedding-004 | 768 | Integración nativa, Matryoshka |
| **Multilingüe crítico** | Cohere embed-v3 | 1024 | Mejor en español/otros idiomas |
| **On-premise/local** | BGE-M3 o E5-mistral | 1024+ | Open source, sin costos de API |
| **Máxima calidad** | OpenAI 3-large + Cohere Rerank | 1536 | SOTA actual en benchmarks |
| **Presupuesto limitado** | BGE-M3 + halfvec | 512 | Open source + compresión |
| **Documentos >8K tokens** | Voyage AI voyage-3 | 1024 | Contexto 32K nativo |
| **Precisión extrema** | ColBERT/Jina-ColBERT-v2 | Multi | Late interaction |

---

### 10.5 Recomendación para el Proyecto

Para el caso de **17 TB de documentación corporativa en español/inglés** con ecosistema GCP:

```
┌─────────────────────────────────────────────────────────────────┐
│                 CONFIGURACIÓN RECOMENDADA                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Modelo:        Gemini text-embedding-004                        │
│  Dimensión:     768 (Matryoshka truncation)                      │
│  Precisión:     halfvec (float16)                                │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  📊 MÉTRICAS RESULTANTES:                                        │
│                                                                  │
│  • Disco total:     ~1.1 TB (vs. 3.0 TB baseline)                │
│  • RAM requerida:   ~90 GB (vs. 240 GB baseline)                 │
│  • Calidad:         ~97.5% del recall baseline                   │
│  • Multilingüe:     ✅ Nativo (español, inglés, otros)           │
│  • Integración GCP: ✅ Directa (Vertex AI)                       │
│  • Costo embedding: ~$500-700/mes (ingestión completa)           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Capítulo 11: Técnicas de Búsqueda

La búsqueda vectorial básica puede mejorarse significativamente con técnicas adicionales que combinan múltiples señales.

### 11.1 Comparativa de Técnicas de Búsqueda

| Técnica | Descripción | Mejora Típica | Latencia Adicional | Complejidad |
|:--------|:------------|:-------------:|:------------------:|:-----------:|
| **Vector puro** | Solo similitud de embeddings | Baseline | 0 | Baja |
| **BM25 puro** | Solo keywords (sparse) | -20% vs. vector | ~5ms | Baja |
| **Hybrid (Vector + BM25)** | Combina ambos con RRF | +10-20% | ~10ms | Media |
| **Reranking** | Cross-encoder reordena top-K | +15-25% | ~100ms | Media |
| **HyDE** | LLM genera doc hipotético | +10-20% | ~500-2000ms | Alta |
| **Query Expansion** | LLM genera queries alternativos | +5-15% | ~200ms | Media |
| **Multi-Query** | Múltiples queries → unión | +10-15% | ~100ms | Media |

---

### 11.2 Búsqueda Híbrida (Hybrid Search)

> **¿Qué es?** Combina búsqueda por palabras clave (BM25/sparse) con búsqueda semántica (dense vectors) para obtener lo mejor de ambos mundos.

```
┌─────────────────────────────────────────────────────────────────┐
│                    BÚSQUEDA HÍBRIDA                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Query: "política de vacaciones 2024"                            │
│                          │                                       │
│          ┌───────────────┴───────────────┐                       │
│          ▼                               ▼                       │
│  ┌───────────────┐              ┌───────────────┐                │
│  │    BM25       │              │   Vector      │                │
│  │  (keywords)   │              │  (semántico)  │                │
│  │               │              │               │                │
│  │ "política"    │              │ embedding de  │                │
│  │ "vacaciones"  │              │ la query      │                │
│  │ "2024"        │              │               │                │
│  └───────┬───────┘              └───────┬───────┘                │
│          │                               │                       │
│          ▼                               ▼                       │
│  [Doc A: 0.8]                    [Doc C: 0.9]                    │
│  [Doc B: 0.6]                    [Doc A: 0.7]                    │
│  [Doc D: 0.5]                    [Doc B: 0.6]                    │
│          │                               │                       │
│          └───────────────┬───────────────┘                       │
│                          ▼                                       │
│          ┌───────────────────────────────┐                       │
│          │   Reciprocal Rank Fusion      │                       │
│          │           (RRF)               │                       │
│          │                               │                       │
│          │   score = Σ 1/(k + rank_i)    │                       │
│          │   donde k = 60 (constante)    │                       │
│          └───────────────┬───────────────┘                       │
│                          ▼                                       │
│          [Doc A: rank 1] ← Aparece en ambos (reforzado)          │
│          [Doc C: rank 2]                                         │
│          [Doc B: rank 3]                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Implementación en PostgreSQL

```sql
-- ============================================================
-- PREPARACIÓN: Crear índice GIN para BM25 (tsvector)
-- ============================================================
ALTER TABLE embeddings ADD COLUMN IF NOT EXISTS tsv tsvector 
    GENERATED ALWAYS AS (to_tsvector('spanish', chunk_text)) STORED;

CREATE INDEX IF NOT EXISTS idx_embeddings_tsv ON embeddings USING GIN(tsv);

-- ============================================================
-- QUERY HÍBRIDA CON RRF (Reciprocal Rank Fusion)
-- ============================================================
-- Input: $1 = query_embedding (vector), $2 = query_text (string)

WITH 
-- Búsqueda vectorial: top 30 por similitud coseno
vector_results AS (
    SELECT 
        id,
        doc_id,
        chunk_text,
        1 - (embedding <=> $1::halfvec) AS vector_score,
        ROW_NUMBER() OVER (ORDER BY embedding <=> $1::halfvec) AS vector_rank
    FROM embeddings
    WHERE area = $3  -- Partition pruning (opcional)
    ORDER BY embedding <=> $1::halfvec 
    LIMIT 30
),
-- Búsqueda BM25: top 30 por relevancia de keywords
bm25_results AS (
    SELECT 
        id,
        doc_id,
        chunk_text,
        ts_rank_cd(tsv, plainto_tsquery('spanish', $2)) AS bm25_score,
        ROW_NUMBER() OVER (ORDER BY ts_rank_cd(tsv, plainto_tsquery('spanish', $2)) DESC) AS bm25_rank
    FROM embeddings
    WHERE tsv @@ plainto_tsquery('spanish', $2)
      AND area = $3  -- Partition pruning (opcional)
    ORDER BY ts_rank_cd(tsv, plainto_tsquery('spanish', $2)) DESC 
    LIMIT 30
),
-- Combinar con RRF
combined AS (
    SELECT 
        COALESCE(v.id, b.id) AS id,
        COALESCE(v.doc_id, b.doc_id) AS doc_id,
        COALESCE(v.chunk_text, b.chunk_text) AS chunk_text,
        v.vector_score,
        b.bm25_score,
        -- RRF: k=60 es el valor estándar
        COALESCE(1.0 / (60 + v.vector_rank), 0) + 
        COALESCE(1.0 / (60 + b.bm25_rank), 0) AS rrf_score
    FROM vector_results v
    FULL OUTER JOIN bm25_results b ON v.id = b.id
)
SELECT 
    id,
    doc_id,
    chunk_text,
    vector_score,
    bm25_score,
    rrf_score
FROM combined
ORDER BY rrf_score DESC
LIMIT 20;
```

#### Dependencias e Impacto

| Depende de... | Impacto |
|:--------------|:--------|
| **Tipo de query** | Queries con términos técnicos se benefician más de BM25 |
| **Vocabulario del dominio** | Jerga específica requiere BM25 |
| **Constante k de RRF** | Ajustar k (default 60) según resultados |

**Cuándo usarlo:**
- ✅ **Siempre como default en producción**
- ✅ Cuando hay términos técnicos o nombres propios
- ✅ Cuando el recall es importante

---

### 11.3 Reranking con Cross-Encoder

> **¿Qué es?** Después de recuperar top-K documentos con búsqueda rápida (bi-encoder), un modelo más preciso (pero lento) los reordena analizando query+doc juntos.

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE CON RERANKING                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Query: "¿Cuántos días de vacaciones tengo?"                     │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────┐                                             │
│  │ Hybrid Search   │  (~25ms)                                    │
│  │ (Vector + BM25) │                                             │
│  │                 │                                             │
│  │ Recall alto,    │                                             │
│  │ precisión media │                                             │
│  └────────┬────────┘                                             │
│           │                                                      │
│           ▼                                                      │
│  Top 50 documentos candidatos                                    │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                             │
│  │ Cross-Encoder   │  (~100ms)                                   │
│  │    Reranker     │                                             │
│  │                 │                                             │
│  │ (Cohere, BGE,   │                                             │
│  │  Jina, etc.)    │                                             │
│  │                 │                                             │
│  │ Precisión alta  │                                             │
│  └────────┬────────┘                                             │
│           │                                                      │
│           ▼                                                      │
│  Top 10 documentos rerankeados                                   │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                             │
│  │  LLM Generation │  (~1500ms)                                  │
│  └─────────────────┘                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Modelos de Reranking

| Modelo | Tipo | Latencia (50 docs) | Calidad | Costo |
|:-------|:-----|:------------------:|:-------:|:-----:|
| **Cohere Rerank 3** | API | ~100ms | ⭐⭐⭐⭐⭐ | $0.001/search |
| BGE-reranker-v2-m3 | Local | ~150ms | ⭐⭐⭐⭐ | Gratis (GPU) |
| Jina Reranker v2 | API/Local | ~80ms | ⭐⭐⭐⭐ | $ |
| GPT-4 as reranker | API | ~500ms | ⭐⭐⭐⭐⭐ | $$$$ |
| Gemini as reranker | API | ~400ms | ⭐⭐⭐⭐ | $$ |

#### Implementación con Cohere

```python
import cohere
from typing import List, Dict

class CohereReranker:
    """Reranker usando Cohere API."""
    
    def __init__(self, api_key: str):
        self.client = cohere.Client(api_key=api_key)
        self.model = "rerank-multilingual-v3.0"  # Mejor para español
    
    def rerank(
        self, 
        query: str, 
        documents: List[str], 
        top_n: int = 10,
        return_documents: bool = True
    ) -> List[Dict]:
        """
        Reordena documentos por relevancia a la query.
        
        Args:
            query: Query del usuario
            documents: Lista de textos a reordenar
            top_n: Número de resultados a retornar
            return_documents: Si incluir el texto en la respuesta
            
        Returns:
            Lista de dicts con {index, relevance_score, text?}
        """
        response = self.client.rerank(
            model=self.model,
            query=query,
            documents=documents,
            top_n=top_n,
            return_documents=return_documents
        )
        
        return [
            {
                "index": result.index,
                "relevance_score": result.relevance_score,
                "text": documents[result.index] if return_documents else None
            }
            for result in response.results
        ]

# Uso en el pipeline
reranker = CohereReranker(api_key="...")

# Después de hybrid search
candidates = hybrid_search(query, top_k=50)
candidate_texts = [doc["chunk_text"] for doc in candidates]

# Reranking
reranked = reranker.rerank(query, candidate_texts, top_n=10)

# Reordenar candidatos según reranking
final_docs = [candidates[r["index"]] for r in reranked]
```

#### Cuándo usar Reranking

- ✅ Siempre que la latencia lo permita (+100ms disponibles)
- ✅ Cuando la precisión es más importante que la velocidad
- ✅ Para áreas críticas (Legal, Finanzas)
- ❌ NO usar para autocompletado (<50ms total)
- ❌ NO usar para Call Center (velocidad prioritaria)

---

### 11.4 HyDE (Hypothetical Document Embeddings)

> **¿Qué es?** En lugar de embeber la query directamente, un LLM genera un "documento hipotético" que respondería la pregunta, y se embede ESE documento.

```
┌─────────────────────────────────────────────────────────────────┐
│                          HyDE                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MÉTODO TRADICIONAL:                                             │
│  ───────────────────                                             │
│  Query ──────────────────────────────────────→ Embedding → Search│
│  "¿Cuántos días de vacaciones tengo?"                            │
│                                                                  │
│  ⚠️ Problema: El embedding de una pregunta es diferente al      │
│               embedding de un documento que la responde          │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  MÉTODO HyDE:                                                    │
│  ────────────                                                    │
│  Query ──→ LLM genera ──→ Doc Hipotético ──→ Embedding ──→ Search│
│            respuesta                                             │
│                                                                  │
│  Query: "¿Cuántos días de vacaciones tengo?"                     │
│                    │                                             │
│                    ▼                                             │
│          ┌─────────────────┐                                     │
│          │       LLM       │                                     │
│          │   (Gemini Pro)  │                                     │
│          └────────┬────────┘                                     │
│                   │                                              │
│                   ▼                                              │
│  Doc Hipotético:                                                 │
│  "Los empleados con más de un año de antigüedad tienen          │
│   derecho a 15 días hábiles de vacaciones anuales,               │
│   incrementándose en 2 días adicionales por cada 5 años          │
│   de servicio. Las vacaciones deben solicitarse con              │
│   al menos 15 días de anticipación..."                           │
│                   │                                              │
│                   ▼                                              │
│          [Embedding del doc hipotético]                          │
│                   │                                              │
│                   ▼ (más similar a docs reales!)                 │
│             Vector Search                                        │
│                                                                  │
│  ✅ Beneficio: El embedding es más similar a documentos reales   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Cuándo usar HyDE

- ✅ Queries vagas o mal formuladas por usuarios no expertos
- ✅ Cuando el gap semántico query→documento es grande
- ✅ Procesamiento batch donde latencia no es crítica
- ❌ NO usar en tiempo real (añade ~500ms-2s)
- ❌ NO usar si queries son claras y específicas

---

### 11.5 Multi-Query Retrieval

> **¿Qué es?** Genera múltiples variantes de la query (usando LLM) y busca con todas, luego combina resultados con RRF.

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-QUERY RETRIEVAL                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Query original: "política de vacaciones"                        │
│                          │                                       │
│                          ▼                                       │
│                  ┌───────────────┐                               │
│                  │      LLM      │                               │
│                  │   (Gemini)    │                               │
│                  │               │                               │
│                  │ "Genera 4     │                               │
│                  │  variantes    │                               │
│                  │  de esta      │                               │
│                  │  query..."    │                               │
│                  └───────┬───────┘                               │
│                          │                                       │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Query 1: "política de vacaciones"                          │  │
│  │ Query 2: "días libres empleados"                           │  │
│  │ Query 3: "derecho a descanso anual"                        │  │
│  │ Query 4: "licencia por vacaciones"                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                       │
│                          ▼                                       │
│          Búsqueda paralela con las 4 queries                     │
│                          │                                       │
│          ┌───────────────┼───────────────┐                       │
│          ▼               ▼               ▼                       │
│       [Docs Q1]       [Docs Q2]       [Docs Q3]                  │
│                          │                                       │
│                          ▼                                       │
│              Unión + RRF (Reciprocal Rank Fusion)                │
│                          │                                       │
│                          ▼                                       │
│                  Top 10 documentos                               │
│          (mejor recall por diversidad de queries)                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Cuándo usar Multi-Query

- ✅ Queries de usuarios no expertos
- ✅ Cuando el recall es prioritario sobre latencia
- ✅ Queries ambiguas que pueden interpretarse de varias formas
- ❌ NO usar si queries son muy específicas (ya están claras)

---

### 11.6 Pipeline Recomendado

Basado en el análisis de 17 TB de documentación corporativa:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PIPELINE RAG OPTIMIZADO                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ══════════════════════════════════════════════════════════════════════════ │
│  INGESTIÓN (offline, batch)                                                  │
│  ══════════════════════════════════════════════════════════════════════════ │
│                                                                              │
│  Documento ──→ Clasificación ──→ Chunking Adaptativo ──→ Embedding 768d     │
│       │              │                    │                    │             │
│       │              ▼                    ▼                    ▼             │
│       │    ┌──────────────────────────────────────────────────────────────┐ │
│       │    │ IF tipo = Legal/Contrato:                                    │ │
│       │    │    → Agentic chunking + Parent Document                      │ │
│       │    │    → Overlap 25%                                             │ │
│       │    │                                                              │ │
│       │    │ ELIF tipo = Manual técnico:                                  │ │
│       │    │    → Recursive chunking (1024 tokens)                        │ │
│       │    │    → Overlap 15%                                             │ │
│       │    │                                                              │ │
│       │    │ ELIF tipo = FAQ/KB:                                          │ │
│       │    │    → Sentence chunking (256 tokens)                          │ │
│       │    │    → Overlap 0%                                              │ │
│       │    │                                                              │ │
│       │    │ ELSE:                                                        │ │
│       │    │    → Recursive chunking (512 tokens)                         │ │
│       │    │    → Overlap 10%                                             │ │
│       │    └──────────────────────────────────────────────────────────────┘ │
│       │                                         │                            │
│       │                                         ▼                            │
│       └──→ GCS (original)           halfvec(768) + HNSW + tsvector (BM25)   │
│                                                                              │
│  ══════════════════════════════════════════════════════════════════════════ │
│  BÚSQUEDA (online)                                                           │
│  ══════════════════════════════════════════════════════════════════════════ │
│                                                                              │
│  Query usuario                                                               │
│       │                                                                      │
│       ▼                                                                      │
│  ┌───────────────────┐     ┌───────────────────────────┐                    │
│  │ Cache Semántico   │ HIT │ Return cached response    │ (~5ms)             │
│  │ (Redis L1 + L2)   │────→│ + Log cache hit           │                    │
│  └─────────┬─────────┘     └───────────────────────────┘                    │
│            │ MISS                                                            │
│            ▼                                                                 │
│  ┌───────────────────┐                                                      │
│  │ Query Embedding   │ Gemini text-embedding-004 (768d) (~30ms)             │
│  └─────────┬─────────┘                                                      │
│            ▼                                                                 │
│  ┌───────────────────┐                                                      │
│  │ Hybrid Search     │ Vector (HNSW) + BM25 + RRF (~25ms)                   │
│  │ Top 50 candidatos │                                                      │
│  └─────────┬─────────┘                                                      │
│            ▼                                                                 │
│  ┌───────────────────┐                                                      │
│  │ Cohere Rerank     │ Cross-encoder multilingual (~80ms)                   │
│  │ Top 50 → Top 10   │ (skip para Call Center/velocidad)                    │
│  └─────────┬─────────┘                                                      │
│            ▼                                                                 │
│  ┌───────────────────┐                                                      │
│  │ LLM Generation    │ Gemini Pro con top 10 docs (~1500ms)                 │
│  │ + Citations       │                                                      │
│  └─────────┬─────────┘                                                      │
│            ▼                                                                 │
│  ┌───────────────────┐                                                      │
│  │ Cache Update      │ Guardar en L1 (exact) + L2 (semantic)                │
│  └─────────┬─────────┘                                                      │
│            ▼                                                                 │
│       Respuesta + Fuentes                                                    │
│                                                                              │
│  ══════════════════════════════════════════════════════════════════════════ │
│  LATENCIAS ESPERADAS:                                                        │
│  ══════════════════════════════════════════════════════════════════════════ │
│                                                                              │
│  • Cache Hit:     ~5ms                                                       │
│  • Cache Miss:    ~1,640ms (30 + 25 + 80 + 1500 + overhead)                  │
│  • Promedio:      ~545ms (con 67% cache hit rate)                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 11.7 Configuración Recomendada por Área

| Área | Chunking | Overlap | Embedding | Búsqueda | Rerank | Latencia Target |
|:-----|:---------|:-------:|:---------:|:---------|:------:|:---------------:|
| **RRHH** | Recursive | 15% | Gemini 768d | Hybrid | ✅ | <2s |
| **Call Center** | Sentence | 10% | Gemini 768d | Hybrid | ❌ | <1s |
| **Legal** | Agentic + Parent | 25% | Gemini 768d | Hybrid + Rerank | ✅ | <3s |
| **Operaciones** | Recursive | 15% | Gemini 768d | Hybrid | ✅ | <2s |
| **Finanzas** | Semantic | 20% | Gemini 768d | Hybrid + Rerank | ✅ | <2s |
| **KB General** | Sentence | 0% | Gemini 768d | Hybrid | ❌ | <500ms |

---
---
---

# SECCIÓN V: ANÁLISIS DE ESCENARIOS Y COSTOS

> **Nota Crítica:** Esta sección es la MÁS IMPORTANTE del documento porque **integra todas las decisiones técnicas anteriores y las traduce a costos concretos**. Los tres escenarios presentados representan diferentes puntos en el trade-off costo-calidad-complejidad.

---

## Capítulo 12: Escenario Baseline (Sin Optimizar)

Este escenario representa la implementación "estándar" sin aplicar las optimizaciones descritas en secciones anteriores. Sirve como **línea base para comparación**.

### 12.1 Configuración del Escenario Baseline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ESCENARIO BASELINE (SIN OPTIMIZAR)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  📦 EMBEDDING:                                                               │
│     • Modelo: Gemini text-embedding-004                                      │
│     • Dimensión: 1024 (sin Matryoshka)                                       │
│     • Precisión: float32 (sin halfvec)                                       │
│     • Bytes/vector: 4,104 B                                                  │
│                                                                              │
│  🗃️ BASE DE DATOS:                                                           │
│     • Tabla única (sin particionamiento)                                     │
│     • Índice HNSW: m=16, ef_construction=64                                  │
│     • Sin optimizaciones de RAM                                              │
│                                                                              │
│  ✂️ CHUNKING:                                                                 │
│     • Estrategia: Recursive básico                                           │
│     • Tamaño: 512 tokens                                                     │
│     • Overlap: 10%                                                           │
│                                                                              │
│  🔍 BÚSQUEDA:                                                                 │
│     • Solo vector search (sin híbrido)                                       │
│     • Sin reranking                                                          │
│     • Sin cache                                                              │
│                                                                              │
│  🤖 GENERACIÓN:                                                               │
│     • Llamada directa al LLM por cada query                                  │
│     • Sin cache semántico                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Dimensionamiento Baseline

Aplicando las fórmulas del Capítulo 2:

| Métrica | Fórmula | Valor |
|:--------|:--------|------:|
| **Documentos** | Input | 17,000,000 |
| **Páginas totales** | 17M × 10 páginas/doc | 170,000,000 |
| **Chunks** | 170M páginas × 1.3 chunks/página × 1.10 (overlap) | ~243,100,000 |
| **Vectores ($N$)** | = Chunks | **~244 M** |

#### Almacenamiento

| Componente | Fórmula | Tamaño |
|:-----------|:--------|-------:|
| Bytes por vector | $d \times 4 + 8$ = 1024 × 4 + 8 | 4,104 B |
| **Tabla de datos** | 244M × (4,104 + 200) B | **~1.05 TB** |
| **Índice HNSW** | 244M × 4,104 × 1.1 | **~1.15 TB** |
| **Disco TOTAL** | Tabla + Índice + Overhead | **~2.5 TB** |

#### RAM Requerida

| Componente | Cálculo | RAM |
|:-----------|:--------|----:|
| Índice HNSW hot (20%) | 1.15 TB × 0.20 | ~230 GB |
| Buffer pool | | ~32 GB |
| OS + overhead | | ~16 GB |
| **RAM TOTAL** | | **~280 GB** |

### 12.3 Costos Mensuales Baseline

| Componente | Descripción | Costo/mes |
|:-----------|:------------|----------:|
| **Cloud SQL Enterprise** | db-custom-48-307200 (48 vCPU, 300 GB RAM) | ~$3,200 |
| | Disco SSD 3 TB | (incluido) |
| **Embeddings API** | ~10K queries/día × 30 días × $0.025/1K tokens | ~$1,500 |
| **LLM API (Gemini Pro)** | ~10K queries/día × 30 días × $0.007/query | ~$2,000 |
| **Redis (Memorystore)** | Standard, 8 GB (solo para sesiones) | ~$300 |
| **Reranker API** | Cohere Rerank, ~5K/día | ~$400 |
| **Cloud Storage** | 17 TB Standard | ~$200 |
| **Cloud Run** | Servicios API | ~$500 |
| **Networking** | Egress interno | ~$150 |
| **Logging/Monitoring** | Cloud Operations | ~$100 |
| **TOTAL MENSUAL** | | **~$8,350/mes** |

### 12.4 Costo de Ingestión Inicial

El costo one-time de procesar e indexar los 17 TB de documentos:

| Componente | Descripción | Costo |
|:-----------|:------------|------:|
| **Embedding de 17 TB** | ~4,000M tokens × $0.025/1K tokens | ~$100,000 |
| **Procesamiento (Cloud Run)** | OCR + Chunking + Parsing | ~$2,000 |
| **Desarrollo** | ~400 horas × $100/hora | ~$40,000 |
| **Testing y validación** | ~100 horas × $100/hora | ~$10,000 |
| **TOTAL INGESTIÓN** | | **~$152,000** |

### 12.5 TCO 3 Años - Escenario Baseline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TCO 3 AÑOS - ESCENARIO BASELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  AÑO 0 (Implementación):                                                     │
│  ───────────────────────                                                     │
│  • Ingestión inicial:                    $152,000                            │
│  • Operación (6 meses):                  $50,100  ($8,350 × 6)               │
│  • Subtotal Año 0:                       $202,100                            │
│                                                                              │
│  AÑO 1:                                                                      │
│  ──────                                                                      │
│  • Operación (12 meses):                 $100,200 ($8,350 × 12)              │
│                                                                              │
│  AÑO 2:                                                                      │
│  ──────                                                                      │
│  • Operación (12 meses):                 $100,200 ($8,350 × 12)              │
│  • Re-indexación parcial (~20%):         $20,000                             │
│  • Subtotal Año 2:                       $120,200                            │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════════ │
│                                                                              │
│  TOTAL TCO 3 AÑOS:                       $422,500                            │
│  Promedio mensual:                       $11,736/mes                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.6 Métricas de Performance Baseline

| Métrica | Valor Esperado | Notas |
|:--------|:--------------:|:------|
| **Latencia P50** | ~1,800 ms | Sin cache |
| **Latencia P95** | ~3,500 ms | Queries complejas |
| **Throughput** | ~20 QPS | Limitado por LLM |
| **Recall@10** | ~85% | Solo vector search |
| **Cache Hit Rate** | 0% | Sin cache |

---

## Capítulo 13: Escenario Optimizado (RECOMENDADO)

Este escenario aplica **todas las optimizaciones descritas en el documento** para lograr el mejor balance entre costo, calidad y complejidad operativa.

### 13.1 Configuración del Escenario Optimizado

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ESCENARIO OPTIMIZADO (RECOMENDADO)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  📦 EMBEDDING:                                                               │
│     • Modelo: Gemini text-embedding-004                                      │
│     • Dimensión: 768 (Matryoshka truncation)                                 │
│     • Precisión: float16 (halfvec)                                           │
│     • Bytes/vector: 1,544 B                                                  │
│     • Retención calidad: ~97.5%                                              │
│                                                                              │
│  🗃️ BASE DE DATOS:                                                           │
│     • Particionamiento por área (6 particiones)                              │
│     • Índice HNSW por partición: m=16, ef_construction=64                    │
│     • Índice GIN para BM25 (tsvector)                                        │
│                                                                              │
│  ✂️ CHUNKING:                                                                 │
│     • Estrategia: Adaptativa por tipo de documento                           │
│     • Legal: Agentic + Parent (25% overlap)                                  │
│     • Técnico: Recursive 1024 tokens (15% overlap)                           │
│     • FAQ/KB: Sentence (0% overlap)                                          │
│                                                                              │
│  🔍 BÚSQUEDA:                                                                 │
│     • Hybrid Search (Vector + BM25 + RRF)                                    │
│     • Cohere Rerank para áreas críticas (Legal, Finanzas)                    │
│     • Partition pruning por área                                             │
│                                                                              │
│  💾 CACHE:                                                                    │
│     • Cache semántico multi-nivel (Redis)                                    │
│     • L1: Exact match (~30% hit rate)                                        │
│     • L2: Semantic similarity (~40% hit rate)                                │
│     • Hit rate combinado: ~67%                                               │
│                                                                              │
│  🤖 GENERACIÓN:                                                               │
│     • Gemini Pro con cache de respuestas                                     │
│     • TTL: 24 horas                                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 13.2 Dimensionamiento Optimizado

| Métrica | Baseline | Optimizado | Reducción |
|:--------|:--------:|:----------:|:---------:|
| **Vectores** | 244 M | 244 M | 0% |
| **Bytes/vector** | 4,104 B | 1,544 B | **-62%** |
| **Disco (tabla)** | ~1.05 TB | ~400 GB | **-62%** |
| **Disco (índice)** | ~1.15 TB | ~450 GB | **-61%** |
| **Disco TOTAL** | ~2.5 TB | **~950 GB** | **-62%** |
| **RAM requerida** | ~280 GB | **~90 GB** | **-68%** |

### 13.3 Costos Mensuales Optimizados

| Componente | Baseline | Optimizado | Ahorro | Razón del ahorro |
|:-----------|:--------:|:----------:|:------:|:-----------------|
| **Cloud SQL Enterprise** | $3,200 | **$1,200** | -$2,000 | Menos RAM/disco |
| **Embeddings API** | $1,500 | **$500** | -$1,000 | Cache de embeddings |
| **LLM API** | $2,000 | **$600** | -$1,400 | Cache semántico (67% hit) |
| **Redis** | $300 | **$350** | +$50 | Más capacidad para cache |
| **Reranker API** | $400 | **$400** | $0 | Sin cambio |
| **Cloud Storage** | $200 | **$200** | $0 | Sin cambio |
| **Cloud Run** | $500 | **$500** | $0 | Sin cambio |
| **Networking** | $150 | **$150** | $0 | Sin cambio |
| **Logging/Monitoring** | $100 | **$100** | $0 | Sin cambio |
| **TOTAL MENSUAL** | $8,350 | **$4,000** | **-$4,350** | **-52%** |

### 13.4 Costo de Ingestión Inicial (Optimizado)

| Componente | Baseline | Optimizado | Ahorro | Razón |
|:-----------|:--------:|:----------:|:------:|:------|
| **Embedding de 17 TB** | $100,000 | **$100,000** | $0 | Mismo modelo/tokens |
| **Procesamiento** | $2,000 | **$3,000** | +$1,000 | Chunking adaptativo |
| **Desarrollo** | $40,000 | **$45,000** | +$5,000 | Más complejidad |
| **Testing** | $10,000 | **$12,000** | +$2,000 | Validación de optimizaciones |
| **TOTAL INGESTIÓN** | $152,000 | **$160,000** | +$8,000 | — |

> **Nota:** El costo de ingestión es ligeramente mayor por la complejidad adicional, pero se recupera rápidamente con los ahorros operativos.

### 13.5 TCO 3 Años - Escenario Optimizado

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TCO 3 AÑOS - ESCENARIO OPTIMIZADO                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  AÑO 0 (Implementación):                                                     │
│  ───────────────────────                                                     │
│  • Ingestión inicial:                    $60,000    (con BGE-M3 parcial)     │
│  • Operación (6 meses):                  $24,000    ($4,000 × 6)             │
│  • Subtotal Año 0:                       $84,000                             │
│                                                                              │
│  AÑO 1:                                                                      │
│  ──────                                                                      │
│  • Operación (12 meses):                 $48,000    ($4,000 × 12)            │
│                                                                              │
│  AÑO 2:                                                                      │
│  ──────                                                                      │
│  • Operación (12 meses):                 $48,000    ($4,000 × 12)            │
│  • Re-indexación parcial (~20%):         $12,000                             │
│  • Subtotal Año 2:                       $60,000                             │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════════ │
│                                                                              │
│  TOTAL TCO 3 AÑOS:                       $192,000                            │
│  Promedio mensual:                       $5,333/mes                          │
│                                                                              │
│  AHORRO vs. BASELINE:                    $230,500 (-55%)                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 13.6 Métricas de Performance Optimizado

| Métrica | Baseline | Optimizado | Mejora |
|:--------|:--------:|:----------:|:------:|
| **Latencia P50** | ~1,800 ms | **~545 ms** | **-70%** |
| **Latencia P95** | ~3,500 ms | **~1,800 ms** | **-49%** |
| **Throughput** | ~20 QPS | **~60 QPS** | **+200%** |
| **Recall@10** | ~85% | **~92%** | **+7%** |
| **Cache Hit Rate** | 0% | **~67%** | — |
| **Costo/query** | $0.028 | **$0.009** | **-68%** |

### 13.7 Retención de Calidad

| Componente | Impacto en Calidad |
|:-----------|:-------------------|
| Matryoshka 768d (vs 1024d) | ~98% retención |
| halfvec (float16 vs float32) | ~99.9% retención |
| **Combinado** | **~97.5% retención** |
| Hybrid Search (vs vector puro) | **+10-15% mejora** |
| Reranking | **+15-20% mejora** |

> ⭐ **Resultado neto:** A pesar de la compresión, la calidad de retrieval **mejora** gracias a hybrid search y reranking.

---

## Capítulo 14: Escenario Ultra-Optimizado (Open Source)

Este escenario maximiza la reducción de costos usando modelos open source y optimizaciones agresivas. Adecuado para organizaciones con expertise técnico y tolerancia a menor calidad.

### 14.1 Configuración Ultra-Optimizada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ESCENARIO ULTRA-OPTIMIZADO (OPEN SOURCE)                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  📦 EMBEDDING:                                                               │
│     • Modelo: BGE-M3 (open source, local)                                    │
│     • Dimensión: 512 (truncation)                                            │
│     • Precisión: float16 (halfvec)                                           │
│     • Bytes/vector: 1,032 B                                                  │
│     • Retención calidad: ~94%                                                │
│                                                                              │
│  🖥️ INFRAESTRUCTURA EMBEDDINGS:                                              │
│     • 4x VMs con GPU T4 (spot instances)                                     │
│     • ONNX runtime optimizado                                                │
│     • Throughput: ~10K embeddings/segundo                                    │
│                                                                              │
│  🗃️ BASE DE DATOS:                                                           │
│     • Todas las optimizaciones del escenario anterior                        │
│     • Particionamiento más agresivo (10+ particiones)                        │
│                                                                              │
│  🔍 BÚSQUEDA:                                                                 │
│     • Hybrid Search + BGE-reranker-v2-m3 (local)                             │
│     • Sin costos de APIs externas                                            │
│                                                                              │
│  🤖 GENERACIÓN:                                                               │
│     • Gemini Pro (único componente cloud)                                    │
│     • Cache semántico agresivo (TTL 48h)                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 14.2 Dimensionamiento Ultra-Optimizado

| Métrica | Baseline | Optimizado | Ultra-Opt | Reducción vs. Baseline |
|:--------|:--------:|:----------:|:---------:|:----------------------:|
| **Vectores** | 244 M | 244 M | 244 M | 0% |
| **Bytes/vector** | 4,104 B | 1,544 B | 1,032 B | **-75%** |
| **Disco TOTAL** | ~2.5 TB | ~950 GB | **~650 GB** | **-74%** |
| **RAM requerida** | ~280 GB | ~90 GB | **~65 GB** | **-77%** |

### 14.3 Costos Mensuales Ultra-Optimizados

| Componente | Baseline | Optimizado | Ultra-Opt | vs. Baseline |
|:-----------|:--------:|:----------:|:---------:|:------------:|
| **Cloud SQL Enterprise** | $3,200 | $1,200 | **$900** | -72% |
| **Embeddings** | $1,500 | $500 | **$0** | -100% (local) |
| **LLM API** | $2,000 | $600 | **$400** | -80% (cache 80%) |
| **GPU VMs (embeddings)** | $0 | $0 | **$400** | +$400 |
| **GPU VMs (reranker)** | $0 | $0 | **$200** | +$200 |
| **Redis** | $300 | $350 | **$350** | +$50 |
| **Reranker API** | $400 | $400 | **$0** | -100% (local) |
| **Cloud Storage** | $200 | $200 | **$200** | 0% |
| **Cloud Run** | $500 | $500 | **$400** | -20% |
| **Networking** | $150 | $150 | **$100** | -33% |
| **Logging** | $100 | $100 | **$100** | 0% |
| **TOTAL MENSUAL** | $8,350 | $4,000 | **$3,050** | **-63%** |

### 14.4 Costo de Ingestión Inicial (Ultra-Optimizado)

| Componente | Baseline | Optimizado | Ultra-Opt |
|:-----------|:--------:|:----------:|:---------:|
| **Embedding de 17 TB** | $100,000 | $100,000 | **$8,000** |
| | | | (solo GPU spot) |
| **Procesamiento** | $2,000 | $3,000 | **$3,000** |
| **Desarrollo** | $40,000 | $45,000 | **$60,000** |
| | | | (más complejo) |
| **Testing** | $10,000 | $12,000 | **$14,000** |
| **TOTAL INGESTIÓN** | $152,000 | $160,000 | **$85,000** |

### 14.5 TCO 3 Años - Escenario Ultra-Optimizado

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TCO 3 AÑOS - ESCENARIO ULTRA-OPTIMIZADO                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  AÑO 0 (Implementación):                                                     │
│  ───────────────────────                                                     │
│  • Ingestión inicial:                    $25,000    (GPU spot + optimizado)  │
│  • Operación (6 meses):                  $18,300    ($3,050 × 6)             │
│  • Subtotal Año 0:                       $43,300                             │
│                                                                              │
│  AÑO 1:                                                                      │
│  ──────                                                                      │
│  • Operación (12 meses):                 $36,600    ($3,050 × 12)            │
│                                                                              │
│  AÑO 2:                                                                      │
│  ──────                                                                      │
│  • Operación (12 meses):                 $36,600    ($3,050 × 12)            │
│  • Re-indexación parcial (~20%):         $2,000     (solo GPU)               │
│  • Subtotal Año 2:                       $38,600                             │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════════ │
│                                                                              │
│  TOTAL TCO 3 AÑOS:                       $118,500                            │
│  Promedio mensual:                       $3,292/mes                          │
│                                                                              │
│  AHORRO vs. BASELINE:                    $304,000 (-72%)                     │
│  AHORRO vs. OPTIMIZADO:                  $73,500 (-38%)                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 14.6 Trade-offs del Escenario Ultra-Optimizado

| Aspecto | Ventaja | Desventaja |
|:--------|:--------|:-----------|
| **Costo** | -72% vs. baseline | — |
| **Calidad** | — | ~94% retención (vs. ~97.5% optimizado) |
| **Complejidad** | — | Alta (gestionar GPUs, modelos locales) |
| **Expertise requerido** | — | Requiere ML engineers |
| **Soporte** | — | Sin soporte enterprise |
| **Escalabilidad** | — | Manual, requiere planificación |
| **Time-to-market** | — | +2-4 semanas de desarrollo |
| **Riesgo operativo** | — | Mayor (más componentes) |

---

## Capítulo 15: Comparativa y Decisión Final

### 15.1 Tabla Comparativa Completa

| Aspecto | Baseline | Optimizado | Ultra-Optimizado |
|:--------|:--------:|:----------:|:----------------:|
| **DIMENSIONAMIENTO** | | | |
| Vectores | 244 M | 244 M | 244 M |
| Bytes/vector | 4,104 B | 1,544 B | 1,032 B |
| Disco total | 2.5 TB | 950 GB | 650 GB |
| RAM requerida | 280 GB | 90 GB | 65 GB |
| | | | |
| **COSTOS** | | | |
| Mensual operativo | $8,350 | $4,000 | $3,050 |
| Ingestión inicial | $152,000 | $60,000 | $25,000 |
| TCO 3 años | $422,500 | $192,000 | $118,500 |
| Costo/mes promedio | $11,736 | $5,333 | $3,292 |
| | | | |
| **PERFORMANCE** | | | |
| Latencia P50 | 1,800 ms | 545 ms | 600 ms |
| Throughput | 20 QPS | 60 QPS | 50 QPS |
| Cache hit rate | 0% | 67% | 80% |
| Recall@10 | 85% | 92% | 88% |
| | | | |
| **CALIDAD** | | | |
| Retención de calidad | 100% | 97.5% | 94% |
| Hybrid search | ❌ | ✅ | ✅ |
| Reranking | ❌ | ✅ (API) | ✅ (local) |
| | | | |
| **OPERATIVO** | | | |
| Complejidad | Baja | Media | Alta |
| Expertise requerido | PostgreSQL | PostgreSQL + ML | PostgreSQL + ML + GPU |
| Soporte enterprise | ✅ | ✅ | ❌ |
| Time-to-production | 3 meses | 4 meses | 5-6 meses |

### 15.2 Gráfico de TCO a 3 Años

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TCO ACUMULADO (3 AÑOS)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  $450K ─┤                                         ┌────────────────────      │
│         │                                    ╱────┘                          │
│  $400K ─┤                               ╱───╯    BASELINE: $422.5K           │
│         │                          ╱────╯                                    │
│  $350K ─┤                     ╱────╯                                         │
│         │                ╱────╯                                              │
│  $300K ─┤           ╱────╯                                                   │
│         │      ╱────╯                                                        │
│  $250K ─┤ ╱────╯                                                             │
│         │╱           ┌─────────────────────────────────────                  │
│  $200K ─┤       ╱───┘                                                        │
│         │  ╱───╯     OPTIMIZADO: $192K                                       │
│  $150K ─┤╱──╯                                                                │
│         │    ┌───────────────────────────────────                            │
│  $100K ─┤╱──╯                                                                │
│         │    ULTRA-OPT: $118.5K                                              │
│   $50K ─┤                                                                    │
│         │                                                                    │
│     $0 ─┼────────────┼────────────┼────────────┼────────────┼                │
│         Año 0        Año 0.5      Año 1        Año 2        Año 3            │
│                                                                              │
│  AHORRO ACUMULADO A 3 AÑOS:                                                  │
│  • Optimizado vs. Baseline:     $230,500 (55% menos)                         │
│  • Ultra-Opt vs. Baseline:      $304,000 (72% menos)                         │
│  • Ultra-Opt vs. Optimizado:    $73,500 (38% menos)                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.3 Análisis de Trade-offs

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ANÁLISIS DE TRADE-OFFS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                           COSTO                                              │
│                             ▲                                                │
│                             │                                                │
│                   BASELINE  ●                                                │
│                 ($422K TCO) │                                                │
│                             │                                                │
│                             │                                                │
│                             │    ● OPTIMIZADO ($192K)                        │
│                             │    ⭐ MEJOR BALANCE                            │
│                             │                                                │
│                             │          ● ULTRA-OPT ($118K)                   │
│                             │                                                │
│  ───────────────────────────┼───────────────────────────────▶ CALIDAD        │
│                           94%              97.5%         100%                │
│                             │                                                │
│                             │                                                │
│                             │         COMPLEJIDAD                             │
│                             ▼         Alta ────────────▶ Baja                │
│                                                                              │
│                                                                              │
│  ZONAS DE DECISIÓN:                                                          │
│  ──────────────────                                                          │
│  • Presupuesto muy limitado + expertise ML → Ultra-Optimizado                │
│  • Balance costo/calidad/riesgo → ⭐ OPTIMIZADO (recomendado)                │
│  • Tiempo crítico + sin expertise ML → Baseline (no recomendado)             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.4 Decisión Final

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                                                                       ║  │
│  ║              DECISIÓN: ESCENARIO OPTIMIZADO                           ║  │
│  ║                                                                       ║  │
│  ╚═══════════════════════════════════════════════════════════════════════╝  │
│                                                                              │
│  CONFIGURACIÓN RECOMENDADA:                                                  │
│  ══════════════════════════                                                  │
│                                                                              │
│  • Embedding: Gemini text-embedding-004, 768d (Matryoshka)                   │
│  • Precisión: halfvec (float16)                                              │
│  • Base de datos: Cloud SQL Enterprise + pgvector                            │
│  • Particionamiento: Por área funcional (6 particiones)                      │
│  • Búsqueda: Hybrid (Vector + BM25 + RRF)                                    │
│  • Reranking: Cohere Rerank para áreas críticas                              │
│  • Cache: Semántico multi-nivel (Redis)                                      │
│                                                                              │
│  ════════════════════════════════════════════════════════════════════════   │
│                                                                              │
│  RAZONES DE LA DECISIÓN:                                                     │
│  ══════════════════════                                                      │
│                                                                              │
│  1. BALANCE COSTO-CALIDAD ÓPTIMO                                             │
│     • 55% ahorro vs. baseline                                                │
│     • 97.5% retención de calidad                                             │
│     • Mejora real de 92% recall (vs. 85% baseline)                           │
│                                                                              │
│  2. COMPLEJIDAD MANEJABLE                                                    │
│     • No requiere expertise en GPUs                                          │
│     • Soporte enterprise disponible (GCP, Cohere)                            │
│     • Debugging con herramientas familiares                                  │
│                                                                              │
│  3. RIESGO CONTROLADO                                                        │
│     • APIs managed = SLAs garantizados                                       │
│     • Rollback simple si hay problemas                                       │
│     • Escalado automático disponible                                         │
│                                                                              │
│  4. TIME-TO-MARKET RAZONABLE                                                 │
│     • 4 meses vs. 5-6 meses de ultra-opt                                     │
│     • MVP funcional en 2 meses                                               │
│                                                                              │
│  5. FLEXIBILIDAD FUTURA                                                      │
│     • Migrar a open source después es posible                                │
│     • Escalar a más vectores sin rediseño                                    │
│                                                                              │
│  ════════════════════════════════════════════════════════════════════════   │
│                                                                              │
│  RUTA DE ESCAPE A ULTRA-OPTIMIZADO:                                          │
│  ═════════════════════════════════                                          │
│                                                                              │
│  Si después de 12 meses el costo sigue siendo una preocupación:              │
│                                                                              │
│  • Fase 1: Migrar embeddings a BGE-M3 local (ahorro: $500/mes)               │
│  • Fase 2: Migrar reranking a BGE-reranker (ahorro: $400/mes)                │
│  • Fase 3: Optimizar LLM con cache más agresivo                              │
│                                                                              │
│  Esto permite una migración gradual sin riesgo de big-bang.                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.5 Alternativas Open Source para Embeddings

Si en el futuro se desea reducir costos de embeddings, estas son las alternativas validadas:

| Modelo | Calidad vs. Gemini | Multilingüe | Costo Ingestión 17 TB | Infraestructura |
|:-------|:------------------:|:-----------:|:---------------------:|:----------------|
| **Gemini API** | 100% | ✅ | ~$100,000 | Ninguna |
| **BGE-M3 (local)** | ~95-98% | ✅ 100+ langs | ~$8,000-15,000 | 4x T4 GPUs |
| **E5-large-v2** | ~92-95% | ✅ | ~$6,000-12,000 | 4x T4 GPUs |
| **Multilingual-e5** | ~93-96% | ✅ 100+ langs | ~$7,000-14,000 | 4x T4 GPUs |

> 💡 **Recomendación:** Usar Gemini API inicialmente para simplicidad, con opción de migrar a BGE-M3 después de validar el sistema.

---
---

# SECCIÓN VI: OPERACIONES Y PRODUCCIÓN

> **Nota:** Esta sección aplica específicamente al **Escenario Optimizado** (el recomendado en la Sección V). Los procedimientos y configuraciones asumen la arquitectura con Gemini embeddings, halfvec, cache semántico y particionamiento.

---

## Capítulo 16: Framework de Evaluación de Calidad

La evaluación continua de la calidad del sistema RAG es crítica para mantener y mejorar el rendimiento en producción.

### 16.1 Métricas de Retrieval

Estas métricas evalúan la calidad de la **búsqueda** de documentos relevantes:

| Métrica | Qué Mide | Cómo Calcular | Target | Criticidad |
|:--------|:---------|:--------------|:------:|:----------:|
| **Recall@K** | ¿El doc relevante está en top K? | Docs relevantes en top K / Total relevantes | >90% (K=10) | 🔴 Alta |
| **Precision@K** | ¿Cuántos de top K son relevantes? | Docs relevantes en top K / K | >70% (K=10) | 🟡 Media |
| **MRR** | ¿Qué tan arriba está el primer relevante? | 1/posición del primer relevante | >0.7 | 🟡 Media |
| **nDCG** | Calidad del ranking considerando posiciones | DCG/IDCG | >0.8 | 🟡 Media |
| **Hit Rate** | ¿Hay al menos 1 relevante en top K? | Queries con hit / Total queries | >95% | 🔴 Alta |

### 16.2 Métricas de Generación (RAG End-to-End)

Estas métricas evalúan la calidad de las **respuestas generadas** por el LLM:

| Métrica | Qué Mide | Herramienta | Target | Criticidad |
|:--------|:---------|:------------|:------:|:----------:|
| **Faithfulness** | ¿La respuesta es fiel al contexto? | RAGAS, TruLens | >85% | 🔴 Alta |
| **Answer Relevancy** | ¿Responde la pregunta? | RAGAS | >80% | 🔴 Alta |
| **Groundedness** | ¿Evita alucinaciones? | TruLens, DeepEval | >90% | 🔴 Crítica |
| **Context Precision** | ¿El contexto recuperado es preciso? | RAGAS | >75% | 🟡 Media |
| **Context Recall** | ¿Se recuperó todo el contexto necesario? | RAGAS | >85% | 🟡 Media |
| **Answer Correctness** | ¿La respuesta es factualmente correcta? | DeepEval, manual | >85% | 🔴 Alta |

### 16.3 Implementación con RAGAS

```python
# evaluator.py - Módulo de evaluación automatizada con RAGAS

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.llms import LangchainLLM
from langchain_google_vertexai import ChatVertexAI
from datasets import Dataset
import pandas as pd
from typing import List, Dict
import json

class RAGEvaluator:
    """
    Evaluador de calidad RAG usando RAGAS.
    Requiere un golden set con queries, respuestas y ground truth.
    """
    
    def __init__(self, project_id: str = "enterprise-ai-platform"):
        # Configurar LLM para evaluación (Gemini Pro)
        self.llm = ChatVertexAI(
            model_name="gemini-1.5-pro",
            project=project_id,
            temperature=0  # Determinístico para evaluación
        )
        
        # Métricas a evaluar
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ]
    
    def load_golden_set(self, filepath: str) -> Dataset:
        """
        Carga golden set desde JSON.
        
        Formato esperado:
        [
            {
                "question": "¿Cuántos días de vacaciones tengo?",
                "answer": "Los empleados tienen 15 días...",
                "contexts": ["Política de vacaciones: ..."],
                "ground_truth": "15 días hábiles anuales"
            },
            ...
        ]
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return Dataset.from_dict({
            "question": [item["question"] for item in data],
            "answer": [item["answer"] for item in data],
            "contexts": [item["contexts"] for item in data],
            "ground_truth": [item["ground_truth"] for item in data],
        })
    
    def evaluate(self, dataset: Dataset) -> Dict[str, float]:
        """
        Ejecuta evaluación completa y retorna métricas.
        """
        result = evaluate(
            dataset=dataset,
            metrics=self.metrics,
            llm=LangchainLLM(llm=self.llm),
        )
        
        return {
            "faithfulness": result["faithfulness"],
            "answer_relevancy": result["answer_relevancy"],
            "context_precision": result["context_precision"],
            "context_recall": result["context_recall"],
            "timestamp": pd.Timestamp.now().isoformat(),
        }
    
    def check_thresholds(self, metrics: Dict[str, float]) -> Dict[str, bool]:
        """
        Verifica si las métricas cumplen los thresholds mínimos.
        """
        thresholds = {
            "faithfulness": 0.85,
            "answer_relevancy": 0.80,
            "context_precision": 0.75,
            "context_recall": 0.85,
        }
        
        return {
            metric: metrics.get(metric, 0) >= threshold
            for metric, threshold in thresholds.items()
        }

# Uso en CI/CD o batch job
if __name__ == "__main__":
    evaluator = RAGEvaluator()
    
    # Cargar golden set (mínimo 50-100 ejemplos para resultados confiables)
    dataset = evaluator.load_golden_set("golden_set_200.json")
    
    # Ejecutar evaluación
    metrics = evaluator.evaluate(dataset)
    print(f"Resultados: {metrics}")
    
    # Verificar thresholds
    passed = evaluator.check_thresholds(metrics)
    if all(passed.values()):
        print("✅ Todas las métricas cumplen thresholds")
    else:
        failed = [k for k, v in passed.items() if not v]
        print(f"❌ Métricas bajo threshold: {failed}")
```

### 16.4 Frecuencia de Evaluación

| Tipo | Frecuencia | Samples | Responsable | Automatizado |
|:-----|:----------:|:-------:|:------------|:------------:|
| **Smoke tests** | Cada deploy | 10 queries fijas | CI/CD | ✅ |
| **Regression** | Semanal | 50-100 queries | ML Engineer | ✅ |
| **Golden set completo** | Mensual | 200+ queries anotadas | QA + Domain Expert | ✅ |
| **A/B testing** | Por feature | Tráfico real | Data Science | ❌ (manual) |
| **User feedback** | Continuo | Thumbs up/down | Usuarios | ❌ (continuo) |

### 16.5 Dashboard de Métricas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      RAG QUALITY DASHBOARD                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  RETRIEVAL METRICS                     GENERATION METRICS                    │
│  ─────────────────                     ───────────────────                   │
│  Recall@10:     92% ████████████░░     Faithfulness:   87% █████████░░░     │
│  Precision@10:  74% ██████████░░░░     Answer Rel:     82% ████████░░░░     │
│  MRR:           0.78 ██████████░░░     Groundedness:   91% ████████████░     │
│  Hit Rate:      96% █████████████░     Context Prec:   78% ██████████░░░     │
│                                                                              │
│  LATENCY (ms)                          COST (last 30 days)                   │
│  ─────────────                         ───────────────────                   │
│  p50: 45ms   ████░░░░░░                Embeddings:   $487                    │
│  p95: 112ms  ██████░░░░                LLM:          $623                    │
│  p99: 245ms  █████████░                Reranker:     $178                    │
│                                        Infra:        $1,245                  │
│  Cache Hit Rate: 67%                   TOTAL:        $2,533                  │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  TREND (30 días)                       ALERTS                                │
│  ──────────────                        ──────                                │
│  Recall@10:    ↑ +2.3%                 ⚠️ Context Precision bajo 75%         │
│  Faithfulness: → 0%                    ✅ No hay alertas críticas            │
│  Latency p95:  ↓ -8%                                                         │
│  Cache Hit:    ↑ +5%                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Capítulo 17: Estrategia de Actualización de Datos

Mantener los embeddings sincronizados con los documentos fuente es crítico para la precisión del sistema.

### 17.1 Tipos de Cambios en el Corpus

| Tipo de Cambio | Frecuencia Típica | Estrategia | Complejidad |
|:---------------|:-----------------:|:-----------|:-----------:|
| **Nuevos documentos** | Diaria | Incremental indexing | Baja |
| **Documentos modificados** | Semanal | Re-embedding selectivo | Media |
| **Documentos eliminados** | Mensual | Soft delete + cleanup batch | Baja |
| **Cambio de modelo embedding** | Anual | Full reindex (planificado) | Alta |
| **Cambio de parámetros chunking** | Raro | Re-procesamiento selectivo | Alta |

### 17.2 Pipeline de Actualización (CDC)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE ACTUALIZACIÓN (CDC)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  OPENTEXT / FUENTES                                                          │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────┐                                                        │
│  │ CDC (Change     │  Detecta: nuevos, modificados, eliminados              │
│  │ Data Capture)   │  Frecuencia: cada 1 hora                               │
│  │                 │  Método: timestamp comparison / hash                   │
│  └────────┬────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        CLASIFICACIÓN DE CAMBIOS                         ││
│  │                                                                         ││
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐               ││
│  │  │   Nuevos    │     │ Modificados │     │ Eliminados  │               ││
│  │  │    docs     │     │    docs     │     │    docs     │               ││
│  │  │  (~500/día) │     │  (~200/día) │     │  (~50/día)  │               ││
│  │  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘               ││
│  │         │                   │                   │                       ││
│  │         ▼                   ▼                   ▼                       ││
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐               ││
│  │  │   Chunk +   │     │  Eliminar   │     │   Marcar    │               ││
│  │  │   Embed +   │     │  chunks     │     │   deleted   │               ││
│  │  │   INSERT    │     │  antiguos   │     │  (soft del) │               ││
│  │  └──────┬──────┘     │  + Re-chunk │     └──────┬──────┘               ││
│  │         │            │  + Re-embed │            │                       ││
│  │         │            │  + UPSERT   │            │                       ││
│  │         │            └──────┬──────┘            │                       ││
│  │         │                   │                   │                       ││
│  └─────────┴───────────────────┴───────────────────┴───────────────────────┘│
│                                │                                             │
│                                ▼                                             │
│                    ┌───────────────────────┐                                │
│                    │      pgvector         │                                │
│                    │   (INSERT/UPSERT)     │                                │
│                    └───────────────────────┘                                │
│                                                                              │
│  JOBS BATCH (nocturnos, 3 AM):                                               │
│  ─────────────────────────────                                              │
│  • Cleanup de soft-deleted (>30 días)                                       │
│  • VACUUM ANALYZE en tablas de embeddings                                   │
│  • Actualización de estadísticas                                             │
│  • Rebuild de índices fragmentados (si fragmentación >20%)                  │
│  • Invalidación de cache para docs modificados                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 17.3 SLAs de Freshness por Área

| Área | Freshness SLA | Estrategia | Justificación | Prioridad CDC |
|:-----|:-------------:|:-----------|:--------------|:-------------:|
| **Políticas RRHH** | 24 horas | Batch diario (noche) | Cambios poco frecuentes | Baja |
| **Call Center KB** | 4 horas | Near real-time | Procedimientos se actualizan frecuentemente | Alta |
| **Legal** | 1 hora | Near real-time | Contratos activos, compliance | Crítica |
| **Operaciones** | 24 horas | Batch diario (noche) | Manuales estables | Baja |
| **Finanzas** | 24 horas | Batch diario (noche) | Reportes periódicos | Media |

### 17.4 Costos de Re-indexación

| Operación | Volumen | Frecuencia | Costo Estimado |
|:----------|:-------:|:----------:|:--------------:|
| **Incremental diario** | ~0.5% del corpus (~850K chunks) | Diaria | ~$50/día |
| **Incremental semanal** | ~2% del corpus (~3.4M chunks) | Semanal | ~$200/semana |
| **Batch mensual** | ~5% del corpus (~8.5M chunks) | Mensual | ~$500/mes |
| **Full reindex** | 100% (~170M chunks) | Anual/emergencia | ~$100,000 |

> ⚠️ **Recomendación:** Planificar el full reindex anualmente, preferiblemente en fin de semana o período de bajo tráfico. Considerar BGE-M3 local para reducir costos.

---

## Capítulo 18: Alta Disponibilidad y Disaster Recovery

### 18.1 Arquitectura de Alta Disponibilidad

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA DE ALTA DISPONIBILIDAD                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  REGIÓN: southamerica-east1 (São Paulo)                                     │
│  ───────────────────────────────────────                                    │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    CLOUD SQL ENTERPRISE                               │  │
│  │                                                                       │  │
│  │  ┌─────────────────┐                  ┌─────────────────┐            │  │
│  │  │    ZONA A       │                  │    ZONA B       │            │  │
│  │  │   (primary)     │◄────Sync────────►│   (standby)     │            │  │
│  │  │                 │    Replication   │                 │            │  │
│  │  │  pgvector       │                  │  pgvector       │            │  │
│  │  │  + índices      │                  │  + índices      │            │  │
│  │  │                 │                  │                 │            │  │
│  │  │  db-custom-16   │                  │  db-custom-16   │            │  │
│  │  │  96GB RAM       │                  │  96GB RAM       │            │  │
│  │  └────────┬────────┘                  └────────┬────────┘            │  │
│  │           │                                    │                      │  │
│  │           │ Automatic                          │ Failover             │  │
│  │           │ Failover                           │ (<60 sec)            │  │
│  │           │                                    │                      │  │
│  │  ┌────────┴────────────────────────────────────┴────────┐            │  │
│  │  │              Internal Load Balancer                   │            │  │
│  │  │              (Private IP: 10.0.1.x)                   │            │  │
│  │  └───────────────────────┬───────────────────────────────┘            │  │
│  │                          │                                             │  │
│  │  ┌───────────────────────┴───────────────────────────────┐            │  │
│  │  │                 Read Replicas (2x)                     │            │  │
│  │  │              (para queries de lectura)                 │            │  │
│  │  │              Distribución: 70% read, 30% write         │            │  │
│  │  └───────────────────────────────────────────────────────┘            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    REDIS CLUSTER (Memorystore)                        │  │
│  │                                                                       │  │
│  │  ┌─────────────────┐                  ┌─────────────────┐            │  │
│  │  │   Primary       │◄────Async───────►│   Replica       │            │  │
│  │  │   16GB          │   Replication    │   16GB          │            │  │
│  │  │   Zona A        │                  │   Zona B        │            │  │
│  │  └─────────────────┘                  └─────────────────┘            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  BACKUP:                                                                     │
│  ───────                                                                     │
│  • Automated daily backups (7 días retención)                               │
│  • Point-in-time recovery (PITR) habilitado                                 │
│  • Binary logs: 7 días                                                       │
│  • Cross-region backup: us-central1 (DR)                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 18.2 RTO/RPO

| Métrica | Valor | Descripción |
|:--------|:-----:|:------------|
| **RPO (Recovery Point Objective)** | ~1-5 min | Máxima pérdida de datos aceptable |
| **RTO (Recovery Time Objective)** | <60 seg | Tiempo máximo de downtime |
| **Disponibilidad SLA** | 99.95% | Cloud SQL Enterprise SLA |
| **Downtime anual máximo** | ~4.4 horas | 99.95% uptime |

### 18.3 Costos de Alta Disponibilidad

| Componente | Costo Base | Costo HA | Overhead | Justificación |
|:-----------|:----------:|:--------:|:--------:|:--------------|
| **Cloud SQL Primary** | $1,200/mes | — | — | — |
| **Standby instance** | — | +$600/mes | +50% | Replicación síncrona |
| **Read replicas (2x)** | — | +$480/mes | +40% | Distribución de carga |
| **Cross-region backup** | — | +$120/mes | +10% | Disaster recovery |
| **Redis HA** | $350/mes | +$175/mes | +50% | Replica |
| **TOTAL** | $1,550/mes | **$2,925/mes** | **+89%** | — |

> 💡 **Recomendación:** HA completa para producción. En desarrollo/staging, usar single-instance para reducir costos.

### 18.4 Procedimiento de Failover

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROCEDIMIENTO DE FAILOVER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FAILOVER AUTOMÁTICO (Cloud SQL Enterprise):                                 │
│  ────────────────────────────────────────────                               │
│                                                                              │
│  T+0s:    🔴 Falla detectada en primary                                      │
│                │                                                             │
│  T+10-30s:    │ Cloud SQL detecta heartbeat failure                          │
│                │ (health check cada 1 segundo)                               │
│                ▼                                                             │
│  T+30s:   ⚠️ Decisión de failover iniciada                                   │
│                │                                                             │
│  T+30-50s:    │ Promoción de standby a primary                               │
│                │ • Flush de WAL logs                                         │
│                │ • Actualización de metadata                                  │
│                │ • Verificación de consistencia                               │
│                ▼                                                             │
│  T+50s:   🔄 DNS interno actualizado                                         │
│                │ (automático, no requiere acción)                            │
│                ▼                                                             │
│  T+55s:   🔌 Connection pooler reconecta                                     │
│                │ • Cloud SQL Proxy detecta nueva IP                          │
│                │ • Conexiones re-establecidas                                 │
│                ▼                                                             │
│  T+60s:   ✅ Sistema operativo nuevamente                                    │
│                                                                              │
│  TOTAL: < 60 segundos de downtime                                            │
│                                                                              │
│  ════════════════════════════════════════════════════════════════════════   │
│                                                                              │
│  POST-FAILOVER (manual):                                                     │
│  ───────────────────────                                                    │
│  1. Verificar estado en Cloud Console                                        │
│  2. Revisar logs de failover                                                 │
│  3. Confirmar que read replicas siguen sincronizadas                         │
│  4. Crear nuevo standby (automático en Enterprise)                           │
│  5. Notificar al equipo via PagerDuty/Slack                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Capítulo 19: Observabilidad y Monitoreo

### 19.1 Stack de Observabilidad

| Capa | Herramienta | Propósito | Costo/mes |
|:-----|:------------|:----------|:---------:|
| **Infraestructura** | Cloud Monitoring | CPU, RAM, Disco, Network | Incluido |
| **Base de datos** | Cloud SQL Insights | Query performance, locks, waits | Incluido |
| **Aplicación** | Cloud Trace | Distributed tracing | ~$50 |
| **Logs** | Cloud Logging | Logs centralizados, búsqueda | ~$30 |
| **RAG Quality** | Custom + Prometheus | Métricas de retrieval/generation | ~$20 |
| **LLM Observability** | LangSmith / Helicone | Token usage, latency, traces | ~$100 |
| **Alerting** | Cloud Monitoring + PagerDuty | Alertas y on-call | ~$50 |

### 19.2 Métricas Críticas y Alertas

| Métrica | Threshold Warning | Threshold Critical | Acción | Responsable |
|:--------|:-----------------:|:------------------:|:-------|:------------|
| **Infra: CPU utilization** | >70% | >85% | Scale up | SRE |
| **Infra: Memory utilization** | >75% | >90% | Scale up / investigar | SRE |
| **Infra: Disk usage** | >70% | >85% | Expandir disco | SRE |
| **DB: Query latency p99** | >100ms | >200ms | Investigar queries lentas | DBA |
| **DB: Connection pool** | >80% | >95% | Aumentar pool size | DBA |
| **DB: Replication lag** | >10s | >60s | Investigar / failover | DBA |
| **App: Cache hit rate** | <50% | <30% | Revisar TTL/estrategia | ML Eng |
| **RAG: Retrieval Recall@10** | <85% | <75% | Revisar embeddings/index | ML Eng |
| **RAG: Faithfulness** | <80% | <70% | Revisar prompts/contexto | ML Eng |
| **API: LLM error rate** | >1% | >5% | Revisar prompts/fallback | ML Eng |
| **API: Response time p95** | >2s | >5s | Investigar bottleneck | Dev Team |
| **Business: Queries/min** | <50 | <10 | Investigar issue de entrada | Dev Team |

### 19.3 Dashboards Recomendados

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ESTRUCTURA DE DASHBOARDS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. OPERATIONAL DASHBOARD (SRE/On-Call)                                      │
│  ──────────────────────────────────────                                     │
│  • Latencia por endpoint (p50, p95, p99)                                    │
│  • Error rate por servicio                                                   │
│  • Recursos de infraestructura (CPU, RAM, Disco)                            │
│  • Alertas activas                                                           │
│  • Status de servicios dependientes (APIs, Redis, etc.)                     │
│  • Últimos 10 errores con stack trace                                       │
│                                                                              │
│  Actualización: Real-time (1 segundo)                                        │
│  Usuarios: SRE, On-Call rotation                                             │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  2. RAG QUALITY DASHBOARD (ML Team)                                          │
│  ─────────────────────────────────                                          │
│  • Retrieval metrics (recall, precision, MRR) - trend 7 días               │
│  • Generation metrics (faithfulness, groundedness) - trend 7 días          │
│  • Cache hit rates (L1, L2, total)                                          │
│  • Query patterns y distribución por área                                   │
│  • Latencia de embedding y reranking                                        │
│  • Comparación con golden set (desviación)                                  │
│                                                                              │
│  Actualización: Cada 5 minutos                                               │
│  Usuarios: ML Engineers, Data Scientists                                     │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  3. COST DASHBOARD (Finance/Management)                                      │
│  ─────────────────────────────────────                                      │
│  • Gasto por servicio (Cloud SQL, LLM, embeddings, etc.)                    │
│  • Tendencia de costos (MoM, YoY)                                           │
│  • Cost per query (promedio, por área)                                      │
│  • Proyección mensual basada en trend                                       │
│  • Alertas de anomalías de costos                                           │
│  • Breakdown por área funcional                                             │
│                                                                              │
│  Actualización: Diaria                                                       │
│  Usuarios: Finance, Engineering Management                                   │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  4. BUSINESS DASHBOARD (Stakeholders)                                        │
│  ────────────────────────────────────                                       │
│  • Queries por día/hora (volumen de uso)                                    │
│  • Queries por área funcional (RRHH, Legal, etc.)                           │
│  • User satisfaction (thumbs up/down ratio)                                 │
│  • Top 10 queries más frecuentes                                            │
│  • Áreas sin consultas (gaps de contenido)                                  │
│  • Usuarios únicos por día                                                  │
│                                                                              │
│  Actualización: Cada hora                                                    │
│  Usuarios: Product Management, Stakeholders                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Capítulo 20: Degradación Graceful

Un sistema RAG empresarial debe manejar fallos de componentes de manera elegante, sin impactar completamente la experiencia del usuario.

### 20.1 Fallback por Componente

| Componente | Falla Típica | Fallback | UX Impact | Mensaje Usuario |
|:-----------|:-------------|:---------|:----------|:----------------|
| **pgvector** | Timeout/Down | Cache semántico | Solo respuestas cacheadas | "Resultados limitados..." |
| **Embedding API** | Rate limit | Cola + retry exponencial | Latencia +2-5s | (silencioso) |
| **LLM API** | Sobrecarga | Gemini Flash (más pequeño) | Calidad reducida | "Respuesta resumida..." |
| **Reranker** | Falla/timeout | Skip reranking | Precisión -10-15% | (silencioso) |
| **Redis Cache** | Down | Bypass cache | Latencia +500ms, costo + | (silencioso) |
| **Read Replica** | Down | Redirect a primary | Mayor carga, latencia + | (silencioso) |
| **BM25 index** | Corrupto | Solo vector search | Recall -10% | (silencioso) |

### 20.2 Circuit Breaker Pattern

```python
# circuit_breaker.py - Implementación de Circuit Breaker para servicios RAG

from circuitbreaker import circuit
from typing import Optional, List, Dict, Any
import logging
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, using fallback
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5      # Fallas antes de abrir
    recovery_timeout: int = 60      # Segundos antes de intentar recovery
    success_threshold: int = 3      # Éxitos para cerrar desde half-open

# ============================================================
# CIRCUIT BREAKER PARA VECTOR SEARCH
# ============================================================

@circuit(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception
)
def search_vectors(query_embedding: List[float], area: str, top_k: int = 20) -> List[Dict]:
    """
    Búsqueda vectorial con circuit breaker.
    Si falla 5 veces consecutivas, circuito se abre por 60 segundos.
    """
    try:
        # Llamada normal a pgvector
        results = pgvector_search(query_embedding, area, top_k)
        return results
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise

def search_with_fallback(query_embedding: List[float], area: str, top_k: int = 20) -> Dict:
    """
    Wrapper con fallback a cache semántico.
    """
    try:
        results = search_vectors(query_embedding, area, top_k)
        return {
            "results": results,
            "source": "pgvector",
            "degraded": False
        }
    except Exception as e:
        # Fallback a cache semántico
        logger.warning(f"Falling back to semantic cache: {e}")
        cached_results = semantic_cache.search_similar(query_embedding, top_k)
        
        if cached_results:
            return {
                "results": cached_results,
                "source": "semantic_cache",
                "degraded": True,
                "message": "Resultados desde información previamente consultada"
            }
        else:
            return {
                "results": [],
                "source": "none",
                "degraded": True,
                "message": "Sistema temporalmente limitado"
            }

# ============================================================
# CIRCUIT BREAKER PARA LLM
# ============================================================

@circuit(
    failure_threshold=3,
    recovery_timeout=30,
    expected_exception=Exception
)
def generate_response_primary(prompt: str, context: str) -> str:
    """
    Generación con modelo primario (Gemini Pro).
    """
    return llm_client.generate(
        model="gemini-1.5-pro",
        prompt=prompt,
        context=context
    )

@circuit(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception
)
def generate_response_fallback(prompt: str, context: str) -> str:
    """
    Fallback a modelo más pequeño y rápido (Gemini Flash).
    """
    return llm_client.generate(
        model="gemini-1.5-flash",
        prompt=prompt,
        context=context
    )

def generate_with_fallback(prompt: str, context: str) -> Dict:
    """
    Generación con fallback en cascada.
    """
    # Intento 1: Modelo primario
    try:
        response = generate_response_primary(prompt, context)
        return {
            "response": response,
            "model": "gemini-1.5-pro",
            "degraded": False
        }
    except Exception as e:
        logger.warning(f"Primary LLM failed, trying fallback: {e}")
    
    # Intento 2: Modelo fallback
    try:
        response = generate_response_fallback(prompt, context)
        return {
            "response": response,
            "model": "gemini-1.5-flash",
            "degraded": True,
            "message": "Respuesta usando modelo alternativo"
        }
    except Exception as e:
        logger.error(f"All LLMs failed: {e}")
        return {
            "response": None,
            "model": None,
            "degraded": True,
            "message": "No es posible generar una respuesta en este momento"
        }

# ============================================================
# HEALTH CHECK AGGREGATOR
# ============================================================

def get_system_health() -> Dict[str, Any]:
    """
    Retorna estado de salud de todos los componentes.
    """
    health = {
        "overall": "healthy",
        "components": {},
        "degraded_services": []
    }
    
    components = [
        ("pgvector", search_vectors),
        ("llm_primary", generate_response_primary),
        ("llm_fallback", generate_response_fallback),
    ]
    
    for name, func in components:
        state = getattr(func, '_circuit_state', CircuitState.CLOSED)
        is_healthy = state == CircuitState.CLOSED
        
        health["components"][name] = {
            "state": state.value,
            "healthy": is_healthy
        }
        
        if not is_healthy:
            health["degraded_services"].append(name)
    
    if health["degraded_services"]:
        health["overall"] = "degraded"
    
    return health
```

### 20.3 Mensajes de Degradación para Usuario

| Estado | Código UI | Mensaje | Icono |
|:-------|:----------|:--------|:-----:|
| **Normal** | `normal` | (sin mensaje) | ✅ |
| **Cache hit** | `cached` | "Respuesta desde información previamente consultada" | 💾 |
| **Modelo degraded** | `degraded_llm` | "Estamos experimentando alta demanda. La respuesta puede ser menos detallada." | ⚡ |
| **Búsqueda limitada** | `degraded_search` | "Algunos resultados pueden no estar disponibles temporalmente." | 🔍 |
| **Sistema parcial** | `partial_outage` | "Algunos servicios no están disponibles. Los resultados pueden ser limitados." | ⚠️ |
| **Sistema down** | `full_outage` | "El sistema está temporalmente fuera de servicio. Por favor intente más tarde." | 🔴 |

### 20.4 Cascada de Degradación

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CASCADA DE DEGRADACIÓN                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  NIVEL 0: NORMAL (100% funcionalidad)                                        │
│  ═════════════════════════════════════                                       │
│  • pgvector ✅  • LLM Pro ✅  • Reranker ✅  • Cache ✅                       │
│                                                                              │
│           │ Falla Cache                                                      │
│           ▼                                                                  │
│  NIVEL 1: DEGRADACIÓN LEVE (~95% funcionalidad)                              │
│  ══════════════════════════════════════════════                             │
│  • pgvector ✅  • LLM Pro ✅  • Reranker ✅  • Cache ❌                       │
│  → Latencia +500ms, costo de APIs +30%                                      │
│  → Usuario: no notificado                                                    │
│                                                                              │
│           │ Falla Reranker                                                   │
│           ▼                                                                  │
│  NIVEL 2: DEGRADACIÓN MODERADA (~85% funcionalidad)                          │
│  ════════════════════════════════════════════════                           │
│  • pgvector ✅  • LLM Pro ✅  • Reranker ❌  • Cache ❌                       │
│  → Precisión -15%, latencia +500ms                                          │
│  → Usuario: no notificado (impacto menor)                                   │
│                                                                              │
│           │ Falla LLM Pro                                                    │
│           ▼                                                                  │
│  NIVEL 3: DEGRADACIÓN SIGNIFICATIVA (~70% funcionalidad)                     │
│  ═══════════════════════════════════════════════════════                    │
│  • pgvector ✅  • LLM Flash ⚡  • Reranker ❌  • Cache ❌                     │
│  → Calidad de respuestas reducida                                           │
│  → Usuario: "Alta demanda, respuesta resumida..."                           │
│                                                                              │
│           │ Falla pgvector                                                   │
│           ▼                                                                  │
│  NIVEL 4: MODO EMERGENCIA (~30% funcionalidad)                               │
│  ═════════════════════════════════════════════                              │
│  • pgvector ❌  • LLM Flash ⚡  • Solo cache semántico                       │
│  → Solo queries previamente cacheadas                                       │
│  → Usuario: "Sistema limitado, resultados parciales..."                     │
│                                                                              │
│           │ Falla LLM Flash                                                  │
│           ▼                                                                  │
│  NIVEL 5: SISTEMA DOWN (0% funcionalidad)                                    │
│  ═════════════════════════════════════════                                  │
│  • Todo ❌                                                                   │
│  → Usuario: "Sistema fuera de servicio, intente más tarde..."               │
│  → Alerta crítica a on-call                                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---
---

# ANEXOS

---

## Anexo A: Checklist Pre-Producción

Antes de llevar el sistema RAG a producción, verificar que se cumplan todos los ítems de este checklist.

### A.1 Infraestructura

| # | Item | Estado | Responsable | Notas |
|:-:|:-----|:------:|:------------|:------|
| 1 | Cloud SQL Enterprise provisionado | ☐ | DevOps | db-custom-16-96GB mínimo |
| 2 | pgvector extensión instalada | ☐ | DBA | `CREATE EXTENSION vector;` |
| 3 | Read replicas configuradas (2x) | ☐ | DevOps | Para distribución de carga |
| 4 | Redis cache desplegado (Memorystore) | ☐ | DevOps | 16 GB Standard tier |
| 5 | Backups automáticos habilitados | ☐ | DevOps | 7 días retención, PITR |
| 6 | VPC y Private IP configurado | ☐ | NetOps | Sin exposición pública |
| 7 | Cloud Run/GKE para servicios API | ☐ | DevOps | Autoscaling configurado |
| 8 | SSL/TLS habilitado | ☐ | Security | Conexiones encriptadas |

### A.2 Datos

| # | Item | Estado | Responsable | Notas |
|:-:|:-----|:------:|:------------|:------|
| 9 | Ingestión inicial completada | ☐ | ML Eng | Todos los 17 TB procesados |
| 10 | Embeddings generados | ☐ | ML Eng | 244M vectores |
| 11 | Tabla con halfvec 768d | ☐ | DBA | Verificar tipo `halfvec(768)` |
| 12 | Índices HNSW construidos | ☐ | DBA | Uno por partición |
| 13 | Índices BM25 (tsvector) construidos | ☐ | DBA | Para hybrid search |
| 14 | Particionamiento por área implementado | ☐ | DBA | 6 particiones |
| 15 | Metadata completa (permisos, fechas) | ☐ | ML Eng | Para filtrado |
| 16 | Pipeline CDC configurado | ☐ | Data Eng | Para actualizaciones |

### A.3 Calidad

| # | Item | Estado | Responsable | Notas |
|:-:|:-----|:------:|:------------|:------|
| 17 | Golden set de 200+ queries anotado | ☐ | QA | Con domain experts |
| 18 | Recall@10 > 90% validado | ☐ | ML Eng | En golden set |
| 19 | Faithfulness > 85% validado | ☐ | ML Eng | RAGAS |
| 20 | Groundedness > 90% validado | ☐ | ML Eng | Sin alucinaciones |
| 21 | Latencia p95 < 2s validada | ☐ | QA | End-to-end |
| 22 | Test de carga (100 QPS) pasado | ☐ | QA | Sin degradación |

### A.4 Observabilidad

| # | Item | Estado | Responsable | Notas |
|:-:|:-----|:------:|:------------|:------|
| 23 | Dashboards configurados (4) | ☐ | SRE | Ops, RAG, Cost, Business |
| 24 | Alertas configuradas | ☐ | SRE | Warning + Critical |
| 25 | Logging habilitado | ☐ | DevOps | Cloud Logging |
| 26 | Tracing habilitado | ☐ | DevOps | Cloud Trace |
| 27 | LLM observability (LangSmith) | ☐ | ML Eng | Token usage, traces |

### A.5 Operacional

| # | Item | Estado | Responsable | Notas |
|:-:|:-----|:------:|:------------|:------|
| 28 | Runbooks documentados | ☐ | SRE | Para incidentes comunes |
| 29 | Pipeline de actualización probado | ☐ | Data Eng | CDC funcional |
| 30 | Procedimiento de rollback definido | ☐ | DevOps | Versionado |
| 31 | On-call rotation definida | ☐ | SRE | PagerDuty configurado |
| 32 | SLIs/SLOs definidos | ☐ | SRE | Latencia, disponibilidad |
| 33 | Escalation paths documentados | ☐ | Management | Para P1/P2 |

### A.6 Seguridad

| # | Item | Estado | Responsable | Notas |
|:-:|:-----|:------:|:------------|:------|
| 34 | IAM roles revisados (least privilege) | ☐ | Security | Solo acceso necesario |
| 35 | Encryption at rest verificado | ☐ | Security | Cloud SQL default |
| 36 | Encryption in transit verificado | ☐ | Security | TLS 1.3 |
| 37 | Network policies aplicadas | ☐ | NetOps | VPC Service Controls |
| 38 | Audit logging habilitado | ☐ | Security | Cloud Audit Logs |
| 39 | Data Loss Prevention (DLP) | ☐ | Security | Para PII en respuestas |
| 40 | Penetration test completado | ☐ | Security | Si aplica |

---

## Anexo B: Configuraciones SQL Recomendadas

### B.1 Creación de Tabla con halfvec

```sql
-- ============================================================
-- CREACIÓN DE TABLA PRINCIPAL CON HALFVEC Y PARTICIONAMIENTO
-- ============================================================

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Para búsquedas de texto

-- Crear tabla particionada por área
CREATE TABLE embeddings (
    id UUID DEFAULT gen_random_uuid(),
    
    -- Vector embedding (halfvec = float16, 768 dimensiones Matryoshka)
    embedding halfvec(768) NOT NULL,
    
    -- Contenido y metadata
    content TEXT NOT NULL,
    content_tokens INTEGER,
    
    -- Búsqueda full-text (BM25)
    content_tsv tsvector GENERATED ALWAYS AS (
        to_tsvector('spanish', content)
    ) STORED,
    
    -- Metadata del documento
    document_id UUID NOT NULL,
    document_title TEXT,
    document_path TEXT,
    chunk_index INTEGER,
    
    -- Clasificación
    area TEXT NOT NULL,  -- 'rrhh', 'legal', 'finanzas', etc.
    document_type TEXT,  -- 'politica', 'contrato', 'manual', etc.
    
    -- Permisos y fechas
    access_level TEXT DEFAULT 'internal',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,  -- Soft delete
    
    -- Constraints
    PRIMARY KEY (id, area)
    
) PARTITION BY LIST (area);

-- Crear particiones por área
CREATE TABLE embeddings_rrhh PARTITION OF embeddings FOR VALUES IN ('rrhh');
CREATE TABLE embeddings_legal PARTITION OF embeddings FOR VALUES IN ('legal');
CREATE TABLE embeddings_finanzas PARTITION OF embeddings FOR VALUES IN ('finanzas');
CREATE TABLE embeddings_operaciones PARTITION OF embeddings FOR VALUES IN ('operaciones');
CREATE TABLE embeddings_call_center PARTITION OF embeddings FOR VALUES IN ('call_center');
CREATE TABLE embeddings_general PARTITION OF embeddings FOR VALUES IN ('general');
```

### B.2 Creación de Índices HNSW

```sql
-- ============================================================
-- ÍNDICES HNSW POR PARTICIÓN
-- ============================================================

-- Parámetros HNSW:
-- m = 16: Número de conexiones por nodo (balance calidad/velocidad)
-- ef_construction = 64: Calidad de construcción (más alto = mejor pero más lento)

-- Índice para cada partición (permite partition pruning)
CREATE INDEX idx_embeddings_rrhh_hnsw ON embeddings_rrhh 
    USING hnsw (embedding halfvec_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_embeddings_legal_hnsw ON embeddings_legal 
    USING hnsw (embedding halfvec_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_embeddings_finanzas_hnsw ON embeddings_finanzas 
    USING hnsw (embedding halfvec_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_embeddings_operaciones_hnsw ON embeddings_operaciones 
    USING hnsw (embedding halfvec_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_embeddings_call_center_hnsw ON embeddings_call_center 
    USING hnsw (embedding halfvec_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_embeddings_general_hnsw ON embeddings_general 
    USING hnsw (embedding halfvec_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================
-- ÍNDICES BM25 (FULL-TEXT) PARA BÚSQUEDA HÍBRIDA
-- ============================================================

CREATE INDEX idx_embeddings_rrhh_fts ON embeddings_rrhh USING GIN (content_tsv);
CREATE INDEX idx_embeddings_legal_fts ON embeddings_legal USING GIN (content_tsv);
CREATE INDEX idx_embeddings_finanzas_fts ON embeddings_finanzas USING GIN (content_tsv);
CREATE INDEX idx_embeddings_operaciones_fts ON embeddings_operaciones USING GIN (content_tsv);
CREATE INDEX idx_embeddings_call_center_fts ON embeddings_call_center USING GIN (content_tsv);
CREATE INDEX idx_embeddings_general_fts ON embeddings_general USING GIN (content_tsv);

-- ============================================================
-- ÍNDICES ADICIONALES PARA FILTRADO
-- ============================================================

CREATE INDEX idx_embeddings_document_id ON embeddings (document_id);
CREATE INDEX idx_embeddings_created_at ON embeddings (created_at);
CREATE INDEX idx_embeddings_deleted_at ON embeddings (deleted_at) WHERE deleted_at IS NULL;
```

### B.3 Búsqueda Híbrida con RRF

```sql
-- ============================================================
-- FUNCIÓN DE BÚSQUEDA HÍBRIDA (VECTOR + BM25 + RRF)
-- ============================================================

CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding halfvec(768),
    query_text TEXT,
    search_area TEXT DEFAULT NULL,
    top_k INTEGER DEFAULT 20,
    vector_weight FLOAT DEFAULT 0.7,
    bm25_weight FLOAT DEFAULT 0.3,
    rrf_k INTEGER DEFAULT 60
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    document_title TEXT,
    document_path TEXT,
    area TEXT,
    vector_score FLOAT,
    bm25_score FLOAT,
    rrf_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH 
    -- Búsqueda vectorial (cosine similarity)
    vector_results AS (
        SELECT 
            e.id,
            e.content,
            e.document_title,
            e.document_path,
            e.area,
            1 - (e.embedding <=> query_embedding) AS score,
            ROW_NUMBER() OVER (ORDER BY e.embedding <=> query_embedding) AS rank
        FROM embeddings e
        WHERE 
            (search_area IS NULL OR e.area = search_area)
            AND e.deleted_at IS NULL
        ORDER BY e.embedding <=> query_embedding
        LIMIT top_k * 2
    ),
    
    -- Búsqueda BM25 (full-text)
    bm25_results AS (
        SELECT 
            e.id,
            e.content,
            e.document_title,
            e.document_path,
            e.area,
            ts_rank_cd(e.content_tsv, plainto_tsquery('spanish', query_text)) AS score,
            ROW_NUMBER() OVER (
                ORDER BY ts_rank_cd(e.content_tsv, plainto_tsquery('spanish', query_text)) DESC
            ) AS rank
        FROM embeddings e
        WHERE 
            e.content_tsv @@ plainto_tsquery('spanish', query_text)
            AND (search_area IS NULL OR e.area = search_area)
            AND e.deleted_at IS NULL
        ORDER BY ts_rank_cd(e.content_tsv, plainto_tsquery('spanish', query_text)) DESC
        LIMIT top_k * 2
    ),
    
    -- Fusión con Reciprocal Rank Fusion (RRF)
    combined AS (
        SELECT 
            COALESCE(v.id, b.id) AS id,
            COALESCE(v.content, b.content) AS content,
            COALESCE(v.document_title, b.document_title) AS document_title,
            COALESCE(v.document_path, b.document_path) AS document_path,
            COALESCE(v.area, b.area) AS area,
            COALESCE(v.score, 0) AS vector_score,
            COALESCE(b.score, 0) AS bm25_score,
            -- RRF: score = sum(1 / (k + rank))
            (
                CASE WHEN v.rank IS NOT NULL 
                     THEN vector_weight * (1.0 / (rrf_k + v.rank)) 
                     ELSE 0 
                END
            ) + (
                CASE WHEN b.rank IS NOT NULL 
                     THEN bm25_weight * (1.0 / (rrf_k + b.rank)) 
                     ELSE 0 
                END
            ) AS rrf_score
        FROM vector_results v
        FULL OUTER JOIN bm25_results b ON v.id = b.id
    )
    
    SELECT 
        c.id,
        c.content,
        c.document_title,
        c.document_path,
        c.area,
        c.vector_score::FLOAT,
        c.bm25_score::FLOAT,
        c.rrf_score::FLOAT
    FROM combined c
    ORDER BY c.rrf_score DESC
    LIMIT top_k;
END;
$$;

-- ============================================================
-- EJEMPLO DE USO
-- ============================================================

-- Búsqueda híbrida en área específica
SELECT * FROM hybrid_search(
    query_embedding := '[0.1, 0.2, ...]'::halfvec(768),  -- Embedding de la query
    query_text := '¿cuántos días de vacaciones tengo?',
    search_area := 'rrhh',
    top_k := 10
);

-- Búsqueda híbrida en todas las áreas
SELECT * FROM hybrid_search(
    query_embedding := '[0.1, 0.2, ...]'::halfvec(768),
    query_text := 'política de trabajo remoto',
    search_area := NULL,  -- Todas las áreas
    top_k := 20,
    vector_weight := 0.6,
    bm25_weight := 0.4
);
```

### B.4 Configuración de PostgreSQL para pgvector

```sql
-- ============================================================
-- CONFIGURACIÓN DE POSTGRESQL PARA PGVECTOR (postgresql.conf)
-- ============================================================

-- Memoria para búsquedas HNSW
-- ef_search: calidad de búsqueda (mayor = mejor recall pero más lento)
SET hnsw.ef_search = 100;  -- Default: 40, recomendado: 100-200

-- Trabajo de índice
SET maintenance_work_mem = '4GB';  -- Para construcción de índices

-- Paralelismo
SET max_parallel_workers_per_gather = 4;
SET max_parallel_workers = 8;

-- Buffer pool (30% de RAM disponible)
SET shared_buffers = '24GB';  -- Para 80 GB RAM total

-- Work memory por query
SET work_mem = '256MB';

-- Estadísticas
SET default_statistics_target = 500;
```

---

## Anexo C: Código de Referencia

### C.1 Pipeline de Chunking Adaptativo (Python)

```python
# chunking_pipeline.py - Pipeline de chunking adaptativo por tipo de documento

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import re

class DocumentType(Enum):
    LEGAL = "legal"
    TECHNICAL = "technical"
    FAQ = "faq"
    POLICY = "policy"
    GENERAL = "general"

@dataclass
class ChunkConfig:
    """Configuración de chunking por tipo de documento."""
    chunk_size: int
    overlap: int
    strategy: str
    description: str

# Configuraciones por tipo de documento
CHUNK_CONFIGS: Dict[DocumentType, ChunkConfig] = {
    DocumentType.LEGAL: ChunkConfig(
        chunk_size=1024,
        overlap=256,  # 25% overlap
        strategy="agentic",
        description="Documentos legales - mayor overlap para preservar contexto"
    ),
    DocumentType.TECHNICAL: ChunkConfig(
        chunk_size=1024,
        overlap=150,  # 15% overlap
        strategy="recursive",
        description="Manuales técnicos - balance costo/calidad"
    ),
    DocumentType.FAQ: ChunkConfig(
        chunk_size=512,
        overlap=0,  # Sin overlap
        strategy="sentence",
        description="FAQs - cada Q&A es una unidad independiente"
    ),
    DocumentType.POLICY: ChunkConfig(
        chunk_size=768,
        overlap=100,  # ~13% overlap
        strategy="recursive",
        description="Políticas - chunks medianos"
    ),
    DocumentType.GENERAL: ChunkConfig(
        chunk_size=512,
        overlap=75,  # ~15% overlap
        strategy="recursive",
        description="Documentos generales - configuración estándar"
    ),
}

class AdaptiveChunker:
    """
    Chunker adaptativo que selecciona estrategia según tipo de documento.
    """
    
    def __init__(self):
        self.separators = ["\n\n", "\n", ". ", " ", ""]
    
    def detect_document_type(self, content: str, metadata: Dict) -> DocumentType:
        """
        Detecta el tipo de documento basado en contenido y metadata.
        """
        # Reglas basadas en metadata
        doc_type = metadata.get("document_type", "").lower()
        area = metadata.get("area", "").lower()
        
        if "contrato" in doc_type or area == "legal":
            return DocumentType.LEGAL
        elif "manual" in doc_type or "técnico" in doc_type.lower():
            return DocumentType.TECHNICAL
        elif "faq" in doc_type or "preguntas" in doc_type:
            return DocumentType.FAQ
        elif "política" in doc_type or "procedimiento" in doc_type:
            return DocumentType.POLICY
        
        # Reglas basadas en contenido
        if re.search(r'artículo \d+|cláusula', content.lower()):
            return DocumentType.LEGAL
        
        return DocumentType.GENERAL
    
    def chunk_document(
        self, 
        content: str, 
        metadata: Dict,
        force_type: Optional[DocumentType] = None
    ) -> List[Dict]:
        """
        Divide un documento en chunks según su tipo detectado.
        
        Returns:
            Lista de dicts con 'content', 'chunk_index', 'config'
        """
        doc_type = force_type or self.detect_document_type(content, metadata)
        config = CHUNK_CONFIGS[doc_type]
        
        if config.strategy == "sentence":
            chunks = self._sentence_chunk(content, config)
        elif config.strategy == "agentic":
            chunks = self._agentic_chunk(content, config)
        else:
            chunks = self._recursive_chunk(content, config)
        
        return [
            {
                "content": chunk,
                "chunk_index": i,
                "chunk_size": len(chunk),
                "document_type": doc_type.value,
                "config": {
                    "strategy": config.strategy,
                    "target_size": config.chunk_size,
                    "overlap": config.overlap
                }
            }
            for i, chunk in enumerate(chunks)
        ]
    
    def _recursive_chunk(self, text: str, config: ChunkConfig) -> List[str]:
        """Chunking recursivo con separadores jerárquicos."""
        chunks = []
        self._split_recursive(
            text, 
            config.chunk_size, 
            config.overlap, 
            self.separators, 
            chunks
        )
        return chunks
    
    def _split_recursive(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: int,
        separators: List[str], 
        chunks: List[str]
    ):
        """Helper recursivo para chunking."""
        if len(text) <= chunk_size:
            if text.strip():
                chunks.append(text.strip())
            return
        
        separator = separators[0] if separators else ""
        parts = text.split(separator) if separator else list(text)
        
        current_chunk = ""
        for part in parts:
            test_chunk = current_chunk + separator + part if current_chunk else part
            
            if len(test_chunk) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Overlap: comenzar el siguiente chunk con parte del anterior
                    if overlap > 0:
                        current_chunk = current_chunk[-overlap:] + separator + part
                    else:
                        current_chunk = part
                else:
                    # Parte muy larga, intentar con siguiente separador
                    if len(separators) > 1:
                        self._split_recursive(
                            part, chunk_size, overlap, separators[1:], chunks
                        )
                        current_chunk = ""
                    else:
                        # Último recurso: cortar por caracteres
                        for i in range(0, len(part), chunk_size - overlap):
                            chunks.append(part[i:i + chunk_size])
                        current_chunk = ""
            else:
                current_chunk = test_chunk
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
    
    def _sentence_chunk(self, text: str, config: ChunkConfig) -> List[str]:
        """Chunking por oraciones completas."""
        import nltk
        nltk.download('punkt', quiet=True)
        from nltk.tokenize import sent_tokenize
        
        sentences = sent_tokenize(text, language='spanish')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= config.chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _agentic_chunk(self, text: str, config: ChunkConfig) -> List[str]:
        """
        Chunking usando LLM para identificar boundaries semánticos.
        (Versión simplificada - en producción usar Gemini)
        """
        # Para producción: llamar a Gemini para identificar boundaries
        # Aquí usamos recursive como fallback
        return self._recursive_chunk(text, config)
```

### C.2 Semantic Cache con Redis (Python)

```python
# semantic_cache.py - Cache semántico multi-nivel con Redis

import redis
import json
import hashlib
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import time

@dataclass
class CacheConfig:
    """Configuración del cache semántico."""
    # TTLs por tipo de cache
    exact_ttl: int = 86400  # 24 horas
    semantic_ttl: int = 3600  # 1 hora
    embedding_ttl: int = 604800  # 7 días
    
    # Thresholds
    similarity_threshold: float = 0.95  # Para cache hit semántico
    
    # Configuración Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Prefijos de keys
    exact_prefix: str = "rag:exact:"
    semantic_prefix: str = "rag:semantic:"
    embedding_prefix: str = "rag:emb:"

class SemanticCache:
    """
    Cache semántico multi-nivel para sistema RAG.
    
    Niveles:
    1. L1 (Exact Match): Hash de la query exacta
    2. L2 (Semantic): Búsqueda por similitud de embedding
    3. L3 (Embedding): Cache de embeddings calculados
    """
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.redis = redis.Redis(
            host=self.config.redis_host,
            port=self.config.redis_port,
            db=self.config.redis_db,
            decode_responses=False  # Para manejar binarios
        )
        
        # Métricas
        self.stats = {
            "exact_hits": 0,
            "semantic_hits": 0,
            "misses": 0,
            "embedding_hits": 0
        }
    
    def _hash_query(self, query: str) -> str:
        """Genera hash de la query para exact match."""
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def _serialize_embedding(self, embedding: List[float]) -> bytes:
        """Serializa embedding a bytes."""
        return np.array(embedding, dtype=np.float16).tobytes()
    
    def _deserialize_embedding(self, data: bytes) -> List[float]:
        """Deserializa bytes a embedding."""
        return np.frombuffer(data, dtype=np.float16).tolist()
    
    # ============================================================
    # L1: EXACT MATCH CACHE
    # ============================================================
    
    def get_exact(self, query: str, area: str = None) -> Optional[Dict]:
        """
        Busca respuesta cacheada por match exacto.
        
        Returns:
            Dict con 'response', 'contexts', 'cached_at' o None
        """
        key = f"{self.config.exact_prefix}{area or 'all'}:{self._hash_query(query)}"
        
        data = self.redis.get(key)
        if data:
            self.stats["exact_hits"] += 1
            return json.loads(data)
        return None
    
    def set_exact(
        self, 
        query: str, 
        response: str, 
        contexts: List[str],
        area: str = None
    ):
        """Guarda respuesta en cache exact match."""
        key = f"{self.config.exact_prefix}{area or 'all'}:{self._hash_query(query)}"
        
        data = {
            "response": response,
            "contexts": contexts,
            "cached_at": time.time(),
            "cache_type": "exact"
        }
        
        self.redis.setex(
            key, 
            self.config.exact_ttl, 
            json.dumps(data)
        )
    
    # ============================================================
    # L2: SEMANTIC SIMILARITY CACHE
    # ============================================================
    
    def get_semantic(
        self, 
        query_embedding: List[float], 
        area: str = None,
        threshold: float = None
    ) -> Optional[Dict]:
        """
        Busca respuesta cacheada por similitud semántica.
        
        Usa Redis como vector store simple para los embeddings cacheados.
        En producción, considerar RediSearch con vector similarity.
        """
        threshold = threshold or self.config.similarity_threshold
        pattern = f"{self.config.semantic_prefix}{area or 'all'}:*"
        
        best_match = None
        best_similarity = 0
        
        # Buscar en embeddings cacheados
        for key in self.redis.scan_iter(match=pattern, count=100):
            data = self.redis.get(key)
            if data:
                cached = json.loads(data)
                cached_emb = self._deserialize_embedding(
                    bytes.fromhex(cached["embedding_hex"])
                )
                
                # Calcular cosine similarity
                similarity = self._cosine_similarity(query_embedding, cached_emb)
                
                if similarity > best_similarity and similarity >= threshold:
                    best_similarity = similarity
                    best_match = cached
        
        if best_match:
            self.stats["semantic_hits"] += 1
            return {
                "response": best_match["response"],
                "contexts": best_match["contexts"],
                "cached_at": best_match["cached_at"],
                "similarity": best_similarity,
                "cache_type": "semantic"
            }
        
        return None
    
    def set_semantic(
        self, 
        query_embedding: List[float],
        response: str, 
        contexts: List[str],
        area: str = None
    ):
        """Guarda respuesta en cache semántico."""
        # Usar hash del embedding como key
        emb_bytes = self._serialize_embedding(query_embedding)
        emb_hash = hashlib.sha256(emb_bytes).hexdigest()[:16]
        
        key = f"{self.config.semantic_prefix}{area or 'all'}:{emb_hash}"
        
        data = {
            "embedding_hex": emb_bytes.hex(),
            "response": response,
            "contexts": contexts,
            "cached_at": time.time()
        }
        
        self.redis.setex(
            key, 
            self.config.semantic_ttl, 
            json.dumps(data)
        )
    
    # ============================================================
    # L3: EMBEDDING CACHE
    # ============================================================
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Obtiene embedding cacheado de un texto."""
        key = f"{self.config.embedding_prefix}{self._hash_query(text)}"
        
        data = self.redis.get(key)
        if data:
            self.stats["embedding_hits"] += 1
            return self._deserialize_embedding(data)
        return None
    
    def set_embedding(self, text: str, embedding: List[float]):
        """Cachea embedding de un texto."""
        key = f"{self.config.embedding_prefix}{self._hash_query(text)}"
        
        self.redis.setex(
            key,
            self.config.embedding_ttl,
            self._serialize_embedding(embedding)
        )
    
    # ============================================================
    # UTILIDADES
    # ============================================================
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calcula similitud coseno entre dos vectores."""
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del cache."""
        total = sum(self.stats.values())
        return {
            **self.stats,
            "total_requests": total,
            "hit_rate": (
                (self.stats["exact_hits"] + self.stats["semantic_hits"]) / total 
                if total > 0 else 0
            )
        }
    
    def clear_area(self, area: str):
        """Limpia cache de un área específica."""
        patterns = [
            f"{self.config.exact_prefix}{area}:*",
            f"{self.config.semantic_prefix}{area}:*"
        ]
        for pattern in patterns:
            for key in self.redis.scan_iter(match=pattern):
                self.redis.delete(key)
```

---

## Anexo D: Referencias y Fuentes

### D.1 Papers Académicos

| Paper | Año | Tema | URL |
|:------|:---:|:-----|:----|
| Matryoshka Representation Learning | 2022 | Embeddings anidados | https://arxiv.org/abs/2205.13147 |
| ColBERT: Efficient and Effective Passage Search | 2020 | Late Interaction | https://arxiv.org/abs/2004.12832 |
| HyDE: Hypothetical Document Embeddings | 2022 | Query expansion | https://arxiv.org/abs/2212.10496 |
| Late Chunking | 2024 | Chunking mejorado | https://arxiv.org/abs/2409.04701 |
| HNSW: Hierarchical NSW Graphs | 2016 | Índices aproximados | https://arxiv.org/abs/1603.09320 |
| Cohere Rerank | 2023 | Cross-encoder reranking | https://txt.cohere.com/rerank/ |
| RAGAS | 2023 | Evaluación de RAG | https://arxiv.org/abs/2309.15217 |

### D.2 Documentación Oficial

| Recurso | Descripción | URL |
|:--------|:------------|:----|
| pgvector | Extensión vectorial PostgreSQL | https://github.com/pgvector/pgvector |
| Cloud SQL | Base de datos managed GCP | https://cloud.google.com/sql/docs |
| Gemini Embeddings | API de embeddings | https://cloud.google.com/vertex-ai/docs/generative-ai/embeddings |
| LangChain | Framework RAG | https://python.langchain.com/ |
| RAGAS | Evaluación automatizada | https://docs.ragas.io/ |
| Redis | Cache distribuido | https://redis.io/docs/ |

### D.3 Benchmarks y Comparativas

| Benchmark | Descripción | URL |
|:----------|:------------|:----|
| MTEB Leaderboard | Benchmark de embeddings | https://huggingface.co/spaces/mteb/leaderboard |
| Pinecone Benchmarks | Comparativa de VectorDBs | https://www.pinecone.io/learn/vector-database-benchmark/ |
| ANN Benchmarks | Benchmark de índices ANN | https://ann-benchmarks.com/ |
| Qdrant Benchmarks | Performance vectorial | https://qdrant.tech/benchmarks/ |

---

## Anexo E: Glosario de Términos

| Término | Definición |
|:--------|:-----------|
| **ANN** | Approximate Nearest Neighbors - Algoritmo para búsqueda aproximada de vecinos más cercanos |
| **BM25** | Best Matching 25 - Algoritmo de ranking para búsqueda de texto |
| **CDC** | Change Data Capture - Técnica para detectar cambios en datos |
| **Chunk** | Fragmento de texto que se convierte en un vector |
| **Cosine Similarity** | Medida de similitud entre vectores basada en el ángulo |
| **Cross-Encoder** | Modelo que procesa query y documento juntos para scoring |
| **Embedding** | Representación numérica (vector) de texto |
| **ef_search** | Parámetro HNSW que controla calidad vs. velocidad |
| **Faithfulness** | Métrica que mide si la respuesta es fiel al contexto |
| **Groundedness** | Métrica que mide si la respuesta evita alucinaciones |
| **halfvec** | Tipo de dato pgvector con precisión float16 |
| **HNSW** | Hierarchical Navigable Small World - Algoritmo de índice ANN |
| **HyDE** | Hypothetical Document Embeddings - Técnica de query expansion |
| **Late Interaction** | Arquitectura donde query y doc se procesan por separado |
| **Matryoshka** | Técnica de embeddings que permite truncar dimensiones |
| **MRR** | Mean Reciprocal Rank - Métrica de calidad de ranking |
| **nDCG** | Normalized Discounted Cumulative Gain - Métrica de ranking |
| **Overlap** | Solapamiento entre chunks consecutivos |
| **Partition Pruning** | Optimización que evita escanear particiones innecesarias |
| **pgvector** | Extensión de PostgreSQL para búsqueda vectorial |
| **RAG** | Retrieval-Augmented Generation - Patrón de generación con contexto |
| **RAGAS** | Framework de evaluación de sistemas RAG |
| **Recall@K** | Proporción de docs relevantes en top K resultados |
| **Reranking** | Re-ordenamiento de resultados con modelo más preciso |
| **RRF** | Reciprocal Rank Fusion - Algoritmo para fusionar rankings |
| **RPO** | Recovery Point Objective - Pérdida de datos aceptable |
| **RTO** | Recovery Time Objective - Tiempo de downtime aceptable |
| **Semantic Cache** | Cache basado en similitud semántica |
| **TCO** | Total Cost of Ownership - Costo total de propiedad |
| **tsvector** | Tipo de dato PostgreSQL para búsqueda full-text |
| **Vector Database** | Base de datos optimizada para búsqueda vectorial |

---
---

# 📊 RESUMEN DEL DOCUMENTO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RESUMEN FINAL DEL DOCUMENTO                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  📄 ESTRUCTURA                                                               │
│  ─────────────                                                               │
│  • Secciones: 6 (I-VI) + Anexos                                             │
│  • Capítulos: 20                                                             │
│  • Anexos: 5 (A-E)                                                           │
│                                                                              │
│  📊 CONTENIDO                                                                │
│  ────────────                                                                │
│  • Tablas: ~75                                                               │
│  • Diagramas ASCII: ~35                                                      │
│  • Bloques de código: ~25 (SQL + Python)                                    │
│  • Fórmulas matemáticas: ~30                                                 │
│                                                                              │
│  📏 EXTENSIÓN                                                                │
│  ───────────                                                                 │
│  • Líneas: ~5,400                                                            │
│  • Palabras: ~45,000                                                         │
│  • Páginas estimadas: ~120 (A4)                                              │
│                                                                              │
│  ✅ COBERTURA                                                                 │
│  ────────────                                                                │
│  • 100% del contenido del BLUEPRINT fuente incluido                         │
│  • Reorganizado en estructura jerárquica                                    │
│  • Ampliado con código de producción                                        │
│  • Agregados diagramas y tablas adicionales                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---
---

<div align="center">

## 📋 CONTROL DEL DOCUMENTO

| Campo | Valor |
|:------|:------|
| **Título** | Arquitectura de Base de Datos Vectorial para Sistema RAG Empresarial |
| **Versión** | 3.0 |
| **Estado** | ✅ Versión Final |
| **Fecha de Generación** | 2026-01-27 |
| **Próxima Revisión** | 2026-04-27 (3 meses) |
| **Clasificación** | 🔒 Documento Técnico Interno |
| **Distribución** | Arquitectura, ML/AI, DevOps, SRE, Stakeholders |

---

### Control de Versiones

| Versión | Fecha | Autor | Cambios |
|:-------:|:-----:|:------|:--------|
| 1.0 | 2025-11 | Equipo Arquitectura | Documento inicial |
| 2.0 | 2025-12 | Equipo Arquitectura | Agregado análisis de costos |
| 3.0 | 2026-01 | Equipo Arquitectura | Versión completa con anexos |

---

### Aprobaciones

| Rol | Nombre | Fecha | Firma |
|:----|:-------|:-----:|:-----:|
| Arquitecto Principal | ______________ | ___/___/___ | ☐ |
| Tech Lead ML/AI | ______________ | ___/___/___ | ☐ |
| Director de Ingeniería | ______________ | ___/___/___ | ☐ |

---

**© 2026 Enterprise AI Platform - Documento Confidencial**

</div>
