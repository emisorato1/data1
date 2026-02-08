# Troubleshooting - Langfuse en Kubernetes (GKE)

Este documento resume los problemas encontrados durante el despliegue de Langfuse en GKE y sus soluciones.

---

## 1. Error: `no valid value, secretKeyRef, fieldRef, or resourceFieldRef provided for langfuse.salt`

### Descripción
Al ejecutar `helm install`, el chart falla indicando que no se proporcionó un valor válido para `salt`, `nextAuthSecret` o `encryptionKey`.

### Causa
Langfuse v3 requiere **secretos obligatorios** que deben configurarse explícitamente:
- `NEXTAUTH_SECRET`: Para validar cookies de sesión
- `SALT`: Para hashear API keys
- `ENCRYPTION_KEY`: Para encriptar datos sensibles

### Solución
Crear un Kubernetes Secret con los valores requeridos y referenciarlo en el `values.yaml` usando la estructura correcta:

```yaml
langfuse:
  salt:
    secretKeyRef:
      name: <nombre-del-secret>
      key: <key-del-salt>
```

**Archivos modificados:** `02.langfuse-secret.yaml`, `03.values.yaml`

---

## 2. Error: `ENCRYPTION_KEY must be 256 bits, 64 string characters in hex format`

### Descripción
El pod `langfuse-worker` crashea con un error de validación de Zod indicando que el `ENCRYPTION_KEY` no tiene el formato correcto.

### Causa
El `ENCRYPTION_KEY` estaba en formato **base64** (88 caracteres) pero Langfuse espera exactamente **64 caracteres hexadecimales**.

### Solución
Generar el `ENCRYPTION_KEY` con el comando correcto y usarlo en texto plano:

```bash
openssl rand -hex 32
```

El valor resultante debe tener exactamente 64 caracteres hexadecimales (ej: `ad4bc29dd4f44e4afbc7e267641b7bac6e7428c200ff5611400d95da1c16c129`).

**Archivo modificado:** `02.langfuse-secret.yaml` - campo `encryption-key`

---

## 3. Error: `secret "langfuse" not found`

### Descripción
Los pods de PostgreSQL, Redis y otros componentes fallan con `CreateContainerConfigError` porque no encuentran el secret.

### Causa
El chart de Helm busca un secret llamado `langfuse` por defecto, pero el secret creado tenía otro nombre (`langfuse-secrets`).

### Solución
Renombrar el secret a `langfuse` en el archivo `02.langfuse-secret.yaml`:

```yaml
metadata:
  name: langfuse  # No usar langfuse-secrets
```

Y asegurarse de que el `values.yaml` referencie el nombre correcto en todas las secciones (`postgresql`, `clickhouse`, `redis`, `s3`).

**Archivos modificados:** `02.langfuse-secret.yaml`, `03.values.yaml`

---

## 4. Error: `Can't reach database server at langfuse-postgresql:5432`

### Descripción
El pod `langfuse-web` no puede conectarse a PostgreSQL durante el inicio.

### Causa
El pod de PostgreSQL estaba en estado `Pending` o `CreateContainerConfigError` debido a problemas de recursos o configuración de secrets.

