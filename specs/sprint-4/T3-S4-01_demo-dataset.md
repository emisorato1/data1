# T3-S4-01: Carga masiva dataset demo via Airflow

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T4-S4-02 (demo flow) |
| Depende de | T3-S2-03 |
| Skill | `rag-indexing/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

Datos bancarios de demo indexados a traves del pipeline Airflow. Sin datos reales indexados, no hay demo posible. Los documentos deben ser variados para demostrar las capacidades del sistema.

El DAG debe soportar **carga masiva**: recibe una carpeta como parametro y procesa todos los documentos contenidos en ella de forma batch, permitiendo reutilizar el mismo DAG para distintos conjuntos de datos (demo, fixtures, futuros datasets reales).

## Spec

Preparar 10-20 documentos bancarios publicos en `data/demo/`, crear un DAG de carga masiva que indexe **todos los documentos de una carpeta dada** via Airflow, ejecutarlo contra la carpeta demo, y verificar que las queries retornan resultados relevantes.

## Acceptance Criteria

- [x] 10-20 documentos bancarios preparados en `tests/data/demo/` (18 documentos: 7 PDFs RRHH + 11 DOCX productos bancarios)
- [x] Variedad: documentos con tablas, texto denso, multiples paginas (PDF + DOCX, RRHH + Paquetes + Prestamos + Cajas de Seguridad)
- [x] DAG de Airflow `load_demo_data` que indexa en batch todos los documentos de una carpeta configurable (default: `data/demo/`)
- [x] DAG configurado para auto-trigger al iniciar el contenedor Airflow (via docker-compose)
- [x] Verificacion: queries de ejemplo retornan resultados relevantes (ejecutar `scripts/verify_demo_data.py` post-indexacion)
- [x] Metricas documentadas: cantidad de chunks, distribucion de tamanos, duracion del DAG (capturar output de `report_results` task)

## Archivos a crear/modificar

- `tests/data/demo/` (creado — 18 documentos bancarios internos: RRHH, Paquetes, Prestamos Personales, Cajas de Seguridad)
- `dags/indexing/load_demo_data.py` (creado — DAG de carga masiva parametrizable por carpeta)
- `scripts/verify_demo_data.py` (creado — queries de verificacion alineadas con documentos reales)
- `docker-compose.yml` (modificado — auto-trigger del DAG al iniciar Airflow)

## Decisiones de diseno

- **DAG parametrizable por carpeta**: el DAG recibe la ruta de la carpeta origen como parametro (default `data/demo/`). Esto permite reutilizarlo para cargar cualquier conjunto de documentos, incluyendo `tests/fixtures/` durante desarrollo/testing
- Documentos publicos: evita problemas de confidencialidad, disponibles para cualquier entorno
- Variedad de formatos: demuestra que el pipeline maneja distintos tipos de contenido
- DAG separado de rag_indexing: logica batch especifica, no poluciona el DAG principal

## Relacion con `tests/fixtures/`

Los fixtures existentes (`tests/fixtures/`) tienen un proposito distinto al demo dataset:

| Aspecto | `tests/fixtures/` | `data/demo/` |
|---------|-------------------|--------------|
| Proposito | Unit/integration tests | Demostracion end-to-end |
| Contenido | Archivos genericos, casos edge | Documentos bancarios realistas |
| Tamano | Minimo (velocidad de tests) | Representativo (calidad de demo) |

Sin embargo, al ser el DAG parametrizable por carpeta, se puede ejecutar contra `tests/fixtures/` para validar el pipeline durante desarrollo sin necesidad de los documentos de demo completos.

**Recomendacion futura**: una vez creados los documentos de demo bancarios, evaluar reemplazar los fixtures genericos (`sample.pdf`, `sample.docx`) por versiones con contenido bancario que sirvan para ambos propositos (tests + smoke test rapido del pipeline).

## Verificacion de queries

El script `scripts/verify_demo_data.py` ejecuta 10 queries de ejemplo contra la base de datos post-indexacion y verifica que los resultados sean relevantes:

| # | Query | Pattern esperado | Documento target |
|---|-------|-----------------|------------------|
| 1 | Medidas de cajas de seguridad | CS001 | CS001 - Manual del producto.docx |
| 2 | Que es un paquete de productos | PAQ001 | PAQ001 - Manual del producto.docx |
| 3 | Solicitar baja de paquete | baja de paquete | PAQ002 - Solicitud de baja de paquete.docx |
| 4 | Retener cliente que cancela paquete | Retenci | PAQ003 - Retencion de paquetes.docx |
| 5 | Alta de paquete en Cobis | Alta de Paquete | PAQ005 - Alta de Paquete.docx |
| 6 | Upgrade de paquete | Upgrade de Paquete | PAQ006 - Upgrade de Paquete.docx |
| 7 | Requisitos prestamo hipotecario UVA | PP001 | PP001 - Manual del producto.docx |
| 8 | Otorgamiento prestamo Contact Center | Otorgamiento | PP002 - Otorgamiento de prestamo personal.docx |
| 9 | Pago cuota prestamo por CRM | Pago de cuota | PP003 - Pago de cuota por CRM.docx |
| 10 | Denunciar accidente de trabajo | Salud | 008 RRHH - Salud, Prevencion y Medio Ambiente.pdf |

Uso: `python scripts/verify_demo_data.py [--db-url URL] [--queries-only] [--json]`

Exit codes: 0 = todas las queries matchean, 1 = alguna falla, 2 = error de ejecucion.

## Metricas de referencia

El task `report_results` del DAG genera automaticamente las siguientes metricas al finalizar la carga batch:

| Metrica | Descripcion | Valor esperado (18 docs) |
|---------|-------------|--------------------------|
| Documents indexed | Documentos procesados exitosamente | 18 |
| Documents failed | Documentos con error de indexacion | 0 |
| Total chunks | Chunks generados (4KB, 15% overlap) | ~200-400 (depende del contenido) |
| Total tokens | Tokens totales en todos los chunks | ~100K-200K |
| Duration | Tiempo total del batch | ~2-10 min (depende de rate limits Gemini) |
| Chunk size min | Chunk mas pequeno (tokens) | ~50-100 |
| Chunk size max | Chunk mas grande (tokens) | ~1000-1100 |
| Chunk size avg | Promedio de tokens por chunk | ~500-800 |
| Chunk size median | Mediana de tokens por chunk | ~600-900 |
| Chunk size p95 | Percentil 95 de tokens por chunk | ~900-1050 |

### Dataset: distribucion por tipo

| Tipo | Cantidad | Formato | Area funcional |
|------|----------|---------|----------------|
| RRHH | 7 | PDF | Administracion, Aprendizaje, Beneficios, Comunicacion, Desarrollo, Tecnologia, Salud |
| Paquetes bancarios | 6 | DOCX | Manual, Baja, Retencion, Alta, Upgrade |
| Cajas de Seguridad | 1 | DOCX | Manual del producto |
| Prestamos Personales | 4 | DOCX | Manual, Otorgamiento, Pago cuota, Revocacion |

### Como capturar las metricas

1. **Via logs de Airflow**: el task `report_results` imprime el reporte completo en stdout/logs
2. **Via XCom**: el return value del task contiene `{"status", "metrics", "indexed_count", "failed_count"}`
3. **Via script de verificacion**: `python scripts/verify_demo_data.py --json` genera un JSON con metricas detalladas de la DB

## Out of scope

- Documentos reales del banco (se usan despues de firma de NDA)
- Evaluacion formal de calidad (RAGAS, post-MVP)
- Dataset de entrenamiento para fine-tuning (post-MVP)
- Reemplazo de fixtures existentes (evaluar post-demo)
