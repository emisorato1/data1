# Integración de Langfuse (Guía Técnica)

Este documento detalla la implementación de **Langfuse** para la observabilidad y trazado (tracing) en el **API Gateway** (`enterprise-ai-platform`), así como una guía de solución de problemas basada en los desafíos encontrados durante la integración.

## 1. Implementación Actual

### 1.1 Arquitectura
La integración utiliza el **SDK de Python de Langfuse v3** en modo asíncrono. Debido a la naturaleza de la aplicación FastAPI y para evitar importaciones circulares, se ha implementado un patrón **Singleton** centralizado.

*   **Módulo Cliente:** `services/api/app/infrastructure/observability/langfuse_client.py`
    *   Maneja la inicialización única del cliente `Langfuse`.
    *   Expone funciones globales: `init_langfuse()`, `get_langfuse_client()` y `flush_langfuse()`.
    *   Configura el cliente usando las variables de entorno.

### 1.2 Configuración
Las credenciales se cargan desde las variables de entorno (definidas en `infra/dev/.env` o `docker-compose.yaml`):

```bash
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com  # Nota: 'base_url', no 'host'
```

### 1.3 Ciclo de Vida (Lifespan)
En `services/api/app/main.py`, el cliente se inicializa al arrancar la aplicación y se hace un `flush` al cerrarla para asegurar que no se pierdan trazas.

```python
# main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_langfuse()  # Inicializa singleton
    yield
    flush_langfuse() # Envía trazas pendientes al cerrar
```

### 1.4 Instrumentación Manual
Se optó por **instrumentación manual** sobre el uso de decoradores (`@observe`) para tener control total sobre el ciclo de vida del trace y manejar correctamente las operaciones asíncronas y los contextos de base de datos.

**Servicios Instrumentados:**
1.  **MessageService** (`services/api/app/application/services/message_service.py`):
    *   Endpoint: `/api/v1/messages/run`
    *   Trace Name: `message_send_and_receive`
    *   Registra: Mensaje del usuario, respuesta del RAG, conteo de fuentes.

2.  **ChatService** (`services/api/app/application/services/chat_service.py`):
    *   Endpoint: `/api/v1/chatbot` (Legacy/Alternativo)
    *   Trace Name: `chat_execute`

**Patrón de Código:**
```python
# Obtener cliente global
langfuse = get_langfuse_client()
trace = None

if langfuse and settings.LANGFUSE_ENABLED:
    try:
        # INICIO: Langfuse v3 usa start_observation()
        trace = langfuse.start_observation(
            name="operation_name",
            input={"param": value}
        )
    except Exception:
        pass

# ... Lógica de negocio ...

# FIN: Actualizar y cerrar
if trace:
    try:
        trace.update(output={"result": result})
        trace.end()  # CRÍTICO: Debe llamarse explícitamente en v3 manual
        langfuse.flush() # Recomendado en entornos serverless/async críticos
    except Exception:
        pass
```

---

## 2. Troubleshooting (Solución de Problemas)

Durante la implementación se resolvieron los siguientes problemas comunes. Úsalo como referencia si algo deja de funcionar.

### 2.1 Error: `'Langfuse' object has no attribute 'trace'`
*   **Causa:** Se estaba intentando usar métodos de la **API v2** (`trace()`) con el SDK de la **API v3**.
*   **Solución:** Usar `start_observation()` para crear nuevos traces o spans.
    *   ❌ `langfuse.trace(...)`
    *   ✅ `langfuse.start_observation(...)`

### 2.2 Error: No aparecen los Traces en el Dashboard
*   **Causa 1 (Flush):** En aplicaciones asíncronas, el proceso puede responder y cerrarse antes de que el SDK envíe los datos en segundo plano.
    *   **Solución:** Llamar a `langfuse.flush()` inmediatamente después de cerrar el trace (`trace.end()`) o configurar el ciclo de vida de la aplicación (`flush_langfuse()` en shutdown).
*   **Causa 2 (Configuración):** Uso incorrecto de parámetros de conexión.
    *   **Solución:** Asegurar que se usa `base_url` en lugar de `host`.
        *   ❌ `Langfuse(host=...)`
        *   ✅ `Langfuse(base_url=...)`

### 2.3 Error: `ImportError: cannot import name ... from partially initialized module`
*   **Causa (Circular Import):** `main.py` importaba servicios que a su vez importaban `main.py` para obtener el cliente de Langfuse.
*   **Solución:** Extraer la lógica de Langfuse a un módulo independiente (`app.infrastructure.observability.langfuse_client`) que no tenga dependencias de negocio.

### 2.4 Logs de Error: Conexión rechazada o Timeout
*   **Causa:** El contenedor de la API no puede alcanzar la URL de Langfuse.
*   **Solución:**
    *   Si usas Langfuse Cloud: Verificar salida a internet y URL `https://cloud.langfuse.com`.
    *   Si usas Langfuse Self-Hosted (Docker): Asegurar que el contenedor API está en la misma red docker y usar el nombre del servicio (ej. `http://langfuse-server:3000`).

### 2.5 Decorador `@observe` no funciona o da errores de contexto
*   **Causa:** Conflictos con el manejo de contexto asíncrono o sesiones de base de datos en FastAPI.
*   **Solución:** Usar el wrapper manual (`try...finally` con `start_observation` y `end`) descrito en la sección 1.4. Es más verboso pero infalible.
