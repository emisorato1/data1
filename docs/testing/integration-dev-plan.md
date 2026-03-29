# Plan de Pruebas de Integración DEV - T6-S8-01

## Meta

| Campo | Valor |
|-------|-------|
| Spec | T6-S8-01 |
| Ambiente | DEV (Kubernetes) |
| Fecha | 2026-03-26 |
| Responsables | Franco, Branko (Track T6) |

---

## Objetivo

Ejecutar y documentar pruebas de integración E2E en el ambiente DEV, cubriendo el pipeline RAG completo (API, frontend, Airflow, DB, GCS) para verificar que todos los componentes funcionan correctamente en conjunto antes de avanzar a testing de QA.

---

## Alcance

### En Scope
- Pruebas E2E del pipeline RAG completo
- Pruebas de rendimiento (latencia p95 < 5s)
- Pruebas de streaming SSE
- Pruebas de flujo de autenticación completo
- Pruebas de concurrencia (10 usuarios simultáneos)
- Pruebas de error recovery
- Documentación de bugs y corrección de críticos

### Out of Scope
- Testing con datos de producción
- Testing de seguridad profundo (Sprint 9)
- Testing de performance con carga extrema (Sprint 9)

---

## Componentes Bajo Prueba

1. **Backend API** (FastAPI)
   - Endpoints REST
   - Streaming SSE
   - Autenticación JWT
   - Manejo de errores

2. **Frontend** (Next.js)
   - UI conversacional
   - Streaming de respuestas
   - Manejo de sesiones

3. **Base de Datos** (PostgreSQL + pgvector)
   - Persistencia de documentos
   - Búsqueda vectorial
   - Transacciones

4. **Storage** (Google Cloud Storage)
   - Upload de documentos
   - Almacenamiento de chunks

5. **Airflow**
   - Pipeline de indexación
   - Pipeline de evaluación

6. **Servicios Externos**
   - Vertex AI (embeddings + LLM)
   - Langfuse (observabilidad)

---

## Casos de Prueba

### TC-DEV-001: E2E Pipeline RAG Completo

**Objetivo**: Verificar flujo completo upload -> indexing -> query -> response con citaciones

**Pre-condiciones**:
- Usuario autenticado en DEV
- Servicios activos (API, DB, GCS, Airflow)

**Pasos**:
1. Login de usuario en frontend
2. Upload de documento PDF (máx 10MB)
3. Verificar documento almacenado en GCS
4. Trigger pipeline de indexación en Airflow
5. Verificar chunks indexados en PostgreSQL
6. Realizar query relacionada al documento
7. Verificar respuesta con citaciones correctas
8. Verificar trazabilidad en Langfuse

**Criterios de Aceptación**:
- [ ] Upload exitoso (status 200)
- [ ] Documento en GCS con path correcto
- [ ] DAG de indexación ejecuta sin errores
- [ ] Chunks en DB con embeddings halfvec(768)
- [ ] Query retorna respuesta relevante
- [ ] Citaciones incluyen chunk_id, page_number, score
- [ ] Trace completo visible en Langfuse

**Datos de Prueba**:
- `docs/testing/fixtures/documento_prueba_normativa_bancaria.pdf`

---

### TC-DEV-002: Rendimiento Queries Standard

**Objetivo**: Verificar latencia p95 < 5 segundos para queries standard

**Pre-condiciones**:
- 50+ documentos indexados en DEV
- Base de conocimiento cargada

**Pasos**:
1. Ejecutar 100 queries representativas
2. Medir tiempo de respuesta (inicio query -> primer token)
3. Calcular percentil 95 (p95)
4. Analizar queries lentas (outliers)

**Criterios de Aceptación**:
- [ ] p95 latency < 5 segundos
- [ ] p50 latency < 2 segundos
- [ ] 0 timeouts en 100 queries
- [ ] Latencia consistente (sin spikes)

**Queries de Prueba**:
```
1. "¿Qué es el riesgo de crédito?"
2. "Explica los requisitos de capital bajo Basilea III"
3. "¿Cuáles son las políticas de AML/CFT?"
4. "Resume el proceso de onboarding de clientes"
5. "¿Qué documentos requiere una apertura de cuenta empresarial?"
... (95 queries adicionales)
```

---

### TC-DEV-003: Streaming SSE

**Objetivo**: Verificar que tokens llegan incrementalmente vía SSE

**Pre-condiciones**:
- Usuario autenticado
- Al menos 1 documento indexado

**Pasos**:
1. Iniciar query desde frontend
2. Abrir conexión SSE
3. Capturar eventos `data:` del stream
4. Verificar tokens llegan sin esperar respuesta completa
5. Verificar evento `[DONE]` al finalizar
6. Verificar manejo de reconexión en caso de drop

**Criterios de Aceptación**:
- [ ] Primer token llega en < 1 segundo
- [ ] Tokens llegan incrementalmente (no batch)
- [ ] Evento `[DONE]` recibido al finalizar
- [ ] Reconexión automática funciona (retry logic)
- [ ] UI actualiza en tiempo real

**Datos de Prueba**:
- Query: "Explica el proceso de gestión de riesgos operacionales en 200 palabras"

---

### TC-DEV-004: Flujo Autenticación Completo

**Objetivo**: Verificar login -> operaciones -> refresh -> logout

**Pre-condiciones**:
- Usuario registrado en DB DEV
- Credentials válidos

**Pasos**:
1. **Login**: POST `/auth/login` con email + password
2. Verificar cookie `access_token` (HTTPOnly, Secure)
3. Verificar cookie `refresh_token` (HTTPOnly, Secure)
4. **Operación autenticada**: GET `/chat/conversations` con access_token
5. Esperar expiración de access_token (15 min en DEV)
6. **Refresh**: POST `/auth/refresh` con refresh_token
7. Verificar nuevos tokens emitidos
8. **Logout**: POST `/auth/logout`
9. Verificar tokens revocados

