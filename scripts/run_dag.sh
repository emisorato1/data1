#!/bin/bash
# Script para ejecutar DAGs de Airflow manualmente Novosibirsk

if [ -z "$1" ]; then
  echo "Uso: ./scripts/run_dag.sh <nombre_del_dag> [config_json]"
  echo "Ejemplo: ./scripts/run_dag.sh load_demo_data '{\"folder_path\": \"data/demo/\"}'"
  exit 1
fi

DAG_NAME=$1
DAG_CONF=${2:-"{}"}

echo "=== Triggering DAG: $DAG_NAME ==="
docker compose exec airflow airflow dags trigger "$DAG_NAME" --conf "$DAG_CONF"
