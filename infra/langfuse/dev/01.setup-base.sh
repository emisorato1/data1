#!/bin/bash
# =============================================================================
# Langfuse Setup Base - Kubernetes (Helm)
# Enterprise AI Platform - Observability
# Documentación: https://langfuse.com/self-hosting/deployment/kubernetes-helm
# =============================================================================

# -----------------------------------------------------------------------------
# PRE-REQUISITOS: 
# - Acceso a un cluster de Kubernetes (minikube, GKE, EKS, AKS, etc.)
# - Helm instalado en tu máquina local
# - gcloud CLI instalado y configurado
# -----------------------------------------------------------------------------

# =============================================================================
# 0. CONFIGURACIÓN DE GOOGLE CLOUD
# =============================================================================

#0.1. Listar proyectos disponibles en tu cuenta de GCP
gcloud projects list

#0.2. Setear el proyecto de GCP por defecto
# Reemplaza <PROJECT_ID> con el ID de tu proyecto
gcloud config set project <PROJECT_ID>

#0.3. Verificar el proyecto actual configurado
gcloud config get-value project

#0.4. Listar clusters de GKE disponibles en el proyecto
gcloud container clusters list

#0.5. Obtener credenciales del cluster de GKE para kubectl
# Reemplaza <CLUSTER_NAME> con el nombre de tu cluster
# Reemplaza <ZONE_OR_REGION> con la zona o región del cluster (ej: us-central1-a)
gcloud container clusters get-credentials <CLUSTER_NAME> --zone <ZONE_OR_REGION>
gcloud container clusters get-credentials airbyte-test --zone us-central1-a

#0.6. (Alternativa) Si el cluster es regional, usa --region en lugar de --zone
# gcloud container clusters get-credentials <CLUSTER_NAME> --region <REGION>

#0.7. Verificar conexión al cluster
kubectl cluster-info

#0.8. Verificar el contexto actual de kubectl
kubectl config current-context

# =============================================================================
# 1. INSTALACIÓN DE LANGFUSE
# =============================================================================

#01. Agregar el repositorio de Helm de Langfuse
helm repo add langfuse https://langfuse.github.io/langfuse-k8s

#02. Actualizar los repositorios de Helm para obtener los charts más recientes
helm repo update

#03. Crear el namespace dedicado para Langfuse (opcional pero recomendado)
kubectl create namespace langfuse-test

# =============================================================================
# 2. GENERACIÓN DE SECRETOS REQUERIDOS (Langfuse v3)
# Documentación: https://langfuse.com/self-hosting/configuration
# =============================================================================

#04. Generar NEXTAUTH_SECRET (usado para validar cookies de sesión)
# Guarda este valor, lo necesitarás para el helm install
openssl rand -base64 32

#05. Generar SALT (usado para hashear API keys)
# Guarda este valor, lo necesitarás para el helm install
openssl rand -base64 32

#06. Generar ENCRYPTION_KEY (usado para encriptar datos sensibles)
# IMPORTANTE: Debe ser 256 bits = 64 caracteres hexadecimales
# Guarda este valor, lo necesitarás para el helm install
openssl rand -hex 32

# =============================================================================
# 3. INSTALACIÓN CON SECRETOS CONFIGURADOS
# =============================================================================

#07. Instalar Langfuse usando Helm con los secretos requeridos
# NOTA: Reemplaza los valores <NEXTAUTH_SECRET>, <SALT>, <ENCRYPTION_KEY>
# con los valores generados en los pasos anteriores

helm install langfuse langfuse/langfuse -n langfuse-test \
  --set langfuse.nextAuthUrl="http://localhost:3000" \
  --set langfuse.nextAuthSecret="<NEXTAUTH_SECRET>" \
  --set langfuse.salt="<SALT>" \
  --set langfuse.encryptionKey="<ENCRYPTION_KEY>"

