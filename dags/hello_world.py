"""
DAG de verificacion para validar el deployment de Airflow 3 en GKE.

Verifica:
  1. Airflow funciona correctamente (TaskFlow API)
  2. Workload Identity permite acceso a GCP (GCS via google.cloud.storage)

Uso:
  gsutil cp dags/hello_world.py gs://macro-ai-dev-airflow/dags/
  Trigger desde UI: http://localhost:8080 (via port-forward)
"""

from __future__ import annotations

import pendulum
from airflow.sdk import dag, task


@dag(
    dag_id="hello_world",
    schedule=None,
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    tags=["test", "verification"],
    doc_md=__doc__,
)
def hello_world():
    @task
    def print_hello():
        """Verificacion basica: Airflow ejecuta tasks correctamente."""
        print("Hello from Airflow 3 on GKE!")
        print("TaskFlow API working correctly.")
        return {"status": "ok", "message": "Airflow is running"}

    @task
    def verify_gcp_access():
        """Verificar que Workload Identity permite acceso a GCS."""
        from google.cloud import storage

        client = storage.Client()
        buckets = [b.name for b in client.list_buckets(max_results=5)]
        print(f"GCP access OK. Found {len(buckets)} buckets: {buckets}")
        return {"status": "ok", "buckets_found": len(buckets)}

    result_hello = print_hello()
    result_gcp = verify_gcp_access()
    result_hello >> result_gcp


hello_world()
