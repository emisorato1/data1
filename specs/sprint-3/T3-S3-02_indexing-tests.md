# T3-S3-02: Testing del pipeline de indexacion + DAG

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | - |
| Depende de | T3-S2-03 |
| Skill | `testing-strategy/SKILL.md` + `testing-strategy/references/fixtures-globales.md` |
| Estimacion | L (4-8h) |

## Contexto

Suite de tests para garantizar calidad del pipeline de indexacion y del DAG de Airflow. El pipeline es critico: si indexa mal, todas las respuestas del RAG se degradan.

## Spec

Crear tests unitarios para cada componente del pipeline, tests de integracion para el pipeline completo, y tests de estructura del DAG de Airflow.

## Acceptance Criteria

- [ ] Tests unitarios: FileValidator, AdaptiveChunker, EmbeddingService
- [ ] Tests de integracion: pipeline completo con Docker Postgres + pgvector
- [ ] Test del DAG: estructura valida, tasks correctos, dependencias bien definidas
- [ ] Fixtures: documentos PDF/DOCX de ejemplo en `tests/fixtures/`
- [ ] Coverage > 80% para modulo `rag-indexing`
- [ ] Test de regresion: mismos documentos producen mismos chunks (determinismo)

## Archivos a crear/modificar

- `tests/unit/test_file_validator.py` (crear o expandir)
- `tests/unit/test_adaptive_chunker.py` (crear o expandir)
- `tests/unit/test_embedding_service.py` (crear)
- `tests/integration/test_indexing_pipeline.py` (crear)
- `tests/unit/test_dag_structure.py` (crear)
- `tests/fixtures/` (agregar documentos de ejemplo)

## Decisiones de diseno

- Tests de estructura de DAG: validan que el DAG compila y tiene las tasks esperadas, sin ejecutar
- Determinismo en chunking: mismo input debe producir mismos chunks, facilita debugging
- Coverage 80% para modulo critico: mas alto que el minimo general (70%)

## Out of scope

- Tests de performance del pipeline (post-MVP)
- Tests con documentos reales del banco (se usan sinteticos)
- Tests de evaluacion de calidad (RAGAS, post-MVP)