#08. (Alternativa) Instalar con un comando que genera los secretos automáticamente
# Este comando genera los secretos en línea - útil para desarrollo/testing
helm install langfuse langfuse/langfuse -n langfuse-test \
  --set langfuse.nextAuthUrl="http://localhost:3000" \
  --set langfuse.nextAuthSecret="$(openssl rand -base64 32)" \
  --set langfuse.salt="$(openssl rand -base64 32)" \
  --set langfuse.encryptionKey="$(openssl rand -hex 32)"


# Alternativa: Crear values.yml y langfuse-secret.yaml
# Cargar el .env y crear el Secret
source .env
kubectl create secret generic langfuse-secrets -n langfuse-test \
  --from-literal=NEXTAUTH_SECRET="$NEXTAUTH_SECRET" \
  --from-literal=SALT="$SALT" \
  --from-literal=ENCRYPTION_KEY="$ENCRYPTION_KEY" \
  --dry-run=client -o yaml > 02.langfuse-secret.yaml

kubectl apply -f 02.langfuse-secret.yaml

helm install langfuse langfuse/langfuse -n langfuse-test -f 03.values.yaml

# =============================================================================
# 4. VERIFICACIÓN Y ACCESO
# =============================================================================

#09. Verificar el estado de los pods (esperar hasta que todos estén Running)
# NOTA: Puede tomar hasta 5 minutos. Los containers langfuse-web y langfuse-worker
# pueden reiniciarse varias veces mientras se provisionan las bases de datos
kubectl get pods -n langfuse-test

#10. Ver el estado de los pods en modo watch (presiona Ctrl+C para salir)
kubectl get pods -n langfuse-test -w

#11. Listar los servicios para obtener el puerto del servicio langfuse-web
kubectl get services -n langfuse-test

#12. Crear port-forward para acceder a la UI de Langfuse localmente
kubectl port-forward svc/langfuse-web -n langfuse-test 3000:3000

#13. Verificar los logs del pod langfuse-web para debugging
kubectl logs -n langfuse-test -l app.kubernetes.io/name=langfuse-web --tail=100

#14. Verificar los logs del pod langfuse-worker para debugging
kubectl logs -n langfuse-test -l app.kubernetes.io/name=langfuse-worker --tail=100

# =============================================================================
# 5. COMANDOS ADICIONALES DE GESTIÓN
# =============================================================================

#15. Actualizar Langfuse a la última versión (rollout con nuevos valores)
helm repo update
helm upgrade langfuse langfuse/langfuse -n langfuse-test -f 03.values.yaml

#16. (Alternativa) Si el upgrade falla, desinstalar y reinstalar
# helm uninstall langfuse -n langfuse-test
# helm install langfuse langfuse/langfuse -n langfuse-test -f 03.values.yaml

#17. Forzar rollout de los deployments (si los pods no se actualizan)
kubectl rollout restart deployment langfuse-web -n langfuse-test
kubectl rollout restart deployment langfuse-worker -n langfuse-test

#18. Ver estado del rollout
kubectl rollout status deployment langfuse-web -n langfuse-test
kubectl rollout status deployment langfuse-worker -n langfuse-test

#19. Desinstalar Langfuse (cleanup completo)
helm uninstall langfuse -n langfuse-test
kubectl delete namespace langfuse-test

#20. Ver los valores configurables del chart (útil para ver todas las opciones)
helm show values langfuse/langfuse

#21. Instalar con valores personalizados desde archivo values.yaml
# helm install langfuse langfuse/langfuse -n langfuse-test -f values.yaml

# =============================================================================
# NOTAS IMPORTANTES:
# - Por defecto, el chart despliega los containers de Langfuse y los datastores
#   (PostgreSQL, Clickhouse, Redis)
# - Opcionalmente puedes apuntar a instancias existentes de PostgreSQL, 
#   Clickhouse y Redis
# - Para configuración avanzada, consulta: 
#   https://langfuse.com/self-hosting/configuration
# - Después de acceder a http://localhost:3000, registra un usuario, 
#   crea una organización y un proyecto para comenzar
# =============================================================================
