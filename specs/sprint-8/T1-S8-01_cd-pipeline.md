# T1-S8-01: CD Pipeline Integral (App, Airflow y DAGs) via Workload Identity

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (DevOps/Ops) |
| Prioridad | Alta |
| Estado | Done |
| Bloqueante para | Despliegues automatizados de RAG |
| Depende de | Infraestructura y Runbook actualizados |
| Skill | `docker-deployment/SKILL.md` |
| Estimacion | XL (8+h) |

## Contexto

El desarrollo se realiza bajo un enfoque **Local First** (usando `docker-compose.yml` para evitar fricciones de red y túneles). El despliegue a los entornos GCP (GKE y Cloud SQL) se debe realizar de manera completamente automatizada. 

Esta especificación reemplaza la visión original de CD básico, incorporando los hallazgos críticos operacionales documentados en el `RUNBOOK.md` del repositorio de infraestructura (gestión de StatefulSets, restricciones de Helm, Custom Image de Airflow y sincronización de DAGs a GCS).

## Spec

Implementar un pipeline de Despliegue Continuo en GitHub Actions activado tras un `push` a la rama `main` (condicionado al éxito del CI). El pipeline utilizará **Workload Identity Federation** (cero claves estáticas) para autenticarse, construir imágenes (Backend/Frontend y Airflow), actualizar los DAGs en GCS y ejecutar un `helm upgrade` seguro con manejo explícito de StatefulSets y migraciones de DB.

## Acceptance Criteria

### 1. Autenticación Segura
+ [x] GitHub Actions configurado con Workload Identity Federation (OIDC) mapeado al repositorio exacto.
+ [x] Service Account de GCP sin claves JSON descargadas, utilizando únicamente permisos mínimos (`artifactregistry.writer`, `container.developer`, `storage.objectAdmin`).

### 2. Construcción y Publicación (Build & Push)
+ [x] **App Principal:** Construcción multi-stage de `docker/Dockerfile`, tageada con `${{ github.sha }}` y subida a GCR.
+ [x] **Airflow Custom Image:** Construcción de `airflow/Dockerfile` (incluyendo pre-cache de `tiktoken` y copiado de `src/`) y subida a GCR.
+ [x] **Sincronización de DAGs:** Ejecución de `gsutil -m rsync -r -d dags/ gs://macro-ai-dev-airflow/dags/` para actualizar los pipelines del orquestador.

### 3. Despliegue y Migraciones (Helm)
+ [x] Uso del comando seguro para GKE restringido: `helm upgrade --install ... --force --no-hooks --timeout 8m`.
+ [x] **Helm Hook de Migración:** Job de tipo `pre-install,pre-upgrade` que levanta un Pod temporal con Cloud SQL Auth Proxy sidecar para ejecutar `alembic upgrade head` contra `macro-ai-dev-db`.
+ [x] Inyección de URL de Langfuse interna (`http://langfuse-web.langfuse.svc.cluster.local:3000`) en los Pods de la aplicación.

### 4. Operaciones Post-Despliegue (StatefulSets Fix)
+ [x] Script automático de reinicio para Workers de Airflow: escalado a `0`, pausa de seguridad (`sleep 120` para PVs), y re-escalado a `2`.
+ [x] Limpieza automática de ReplicaSets huérfanos generados por el flag `--force` (`awk '$2==0 && $3==0'`).

### 5. Notificación y Validación
+ [x] Notificación de deploy exitoso o fallido (Slack/Email).
+ [x] Documentación técnica del pipeline actualizada (`docs/deployment/cd-pipeline.md`).

## Archivos a crear/modificar

- `.github/workflows/cd.yml` (crear)
- `helm/chart/templates/db-migrate-hook.yaml` (crear)
- `helm/chart/values.yaml` (modificar para inyectar tag de imagen dinamico y Langfuse)

## Decisiones de diseno

- **Desarrollo "Local First":** Los desarrolladores no configuran túneles a GCP. El pipeline asume la responsabilidad de mapear el código a la infraestructura en la nube.
- **Workload Identity sobre SA Keys:** Cumplimiento de normativas de seguridad bancarias evitando filtración de credenciales estáticas.
- **Manejo Manual de StatefulSets:** `helm upgrade` no actualiza StatefulSets. Se requiere un fix imperativo post-deploy para asegurar que Airflow use la nueva imagen.
- **GCS Sync Directo:** Enviar los DAGs al bucket directamente desde el CI es más rápido y predecible que depender exclusivamente de commits monitoreados dentro del clúster.

## Out of scope

- Despliegues Blue-Green / Canary (El actual es un Rolling Update / Recreate).
- Infraestructura inmutable (Terraform sigue siendo ejecución manual / separada).

____________________________________________________________________________________


1. Autenticación a Google Cloud (GCP)
Original: Planteaba usar credenciales estáticas metidas a mano (GCP SA key en GitHub Secrets).
Actualizada: Obliga a usar Workload Identity Federation (OIDC). Esto es un cambio fundamental de seguridad bancaria ("Zero Trust"), eliminando las claves en texto plano / archivos JSON descargados.
2. Alcance de lo que se despliega
Original: Solo mencionaba compilar la imagen principal (Backend/Frontend) y correr un comando genérico de Helm.
Actualizada: Detalla que el proyecto no es solo una app, sino todo un ecosistema RAG. Agrega como requerimiento:
Compilar y empujar también una Custom Image de Airflow (con librerías de Python precacheadas).
Sincronizar explícitamente la carpeta de los DAGs hacia el bucket de Google Cloud Storage (gsutil rsync -r dags/).
3. Migraciones de Base de Datos
Original: No mencionaba cómo se actualizaba el esquema de Postgres.
Actualizada: Incorpora el requerimiento de crear un Helm Hook de Migración. Específica que antes del despliegue se debe levantar un Pod temporal con un sidecar (Cloud SQL Auth Proxy) para ejecutar alembic upgrade head.
4. Manejo del Estado (StatefulSets)
Original: Asumía que helm upgrade refrescaba todo sin problemas ("Zero-downtime deployment").
Actualizada: Introduce los "Operaciones Post-Despliegue". Como Helm no reinicia automáticamente bien los StatefulSets de Airflow cuando se usa un tag de imagen específico, obliga a crear un script para bajarlos a 0, esperar a que se liberen los discos persistentes (PVs), y volver a subirlos a 2.
5. Configuración de Red/Dependencias internas
Original: No mencionaba integraciones internas.
Actualizada: Agrega explícitamente la obligación de inyectar la URL interna del traceador Langfuse (http://langfuse-web...) dentro del clúster de Kubernetes en los valores del despliegue.