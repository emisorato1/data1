# Guía de Instrumentación y Observabilidad

Esta guía explica cómo utilizar el sistema de observabilidad (Langfuse + structlog) en el proyecto.

## 1. Logging Estructurado (structlog)

No uses el módulo `logging` estándar. Usa `structlog` para obtener logs en JSON (en prod) y con contexto automático.

```python
import structlog

logger = structlog.get_logger()

def mi_funcion():
    logger.info("procesando_documento", doc_id="123", status="ok")
```

### Contexto Automático
El middleware inyecta automáticamente:
- `request_id`
- `user_id`
- `trace_id` (si estás en un contexto de Langfuse)

## 2. Tracing con Langfuse

### Decorador `@observe`
Para trazar funciones completas (incluyendo latencia y errores):

```python
from src.infrastructure.observability.langfuse_client import observe

@observe(name="mi_proceso_complejo")
async def mi_proceso():
    # ...
```

### Integración con LangChain / LangGraph
Para trazar automáticamente llamadas a LLMs, recuperadores, etc., pasa el callback handler:

```python
from src.infrastructure.observability.langfuse_client import get_langfuse_callback

callback = get_langfuse_callback()
res = await chain.ainvoke({"input": "hola"}, config={"callbacks": [callback]})
```

## 3. Configuración (.env)

Asegúrate de tener las siguientes variables en tu `.env`:

```bash
LANGFUSE_ENABLED=True
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

## 4. Mejores Prácticas
- Usa nombres descriptivos en `@observe(name="...")`.
- Loggea eventos clave con contexto adicional.
- No loggees secretos ni PII (Personal Identifiable Information).
