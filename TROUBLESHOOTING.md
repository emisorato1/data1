# Troubleshooting Guide - Enterprise AI Platform

Este documento centraliza los problemas comunes encontrados durante el despliegue y estabilización de la plataforma, junto con sus soluciones técnicas.

---

## 1. Langfuse: Conectividad y Despliegue

### Error: `CrashLoopBackOff` en `langfuse-web` (P1001: Can't reach database)
**Problema:** El pod de Langfuse no puede conectar a la base de datos de Cloud SQL porque falta el sidecar de `cloud-sql-proxy`.
**Solución:**
- Asegurarse de incluir la configuración de `extraContainers` en el `values.yaml` de Langfuse.
- Langfuse v3 usa `langfuse.extraContainers` (no a nivel de `web/worker` individualmente si se usa el chart oficial v1.5.20+).
- **Sidecar Requerido:** `gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.14.3` con argumentos `--private-ip` y el nombre de conexión correcto.

### Error: `JavaScript heap out of memory` (OOM)
**Problema:** Langfuse v3 consume más de 512Mi de RAM durante el arranque (migraciones de Prisma).
**Solución:** 
- Incrementar `resources.requests.memory` a `512Mi` y `limits.memory` a `1Gi`.
- Aumentar `initialDelaySeconds` en los liveness/readiness probes a `120s` para dar tiempo a las migraciones.

### Error: Falla de validación S3 en Helm
**Problema:** `s3.[eventUpload].bucket is required`.
**Solución:** Aunque se use GCS, el chart de Langfuse a veces requiere que las secciones de S3 existan. Configurar:
```yaml
storageProvider: gcs
s3:
  batchExport:
    bucket: "nombre-bucket"
  mediaUpload:
    bucket: "nombre-bucket"
  eventUpload:
    bucket: "nombre-bucket"
```

---

## 2. Autenticación y Cuentas

### Problema: Credenciales de Admin desconocidas o Sign-up deshabilitado
**Solución:** Forzar la creación/reset de contraseña directamente en la base de datos desde el pod:
```bash
kubectl exec -it deployment/langfuse-web -n langfuse -c langfuse-web -- sh -c '
DATABASE_URL="postgresql://${DATABASE_USERNAME}:${DATABASE_PASSWORD}@${DATABASE_HOST}:${DATABASE_PORT}/${DATABASE_NAME}" \
node -e "
const { PrismaClient } = require(\"@prisma/client\");
const bcrypt = require(\"bcryptjs\");
const prisma = new PrismaClient();
async function main() {
  const hash = await bcrypt.hash(\"NUEVA_PASSWORD\", 10);
  await prisma.user.upsert({
    where: { email: \"admin@macroai.dev\" },
    update: { password: hash },
    create: { email: \"admin@macroai.dev\", name: \"Admin\", password: hash }
  });
}
main().catch(console.error).finally(() => prisma.\$disconnect());
"
'
```

---

## 3. RAG y Permisos (ACL)

### Problema: El chat responde "No tengo información suficiente" (Retrieved 0 chunks)
**Causa 1: Desconexión de IDs (Security Mirror vs Vector Store)**
- El índice vectorial (`document_chunks`) usa IDs originales de OpenText (ej: `17957851`).
- La tabla de permisos (`dtreeacl`) a veces tiene IDs secuenciales de prueba (ej: `2000, 2001`).
**Solución:** Mapear las ACLs a los IDs que realmente existen en el índice:
```python
# Script para ejecutar vía `kubectl exec api-pod`
res = conn.execute(text("SELECT DISTINCT document_id FROM document_chunks"))
real_ids = [row[0] for row in res]
for d_id in real_ids:
    conn.execute(text("INSERT INTO dtreeacl (data_id, right_id, permissions) VALUES (:d_id, 1000, 2)"), {"d_id": d_id})
```

**Causa 2: Falta de instrumentación o callbacks**
- Los nodos tenían `@observe` pero el flujo principal y el streaming de Gemini no.
- LangGraph no estaba recibiendo el `CallbackHandler` en el `config`.
**Solución:** 
- Decorar `stream_rag_events` con `@observe(name="chat_flow")`.
- Pasar `get_langfuse_callback()` en la configuración de `ainvoke` y del LLM.
- Llamar a `flush_langfuse()` al finalizar el streaming para forzar el envío de datos.

**Causa 3: ClickHouse Ingestion Lag**
- Si el Langfuse Worker muestra errores de `ClickhouseWriter`, las trazas no aparecerán en la UI.
**Solución:** Reiniciar ClickHouse y el Worker para limpiar conexiones muertas:
```bash
kubectl delete pod langfuse-clickhouse-shard0-0 -n langfuse
kubectl rollout restart deployment langfuse-worker -n langfuse
```

---

## 4. Mantenimiento del Cluster

### Limpieza de puertos locales (Port-forward)
Para reiniciar todos los túneles locales si se quedan colgados:
```bash
lsof -ti:3000,3001,8000,8080 | xargs kill -9
```

### Limpieza de Pods Pendientes/Error
Si el cluster tiene `Insufficient CPU`, eliminar pods en estado `Pending` o `Error` de despliegues viejos:
```bash
kubectl get pods -A | grep -iE "Error|Pending|CrashLoop" | awk "{print $2 \" -n \" $1}" | xargs -n 3 kubectl delete pod
```
