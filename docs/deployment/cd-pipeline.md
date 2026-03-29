# Continuous Deployment (CD) Pipeline Integral

El pipeline de despliegue continuo de la plataforma automatiza la entrega a GCP (GKE y GCS), asegurando el cumplimiento de los estándares de seguridad (Zero Trust) y mitigando comportamientos esperados de la infraestructura.

## Descripción del Pipeline (`.github/workflows/cd.yml`)

El pipeline se dispara automáticamente en cada push a la rama `main` y consta de tres fases principales:

### 1. Construcción y Publicación (Build & Push)
- **Autenticación Segura:** Utiliza Workload Identity Federation (WIF) con OpenID Connect (OIDC). No se almacenan Service Account keys estáticas en GitHub.
- Se compilan tres imágenes multi-stage y se suben a Google Artifact Registry etiquetadas con el SHA del commit:
  - **Backend:** `docker/Dockerfile`
  - **Frontend:** `docker/Dockerfile.frontend`
  - **Airflow Custom Image:** `airflow/Dockerfile` (con dependencias para el orquestador precacheadas como tiktoken).

### 2. Sincronización de DAGs a GCS
Para garantizar que el orquestador Airflow procese siempre las últimas rutinas definidas, la carpeta `dags/` se sincroniza directamente contra el bucket de Google Cloud Storage designado mediante el comando rápido `gsutil -m rsync -r -d dags/`.

### 3. Migraciones, Despliegue y Fixes
- **Migración Segura (Helm Hook):** En vez de confiar la migración a un paso dentro del clúster desatendido, se orquesta explícitamente el Job `db-migrate-hook.yaml`. Este Job levanta un sidecar con el *Cloud SQL Auth Proxy* y corre `alembic upgrade head`, deteniendo el proxy internamente al finalizar la operación (para que el Pod no quede colgado).
- **Despliegue General:** Se ejecuta `helm upgrade --install` con el flag `--no-hooks` para obviar pasos automáticos lentos y el flag `--force` para evitar interrupciones de diff. La configuración inyecta dinámicamente:
  - Los tags generados (`${{ github.sha }}`).
  - La URL interna de Langfuse (vía `values.yaml` `config.langfuseHost`).
- **Fix de StatefulSets (Airflow):** Dado que la bandera `--force` en Helm tiene dificultades para reiniciar limpiamente StatefulSets persistentes, el pipeline incluye un paso imperativo que escala los workers de Airflow a `0`, pausa 120 segundos para que se liberen los *Persistent Volumes*, y los vuelve a escalar a la cantidad base.
- **Limpieza de Basura:** Un recolector al final (`awk '$2==0 && $3==0'`) elimina *ReplicaSets* huérfanos que el update en modo fuerza haya dejado sueltos.

## Requisitos y Configuración Previa
Para que el pipeline funcione correctamente, los siguientes secretos deben estar en GitHub:
* `WIF_PROVIDER`: El path completo al proveedor OIDC en IAM.
* `SERVICE_ACCOUNT`: El e-mail del service account de despliegue que posee roles `artifactregistry.writer`, `container.developer`, y `storage.objectAdmin`.

### Notas de Arquitectura (Decisiones de diseño)
*   Se adoptó **Workload Identity sobre SA Keys** para el estricto cumplimiento bancario.
*   **Desarrollo Local-First:** El pipeline asume el 100% de la carga del traslado a GCP.
*   **Aproximación Imperativa en GKE:** Algunos recursos en GKE son inherentemente obstinados con respecto a las actualizaciones automáticas declarativas (StatefulSets). Abordar su reinicio de manera imperativa en el pipeline asegura consistencia y evita falsos positivos.