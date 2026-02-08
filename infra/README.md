# Infra

Infraestructura como código y configuraciones de despliegue. Contiene manifiestos de **Kubernetes** (estructura base/overlays con Kustomize para dev/staging/prod), **docker-compose** para entorno local, scripts de deployment, configuración de Helm charts, y archivos de automatización. Diseñado para self-hosting en K8s con soporte para Docker Compose como alternativa. Incluye configuraciones para todos los servicios, bases de datos, observabilidad y networking. Preparado para CI/CD con GitHub Actions.