### Solución
1. Verificar que el secret `langfuse` exista y contenga la clave `postgresql-password`
2. Verificar que el pod de PostgreSQL esté en estado `Running`
3. Si el pod está en `Pending`, revisar los recursos del cluster (ver problema #6)

**Comando de diagnóstico:**
```bash
kubectl describe pod langfuse-postgresql-0 -n langfuse-test
```

---

## 5. Error: `failed to open database: dial tcp X.X.X.X:9000: connect: connection refused` (ClickHouse)

### Descripción
Las migraciones de PostgreSQL pasan correctamente, pero las migraciones de ClickHouse fallan porque no puede conectarse al puerto 9000.

### Causa
El pod de ClickHouse estaba en estado `Pending` debido a recursos insuficientes en el cluster.

### Solución
Verificar el estado del pod de ClickHouse y resolver los problemas de recursos (ver problema #6).

**Comando de diagnóstico:**
```bash
kubectl get pods -n langfuse-test | grep clickhouse
kubectl describe pod langfuse-clickhouse-shard0-0 -n langfuse-test
```

---

## 6. Error: `0/N nodes are available: N Insufficient cpu`

### Descripción
Los pods de ClickHouse, Zookeeper y/o PostgreSQL quedan en estado `Pending` indefinidamente.

### Causa
El cluster GKE no tiene suficientes recursos (CPU/memoria) para programar los pods. Esto ocurre porque:
- Los presets de recursos por defecto son muy altos (ej: ClickHouse usa `2xlarge` = 500m CPU)
- El autoscaler tiene un límite máximo de nodos alcanzado
- Las máquinas del cluster son pequeñas (ej: `e2-medium` = 2 vCPU, 4GB RAM)

### Solución

**Opción A: Reducir recursos en `values.yaml`**

Usar `resourcesPreset: "none"` y especificar recursos mínimos explícitos:

```yaml
clickhouse:
  resourcesPreset: "none"
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
```

Aplicar lo mismo para `zookeeper`, `postgresql`, `redis` y `s3`.

**Opción B: Aumentar capacidad del cluster**

```bash
# Aumentar límite de autoscaling
gcloud container clusters update <cluster-name> \
  --zone <zone> \
  --node-pool <pool-name> \
  --enable-autoscaling \
  --max-nodes 5

# O agregar un node pool con máquinas más grandes
gcloud container node-pools create langfuse-pool \
  --cluster <cluster-name> \
  --zone <zone> \
  --machine-type e2-standard-4 \
  --num-nodes 1
```

**Archivo modificado:** `03.values.yaml` - secciones de recursos de cada componente

---

## 7. Pods en `CrashLoopBackOff` después de resolver dependencias

### Descripción
Después de que ClickHouse y otros servicios están `Running`, el pod `langfuse-web` sigue en `CrashLoopBackOff` con muchos restarts acumulados.

### Causa
El pod tiene un backoff exponencial por los restarts previos y no intenta reconectarse inmediatamente a las nuevas dependencias.

### Solución
Eliminar el pod manualmente para forzar su recreación con un contador de restarts limpio:

```bash
kubectl delete pod <nombre-del-pod> -n langfuse-test
```

El ReplicaSet creará automáticamente un nuevo pod que se conectará a las dependencias ahora disponibles.

---

## Comandos útiles de diagnóstico

```bash
# Ver estado de todos los pods
kubectl get pods -n langfuse-test

# Ver eventos de un pod específico
kubectl describe pod <nombre-pod> -n langfuse-test | grep -A 15 "Events:"

# Ver logs de un pod
kubectl logs <nombre-pod> -n langfuse-test --tail=50

# Ver recursos solicitados por un pod
kubectl get pod <nombre-pod> -n langfuse-test -o jsonpath='{.spec.containers[*].resources}'

# Ver recursos disponibles en los nodos
kubectl describe nodes | grep -A 10 "Allocated resources:"

# Ver configuración del cluster GKE
gcloud container clusters describe <cluster-name> --zone <zone>
```

---

## Resumen de archivos de configuración

| Archivo | Propósito |
|---------|-----------|
| `01.setup-base.sh` | Comandos para setup de GKE y despliegue con Helm |
| `02.langfuse-secret.yaml` | Kubernetes Secret con credenciales |
| `03.values.yaml` | Configuración personalizada del chart de Helm |

---

## Referencias

- [Documentación oficial de Langfuse - Kubernetes Helm](https://langfuse.com/self-hosting/deployment/kubernetes-helm)
- [Configuración de variables de entorno](https://langfuse.com/self-hosting/configuration)
- [Repositorio langfuse-k8s](https://github.com/langfuse/langfuse-k8s)
