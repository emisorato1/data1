# Estrategia de Ingress para Entorno Bancario (GCP)

Este documento detalla la estrategia de exposición de servicios para la **Enterprise AI Platform** en un entorno de banca de alta seguridad (Argentina).

## 1. Contexto y Requerimientos
Dada la naturaleza de los datos procesados (RAG sobre documentos sensibles de OpenText), el sistema **no debe ser expuesto a la internet pública**.

*   **Red**: Acceso exclusivo desde la red interna del banco (VPN o Direct Interconnect).
*   **Identidad**: Integración con **Azure AD** via OTDS (OpenText Directory Services).
*   **Compliance**: Auditoría de acceso y protección contra ataques de red (WAF).

## 2. Flujo de Autenticación Propuesto: Azure AD + OTDS

Dada la infraestructura del banco ("Azure AD to OTDS Authentication"), el flujo recomendado para asegurar "Zero Trust" es:

1.  **Nivel de Ingress (GCP IAP)**: 
    *   Configurar **Identity-Aware Proxy (IAP)** federado con el **Azure AD** del banco mediante OIDC.
    *   Esto asegura que solo empleados autenticados en el AD del banco lleguen a la aplicación.
2.  **Nivel de Aplicación (User Mapping)**:
    *   La aplicación recibe los headers de IAP (`x-goog-authenticated-user-email`).
    *   **Mapeo**: Se busca ese email/UPN en la tabla `kuaf` (Mirror de OpenText/OTDS) para obtener el `user_id` numérico.
    *   **Authorization**: Ese `user_id` se usa en las consultas SQL al RAG para filtrar por ACLs (`dtreeacl`).

## 3. Arquitectura de Ingress Propuesta

La solución recomendada para el ecosistema GKE del banco es el uso de **GCP HTTP(S) Load Balancing (Internal)** con los siguientes componentes:

### 2.1 Google Cloud Armor (WAF)
Se deben aplicar políticas de seguridad a nivel de Load Balancer para:
*   **IP Allowlisting**: Solo permitir tráfico desde los rangos CIDR de las sucursales y oficinas centrales del banco.
*   **OWASP Core Rule Set**: Mitigar inyecciones SQL, XSS y otros ataques comunes de la capa 7.

### 2.2 Identity-Aware Proxy (IAP)
Crucial para el banco. IAP actúa como una capa de autenticación *antes* de que el tráfico llegue al pod.
*   **Beneficio**: No es necesario que el frontend o la API gestionen el login inicial. Google valida el token de identidad del banco.
*   **Implementación**: Se habilita mediante una anotación en el BackendConfig de Kubernetes vinculado al Service.

### 2.3 Managed Certificates & Private CA
*   Uso de **Google-managed certificates** si se utiliza un dominio interno registrado en Cloud DNS.
*   Si el banco requiere certificados emitidos por su propia CA, se deben subir como Kubernetes Secrets y referenciarlos en el Ingress.

## 3. Configuración de Kubernetes (GKE)

Para implementar esto, el `ingress.yaml` de Helm debe configurarse para usar la clase de ingress de GKE:

```yaml
# Definición sugerida para el Ingress de Producción
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rag-enterprise-ai-platform
  annotations:
    kubernetes.io/ingress.class: "gce-internal"  # Load Balancer Interno
    kubernetes.io/ingress.allow-http: "false"     # Forzar HTTPS
    networking.gke.io/v2-managed-certificates: "rag-cert"
    networking.gke.io/v1beta1.FrontendConfig: "rag-frontend-config"
spec:
  rules:
  - host: "ai.macro.com.ar"  # Ejemplo de dominio del banco
    http:
      paths:
      - path: /api/*
        pathType: ImplementationSpecific
        backend:
          service:
            name: backend-service
            port:
              number: 8000
      - path: /*
        pathType: ImplementationSpecific
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

## 4. Estrategia de DNS
*   **Cloud DNS (Private Zone)**: Crear una zona privada vinculada a la VPC del proyecto.
*   **Nombre**: `ai-enterprise.bancomacro.com.ar` (o el subdominio asignado por el banco).
*   **Registro**: El registro A debe apuntar a la IP estática del Internal Load Balancer.

## 5. Próximos Pasos (Hoja de Ruta)

1.  **Terraform**: Reservar una IP estática interna en la subred de servicios.
2.  **Seguridad**: Configurar la política de Cloud Armor en la consola de GCP.
3.  **Helm**: Actualizar `values.yaml` para habilitar el ingress con las anotaciones específicas de Google (`gce-internal`).
4.  **Pruebas**: Validar acceso desde una VM dentro de la misma VPC antes de habilitar IAP.