**Criterios de Aceptación**:
- [ ] Login exitoso retorna tokens válidos
- [ ] Cookies con flags HTTPOnly + Secure
- [ ] Operaciones autenticadas funcionan
- [ ] Refresh exitoso renueva tokens
- [ ] Logout revoca tokens correctamente
- [ ] Requests post-logout retornan 401

**Datos de Prueba**:
- Email: `test-dev@banco.com`
- Password: `Test123!@#Dev`

---

### TC-DEV-005: Concurrencia 10 Usuarios

**Objetivo**: Verificar sistema maneja 10 usuarios simultáneos sin degradación

**Pre-condiciones**:
- 10 usuarios registrados en DEV
- Base de conocimiento cargada

**Pasos**:
1. Iniciar 10 sesiones simultáneas (threads/processes)
2. Cada usuario ejecuta secuencia:
   - Login
   - 5 queries diferentes
   - Upload de documento
   - 3 queries adicionales sobre su documento
   - Logout
3. Medir latencia y errores por usuario
4. Verificar no hay contención en DB
5. Verificar no hay race conditions

**Criterios de Aceptación**:
- [ ] 10 usuarios completan flujo sin errores
- [ ] Latencia < 5s p95 se mantiene
- [ ] 0 errores de concurrencia (locks, deadlocks)
- [ ] Cada usuario ve solo sus propios documentos
- [ ] Rate limiting funciona (429 si aplica)

**Herramientas**:
- `locust` para simulación de carga
- Configuración: `tests/integration/locustfile_dev.py`

---

### TC-DEV-006: Error Recovery

**Objetivo**: Verificar recuperación del sistema ante fallas de componentes

**Pre-condiciones**:
- Sistema funcionando en DEV
- Acceso a K8s para restart de pods

**Escenarios**:

#### 6.1: Reinicio API Pod
1. Identificar pod de API: `kubectl get pods -n rag-dev`
2. Eliminar pod: `kubectl delete pod <api-pod> -n rag-dev`
3. Verificar nuevo pod levanta automáticamente
4. Verificar health check pasa: GET `/health`
5. Verificar queries funcionan post-restart

**Criterio**: Sistema recupera en < 30 segundos

#### 6.2: Conexión DB Perdida
1. Simular timeout de DB (firewall rule temporal)
2. Verificar API retorna error 503
3. Restaurar conexión
4. Verificar API recupera automáticamente
5. Verificar próximas queries funcionan

**Criterio**: Recuperación automática sin restart manual

#### 6.3: Falla GCS Temporal
1. Simular error 503 en GCS (mock/proxy)
2. Intentar upload de documento
3. Verificar retry automático (exponential backoff)
4. Verificar error 500 con mensaje claro si falla definitivamente
5. Restaurar GCS
6. Verificar próximos uploads funcionan

**Criterio**: Retry automático con backoff, error claro al usuario

---

## Métricas de Éxito

| Métrica | Target | Crítico |
|---------|--------|---------|
| E2E pipeline success rate | 100% | Sí |
| p95 latency queries | < 5s | Sí |
| p50 latency queries | < 2s | No |
| SSE primer token | < 1s | Sí |
| Auth flow success rate | 100% | Sí |
| Concurrencia 10 users | 0 errores | Sí |
| Error recovery time | < 30s | No |
| Bugs críticos encontrados | 0 al cerrar | Sí |

---

## Ambiente DEV

### URLs
- **Frontend**: https://rag-dev.banco.com
- **API**: https://api-rag-dev.banco.com
- **Airflow**: https://airflow-rag-dev.banco.com
- **Langfuse**: https://langfuse-rag-dev.banco.com

### Credentials
- Almacenados en `1Password` vault `RAG-DEV`
- No incluir en repositorio

### Configuración K8s
- Namespace: `rag-dev`
- Cluster: `gke-rag-dev-cluster`
- Region: `us-central1`

---

## Priorización de Bugs

| Severidad | Definición | Acción |
|-----------|-----------|--------|
| **Crítico** | Bloquea funcionalidad core, sistema no usable | Fix inmediato antes de cerrar sprint |
| **Alto** | Afecta funcionalidad importante, hay workaround | Fix en Sprint 9 |
| **Medio** | Experiencia degradada, no bloquea uso | Backlog priorizado |
| **Bajo** | Cosmético, no afecta funcionalidad | Backlog |

---

## Registro de Ejecución

| Caso | Ejecutado Por | Fecha | Resultado | Notas |
|------|---------------|-------|-----------|-------|
| TC-DEV-001 | - | - | - | - |
| TC-DEV-002 | - | - | - | - |
| TC-DEV-003 | - | - | - | - |
| TC-DEV-004 | - | - | - | - |
| TC-DEV-005 | - | - | - | - |
| TC-DEV-006 | - | - | - | - |

---

## Dependencias

- **Dependencias externas**:
  - Acceso a K8s cluster DEV
  - Credentials para Vertex AI
  - Acceso a GCS bucket DEV
  - Usuarios de prueba creados

- **Dependencias internas**:
  - T6-S7-01: Testing interno completado ✅

---

## Aprobación

| Rol | Nombre | Firma | Fecha |
|-----|--------|-------|-------|
| Tech Lead | - | - | - |
| QA Lead | - | - | - |
| Product Owner | - | - | - |

---

## Referencias

- Spec: `specs/sprint-8/T6-S8-01_pruebas-integracion-dev.md`
- Skill: `testing-strategy/SKILL.md`
- Tests automatizados: `tests/integration/test_dev_*.py`
