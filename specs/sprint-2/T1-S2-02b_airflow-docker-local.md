# T1-S2-02b: Airflow 3 en Docker Compose para desarrollo local

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Infra) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T3-S2-03 (DAG indexacion) |
| Depende de | T1-S1-03 (docker-compose base) |
| Skill | `docker-deployment/SKILL.md` |
| Estimacion | M (2-4h) |

## Contexto

T3-S2-03 (DAG de indexacion) depende de T1-S2-02 (Airflow en K8s), que a su vez depende de infraestructura externa (GKE cluster, Cloud SQL, GCS bucket) gestionada por el repo `itmind-infrastructure`. Esta dependencia externa bloquea el desarrollo local del DAG.

La decision original (T1-S1-03) establecia que Airflow NO se levanta localmente porque consume muchos recursos. Sin embargo, para desbloquear T3-S2-03 sin esperar la infra K8s, necesitamos un Airflow minimal local que permita:

1. Desarrollar y probar DAGs con `dag.test()` y desde la UI
2. Validar la integracion entre Airflow y `IndexingService` (T3-S2-02)
3. Iterar rapido sin depender de port-forward al cluster

Esta spec NO reemplaza T1-S2-02 (deploy K8s productivo). Es un entorno de desarrollo local complementario.

## Spec

Agregar Apache Airflow 3 al `docker-compose.yml` existente con configuracion minimalista usando `SequentialExecutor` y SQLite (metadata interna de Airflow), conectado a la base PostgreSQL local existente (donde `IndexingService` escribe). Los DAGs se montan desde el directorio `dags/` del monorepo via bind mount.

## Acceptance Criteria

- [x] Servicio `airflow` agregado al `docker-compose.yml` existente bajo un profile `airflow` (no se levanta por defecto con `docker compose up`)
- [x] Imagen oficial `apache/airflow:3.0.6-python3.12` (ultima 3.x estable compatible con Python 3.12)
- [x] Executor: `LocalExecutor` (default de Airflow 3 standalone; suficiente para desarrollo local)
- [x] Base de datos de metadata: SQLite interna (default de Airflow standalone; sin agregar otra Postgres)
- [x] DAGs montados via bind mount: `./dags:/opt/airflow/dags`
- [x] Conexion `rag_db` configurada via variable de entorno para que los DAGs accedan a la PostgreSQL local (la misma de `db` service)
- [x] Variables de entorno de Google Cloud (`GOOGLE_API_KEY`) propagadas al contenedor para que los DAGs puedan generar embeddings
- [x] Airflow UI accesible en `http://localhost:8080`
- [x] Healthcheck configurado contra el endpoint `/api/v2/monitor/health` (Airflow 3)
- [x] `docker compose --profile airflow up` levanta Airflow + PG + Redis sin errores
- [x] Verificacion: DAG `hello_world` de prueba ejecuta correctamente (1 DAG, 0 errores en dag-processor)
- [x] `.env.example` actualizado con variables de Airflow local y comentarios de uso
- [x] Documentacion en `.env.example` indicando como activar el profile de Airflow

## Archivos a crear/modificar

- `docker-compose.yml` (modificar) -- agregar servicio `airflow` con profile
- `.env.example` (modificar) -- agregar variables de Airflow local
- `dags/__init__.py` (crear) -- package marker para directorio de DAGs
- `dags/hello_world.py` (crear) -- DAG de smoke test si no existe aun
- `tests/unit/test_airflow_smoke.py` (crear) -- test de que el DAG parsea sin errores

## Decisiones de diseno

- **Profile `airflow`**: permite que `docker compose up` siga levantando solo PG+Redis (comportamiento actual). Airflow se activa explicitamente con `--profile airflow`. Esto respeta la decision original de T1-S1-03 de mantener el compose minimalista
- **SequentialExecutor + SQLite**: minimo overhead. En K8s se usa KubernetesExecutor (T1-S2-02), pero localmente no necesitamos paralelismo de tasks ni Postgres para metadata de Airflow
- **Bind mount de `dags/`**: los DAGs viven en el monorepo y se montan directamente. Sin GCS sync, sin builds de imagen custom. Editar un DAG se refleja inmediatamente
- **Conexion a PG del app via env vars**: los DAGs usan `IndexingService` que lee `DATABASE_URL` del environment. La conexion Airflow a la PG de la app se configura via `AIRFLOW_CONN_RAG_DB` para que los tasks accedan a la misma base
- **Sin Celery, sin Redis para Airflow**: Redis ya existe en el compose para cache de la app, pero Airflow local no lo necesita (SequentialExecutor no usa broker)
- **Imagen base sin customizar**: para desarrollo local alcanza con montar `src/` y configurar `PYTHONPATH`. No se crea Dockerfile custom de Airflow (eso es parte de T1-S3-01 o T1-S2-02 para K8s)
- **`src/` montado como volumen**: para que los DAGs puedan hacer `from src.application.services.indexing_service import IndexingService`, se monta `./src:/opt/airflow/src:ro` y se setea `PYTHONPATH=/opt/airflow`
- **Dependencias Python del proyecto**: las dependencias core del proyecto (`sqlalchemy`, `pgvector`, `langchain`, etc.) se instalan en el contenedor de Airflow via un entrypoint que ejecuta `pip install` desde `pyproject.toml`. Alternativa: pre-built image (out of scope, ver T1-S3-01)

## TDD: estrategia de testing

El DAG de smoke test (`hello_world.py`) y el test unitario validan que:

1. **Parseo del DAG**: Airflow puede importar el DAG sin errores de sintaxis ni imports faltantes
2. **Estructura del DAG**: el DAG tiene los tasks esperados y las dependencias correctas

```python
# tests/unit/test_airflow_smoke.py
import pytest

def test_hello_world_dag_loads():
    """Verificar que el DAG parsea sin errores de import."""
    from dags.hello_world import dag
    assert dag is not None
    assert dag.dag_id == "hello_world"

def test_hello_world_dag_has_tasks():
    """Verificar que el DAG tiene al menos un task."""
    from dags.hello_world import dag
    assert len(dag.tasks) > 0
```

Estos tests corren con `pytest` (sin necesidad de Docker) y validan la integridad del DAG antes de levantarlo en el contenedor.

## Out of scope

- Dockerfile custom de Airflow con dependencias pre-instaladas (spec T1-S3-01)
- Deploy de Airflow en K8s (spec T1-S2-02)
- KubernetesExecutor, CeleryExecutor (solo SequentialExecutor local)
- Conexion a Cloud SQL via proxy
- GCS bucket sync para DAGs
- DAG de indexacion real (spec T3-S2-03)
- CI/CD para DAGs
- Autenticacion de Airflow UI (desarrollo local, acceso directo)
