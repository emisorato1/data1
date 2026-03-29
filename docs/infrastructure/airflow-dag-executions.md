# Ejecuciones de DAGs en Airflow

Referencia operativa para los DAGs del sistema. Cubre los tres métodos de ejecución
(UI, CLI, REST API) aplicados a cada DAG disponible.

---

## DAGs disponibles

| DAG | Trigger | Propósito |
|-----|---------|-----------|
| `rag_indexing` | Manual | Indexa un documento individual (validate → chunk → embed → store) |
| `load_demo_data` | Manual | Indexa todos los documentos de una carpeta local o bucket GCS |
| `ragas_evaluation` | Programado (`@daily`) | Evalúa la calidad del pipeline RAG contra el golden dataset |

---

## Métodos de ejecución

### 1. Airflow UI

1. Abre `http://localhost:8080`
2. Busca el DAG en la lista
3. Clic en **Trigger DAG** (▶) para ejecución sin parámetros
4. Clic en **Trigger DAG w/ config** (▶⚙) para pasar JSON de configuración

---

### 2. CLI (desde el host con Docker Compose)

```bash
docker compose exec airflow-scheduler airflow dags trigger <dag_id> \
  --conf '<json>'
```

---

### 3. REST API

```bash
curl -X POST http://localhost:8080/api/v1/dags/<dag_id>/dagRuns \
  -H "Content-Type: application/json" \
  -u "admin:admin" \
  -d '{"conf": <json>}'
```

---

## `rag_indexing` — Indexación de documento individual

**Cuándo usarlo:** cuando se sube un documento nuevo via API y hay que indexarlo
(el endpoint `/api/v1/documents/upload` lo trigerea automáticamente).

**Parámetros:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `document_id` | int | Sí | ID del registro en tabla `documents` |
| `file_path` | string | No | Ruta local o URI `gs://`. Si se omite, se busca en BD por `document_id` |

**Ejemplos:**

```bash
# Con document_id y file_path explícito
docker compose exec airflow-scheduler airflow dags trigger rag_indexing \
  --conf '{"document_id": 42, "file_path": "/opt/airflow/data/uploads/manual.pdf"}'

# Solo document_id (busca file_path en la BD)
docker compose exec airflow-scheduler airflow dags trigger rag_indexing \
  --conf '{"document_id": 42}'

# Desde GCS
docker compose exec airflow-scheduler airflow dags trigger rag_indexing \
  --conf '{"document_id": 42, "file_path": "gs://macro-ai-dev-backend-samples/RRHH/doc.pdf"}'
```

**Pipeline de tasks:**
```
validate_file → load_and_chunk → generate_embeddings → store_chunks
```

---

## `load_demo_data` — Indexación masiva (batch)

**Cuándo usarlo:** para indexar todos los documentos del dataset de demo de una vez,
ya sea desde el filesystem local del contenedor o desde un bucket GCS.

### Modo local (desarrollo)

Indexa los archivos montados en `/opt/airflow/data/demo/` (bind mount de `tests/data/demo/`).
No requiere acceso a GCS.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `folder_path` | string | `null` | Ruta relativa a `/opt/airflow`. Si se setea, activa modo local |
| `skip_existing` | bool | `true` | Omite archivos ya indexados (por hash SHA-256) |

```bash
# Primera indexación (indexa todo)
docker compose exec airflow-scheduler airflow dags trigger load_demo_data \
  --conf '{"folder_path": "data/demo/", "skip_existing": false}'

# Ejecuciones posteriores (solo archivos nuevos)
docker compose exec airflow-scheduler airflow dags trigger load_demo_data \
  --conf '{"folder_path": "data/demo/", "skip_existing": true}'
```

### Modo GCS (producción)

Escanea el bucket GCS y descarga cada archivo para indexarlo.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `gcs_bucket` | string | `macro-ai-dev-backend-samples` | Nombre del bucket (sin `gs://`) |
| `skip_existing` | bool | `true` | Omite archivos ya indexados |

```bash
# Bucket default
docker compose exec airflow-scheduler airflow dags trigger load_demo_data \
  --conf '{"skip_existing": true}'

# Bucket alternativo
docker compose exec airflow-scheduler airflow dags trigger load_demo_data \
  --conf '{"gcs_bucket": "otro-bucket", "skip_existing": false}'
```

**Pipeline de tasks:**
```
discover_documents → index_documents → report_results
```

> **Nota:** si se pasa `folder_path` y `gcs_bucket` al mismo tiempo, tiene prioridad
> el modo local (`folder_path`).

---

## `ragas_evaluation` — Evaluación de calidad RAGAS

**Cuándo usarlo:** corre automáticamente `@daily`. Se puede trigear manualmente
para evaluar después de un cambio en el pipeline o con un dataset distinto.

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `dataset_path` | string | `data/golden_dataset_sample.json` | Ruta al golden dataset JSON |

```bash
# Con el golden dataset por defecto
docker compose exec airflow-scheduler airflow dags trigger ragas_evaluation

# Con un dataset específico
docker compose exec airflow-scheduler airflow dags trigger ragas_evaluation \
  --conf '{"dataset_path": "data/golden/custom_eval.json"}'
```

**Pipeline de tasks:**
```
load_golden_dataset → run_ragas_evaluation → store_results → check_thresholds
```

**Umbrales de calidad** (configurables via Airflow Variable `ragas_evaluation_thresholds`):

| Métrica | Umbral mínimo |
|---------|---------------|
| `faithfulness` | 0.90 |
| `answer_relevancy` | 0.85 |
| `context_precision` | 0.80 |
| `context_recall` | 0.80 |

El task `check_thresholds` falla el DAG si alguna métrica cae por debajo del umbral,
generando una alerta visible en la UI.

---

## Monitoreo post-ejecución

### Ver logs de un DAG run

```bash
# Listar últimas ejecuciones
docker compose exec airflow-scheduler airflow dags list-runs -d <dag_id>

# Log de un task específico
docker compose exec airflow-scheduler airflow tasks logs <dag_id> <task_id> <run_id>
```

### Verificar indexación en base de datos

```sql
-- Documentos indexados (file_hash != NULL)
SELECT id, filename, area, file_hash IS NOT NULL AS indexed
FROM documents
ORDER BY id;

-- Chunks por documento
SELECT d.filename, COUNT(dc.id) AS chunks, SUM(dc.token_count) AS tokens
FROM document_chunks dc
JOIN documents d ON d.id = dc.document_id
GROUP BY d.filename
ORDER BY d.filename;

-- Pipeline runs recientes
SELECT document_id, status, started_at, finished_at, error_message
FROM pipeline_runs
ORDER BY started_at DESC
LIMIT 20;
```

### Variables de Airflow configurables

| Variable | Descripción | Default |
|----------|-------------|---------|
| `ragas_evaluation_schedule` | Cron del DAG de evaluación | `@daily` |
| `ragas_evaluation_thresholds` | JSON con umbrales RAGAS | Ver tabla arriba |
