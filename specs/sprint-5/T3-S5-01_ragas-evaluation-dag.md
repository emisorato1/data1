# T3-S5-01: Airflow DAG evaluacion RAGAS programado

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | - |
| Depende de | T1-S2-02 (done), T3-S2-02 (done), T1-S2-03 (done), T3-S4-01 (done) |
| Skill | `observability/SKILL.md` + `observability/references/ragas-evaluator.md` |
| Estimacion | L (4-8h) |

## Contexto

Quality monitoring of the RAG pipeline requires automated evaluation. RAGAS provides standardized metrics (faithfulness, answer relevancy, context precision) that must be computed regularly against a test dataset.

## Spec

Create Airflow DAG `ragas_evaluation` that runs on a configurable schedule (default: daily), evaluates the RAG pipeline against a golden dataset, and stores metrics in the database + Langfuse.

## Acceptance Criteria

- [x] DAG `ragas_evaluation` en `dags/evaluation/ragas_evaluation.py`
- [x] Schedule configurable via Airflow Variable (default: `@daily`)
- [x] Tasks: `load_golden_dataset` -> `run_queries` -> `compute_metrics` -> `store_results` -> `alert_on_regression`
- [x] Metricas RAGAS: faithfulness, answer_relevancy, context_precision, context_recall
- [x] Golden dataset en formato JSON con pares (question, ground_truth, contexts)
- [x] Resultados almacenados en tabla `ragas_evaluations` con timestamp y metricas
- [x] Alerta si alguna metrica cae por debajo de threshold configurable
- [x] Metricas enviadas a Langfuse como scores
- [x] Tests de estructura del DAG

## Archivos a crear/modificar

- `dags/evaluation/ragas_evaluation.py` (crear)
- `dags/evaluation/__init__.py` (crear)
- `src/infrastructure/evaluation/ragas_evaluator.py` (crear)
- `alembic/versions/xxx_add_ragas_evaluations_table.py` (crear)
- `tests/unit/test_dag_ragas.py` (crear)
- `data/golden_dataset_sample.json` (crear)

## Decisiones de diseno

- **DAG separado del indexing**: Evaluacion no debe interferir con la carga de documentos.
- **Golden dataset versionable**: JSON en el repo permite trackear cambios al dataset de evaluacion.
- **Alertas por regresion**: Detectar degradacion temprana del pipeline.

## Out of scope

- Creacion del golden dataset real (requiere Entregable #3 del banco)
- Dashboard de metricas RAGAS (spec T5-S8-01)
- Fine-tuning automatico basado en metricas
