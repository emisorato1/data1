# T1-S7-01: Fix y evolución de instrumentación Langfuse

## Meta

| Campo | Valor |
|-------|-------|
| Track | T1 (Agus) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | - (mejora observabilidad para todo el equipo) |
| Depende de | T1-S2-03 (instrumentación original) |
| Skill | `observability/SKILL.md` + `observability/references/logging-config.md` |
| Estimacion | M (2-4h implementado + 2-4h mejoras) |
| Branch | `feature/langfuse-tracing-fix` |

## Contexto

La instrumentación original de Langfuse (T1-S2-03) cubría la inicialización básica del cliente y el decorador `@observe`. En la práctica, se detectaron problemas críticos:

1. **Pérdida de trazas en streaming async**: FastAPI cerraba el scope del worker antes de que el buffer del SDK de Langfuse se vaciara, resultando en trazas incompletas o perdidas.
2. **Falta de integración profunda con LangGraph**: Los nodos del grafo RAG no se reportaban como spans hijos de la traza principal.
3. **Sin degradación graceful**: Si el SDK no estaba instalado o Langfuse estaba deshabilitado, la app fallaba en lugar de continuar sin instrumentación.

Esta spec formaliza el trabajo correctivo y evolutivo realizado por Agus en el branch `feature/langfuse-tracing-fix`, y define mejoras adicionales pendientes para completar la solución de observabilidad.

## Spec

Refactorizar el cliente de Langfuse como un wrapper centralizado con inicialización lazy, feature flag (`LANGFUSE_ENABLED`), degradación graceful si el SDK no está disponible, y flush explícito para entornos de streaming async. Instrumentar los métodos core del LLM client y el use case principal con decoradores `@observe` y callbacks de LangGraph.

## Arquitectura de la solución

```
┌──────────────────────────────────────────────────────────────┐
│  FastAPI /stream endpoint                                    │
│  └─ stream_rag_events() @observe("chat_flow")                │
│      ├─ propagate_attributes(user_id, session_id, tags)      │
│      ├─ LangGraph.ainvoke(callbacks=[CallbackHandler()])     │
│      │   ├─ classify_query node (reported via callback)      │
│      │   ├─ validate_input node (reported via callback)      │
│      │   ├─ retrieve node (reported via callback)            │
│      │   ├─ rerank node (reported via callback)              │
│      │   └─ assemble_context node                            │
│      ├─ GeminiClient.generate_stream()                       │
│      │   └─ @observe("llm_generate_stream", generation)      │
│      └─ flush_langfuse()  ← CRÍTICO para async               │
└──────────────────────────────────────────────────────────────┘
```

## Acceptance Criteria

### Implementado (branch `feature/langfuse-tracing-fix`)

- [x] `langfuse_client.py` como wrapper centralizado con inicialización lazy (singleton)
- [x] Feature flag `LANGFUSE_ENABLED` que convierte decoradores en no-op cuando está deshabilitado
- [x] Degradación graceful si el paquete `langfuse` no está instalado (try/except ImportError)
- [x] Función `observe()` exportada como decorador wrapper que respeta el feature flag
- [x] Función `get_langfuse_callback()` que retorna `CallbackHandler` para LangGraph
- [x] Función `flush_langfuse()` que vacía el buffer del SDK y del callback handler
- [x] Función `shutdown_langfuse()` para procesos batch (Airflow tasks)
- [x] Decorador `@observe(name="chat_flow")` en `stream_rag_events()` como traza root
- [x] Callback de Langfuse inyectado en `graph_config["callbacks"]` para LangGraph
- [x] Llamada a `flush_langfuse()` al final del stream antes de cerrar el scope de FastAPI
- [x] Decorador `@observe(name="llm_generate")` en `GeminiClient.generate()`
- [x] Decorador `@observe(name="llm_generate_structured")` en `GeminiClient.generate_structured()`
- [x] Decorador `@observe(name="llm_generate_stream")` en `GeminiClient.generate_stream()`
- [x] Decorador `@observe(name="embedding_generate")` en `GeminiClient.embed()`
- [x] Configuración en `settings.py`: `langfuse_enabled`, `langfuse_public_key` (SecretStr), `langfuse_secret_key` (SecretStr), `langfuse_host`
- [x] Documentación técnica: `LANGFUSE_INSTRUMENTATION_SPEC.md` con diagrama de secuencia Mermaid

### Correcciones requeridas (hallazgos de revisión contra SDK v3)

- [x] **CRITICAL — Eliminar singleton `CallbackHandler`**: `get_langfuse_callback()` retorna un singleton compartido entre requests, rompiendo el aislamiento de trazas por request. El SDK v3 requiere crear un `CallbackHandler()` fresh por request dentro de la función decorada con `@observe`, para que herede el trace context actual. Refactorizar `stream_rag_events()` para instanciar `CallbackHandler()` directamente en lugar de usar `get_langfuse_callback()`. Una vez aplicada esta corrección, **eliminar `get_langfuse_callback()` y `_callback_handler` de `langfuse_client.py`** ya que el wrapper no debe exponer un singleton de callback.
  ```python
  # Antes (singleton — trazas mezcladas entre requests)
  cb = get_langfuse_callback()
  graph_config = {"callbacks": [cb] if cb else []}

  # Después (fresh por request — hereda trace context)
  from langfuse.langchain import CallbackHandler
  handler = CallbackHandler()  # auto-config desde env vars
  graph_config = {"callbacks": [handler]}
  ```
- [x] **HIGH — Agregar `as_type="generation"` en decoradores LLM**: Los 4 `@observe` en `GeminiClient` usan el default `as_type="span"`. Deben usar `as_type="generation"` para que Langfuse los clasifique como generaciones LLM con UI específica (modelo, tokens, costo). Aplicar en: `generate()`, `generate_structured()`, `generate_stream()`, `embed()`.
  ```python
  @observe(name="llm_generate", as_type="generation")
  @observe(name="llm_generate_structured", as_type="generation")
  @observe(name="llm_generate_stream", as_type="generation")
  @observe(name="embedding_generate")  # embeddings no es generation
  ```
- [x] **MEDIUM — Renombrar `langfuse_host` a `langfuse_base_url`** en `settings.py` para alinear con la env var oficial del SDK v3 (`LANGFUSE_BASE_URL`). Actualizar `langfuse_client.py` correspondientemente.

### Mejoras pendientes

- [x] Inyectar `userId`, `session_id` y `tags` usando `propagate_attributes()` del SDK v3 (no parámetros del decorador) en `stream_rag_events()`:
  ```python
  from langfuse import propagate_attributes

  @observe(name="chat_flow")
  async def stream_rag_events(conversation_id, user_id, message, ...):
      with propagate_attributes(
          user_id=str(user_id),
          session_id=str(conversation_id),
          tags=["rag", query_type],
      ):
          handler = CallbackHandler()
          result = await rag_graph.ainvoke(input, config={"callbacks": [handler]})
  ```
- [x] Tests unitarios para `langfuse_client.py`:
  - Test `observe()` retorna no-op cuando `LANGFUSE_ENABLED=false`
  - Test `observe()` delega a `langfuse_observe` cuando habilitado
  - Test `get_langfuse()` inicializa cliente lazy (singleton)
  - Test `flush_langfuse()` invoca flush en cliente y callback
  - Test `shutdown_langfuse()` limpia estado global
  - Test degradación graceful cuando paquete no instalado (mock ImportError)
- [ ] Métricas custom en spans via `update_current_span()` y `set_current_trace_io()`:
  ```python
  from langfuse import get_client
  langfuse = get_client()

  @observe(name="llm_generate", as_type="generation")
  async def generate(self, prompt, ...):
      result = await self._llm.ainvoke(prompt)
      # Metadata a nivel de span (modelo, temperatura)
      langfuse.update_current_span(metadata={
          "model": self._model_name,
          "temperature": self._temperature,
      })
      # I/O a nivel de trace root (resumen de la interacción)
      langfuse.set_current_trace_io(
          input={"prompt": prompt[:200]},
          output={"response": str(result.content)[:200]},
      )
      return result
  ```
- [ ] Considerar `capture_input=False` en funciones que procesan datos PII para evitar capturar contenido sensible en Langfuse
- [x] Actualizar documentación interna del equipo con los nuevos patrones de instrumentación y troubleshooting (skill actualizado)

## Archivos creados/modificados

### Creados
- `src/infrastructure/observability/langfuse_client.py` — wrapper centralizado
- `LANGFUSE_INSTRUMENTATION_SPEC.md` — documentación técnica de la solución
- `TROUBLESHOOTING.md` — guía de troubleshooting (incluye sección Langfuse)

### Modificados
- `src/infrastructure/llm/client.py` — 4 decoradores `@observe` + import del wrapper
- `src/application/use_cases/rag/stream_response.py` — integración callbacks + flush
- `src/config/settings.py` — 4 campos de configuración Langfuse

### Por crear (mejoras)
- `tests/unit/infrastructure/observability/test_langfuse_client.py` — tests unitarios

## Decisiones de diseño

- **Wrapper sobre SDK directo**: Centraliza la lógica de feature flag y degradación en un solo lugar. Todo el equipo importa desde `langfuse_client.py`, nunca directo del SDK.
- **Flush explícito sobre autoflush**: En contextos async con `yield` (SSE streaming), el autoflush del SDK no se ejecuta a tiempo. El flush manual al final del generador garantiza entrega.
- **Callback + Decoradores (dual)**: Los callbacks capturan la ejecución interna de LangGraph (nodos), mientras que los decoradores capturan métodos del LLM client que se ejecutan fuera del grafo (fase 2 de streaming directo).
- **No-op decorator sobre condicional en cada call site**: Mover la lógica de habilitado/deshabilitado al decorator evita ensuciar el código de negocio con condicionales.
- **Singleton para Langfuse client, fresh por request para CallbackHandler**: El cliente Langfuse (`get_langfuse()`) es stateless y thread-safe, apropiado como singleton lazy. El `CallbackHandler` en cambio DEBE crearse fresh por request para heredar el trace context de la traza root actual — un singleton mezclaría trazas entre requests concurrentes (ver corrección CRITICAL).

## Configuración requerida

Variables de entorno en el Secret `rag-enterprise-ai-platform-secrets`:

| Variable | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `LANGFUSE_ENABLED` | bool | `true` | Activa/desactiva toda la instrumentación (custom, no nativo del SDK) |
| `LANGFUSE_PUBLIC_KEY` | SecretStr | — | Key pública del proyecto en Langfuse |
| `LANGFUSE_SECRET_KEY` | SecretStr | — | Key secreta para ingesta de trazas |
| `LANGFUSE_BASE_URL` | str | — | URL de la instancia (ej. `http://langfuse-web.langfuse.svc.cluster.local:3000`). Nota: actualmente en settings.py como `langfuse_host` — renombrar para alinear con SDK v3 |

## Hallazgos de revisión (auditoría contra SDK v3 oficial)

Revisión realizada comparando la implementación en el branch contra la documentación oficial de Langfuse SDK v3 (https://langfuse.com/docs/sdk/python).

| # | Severidad | Hallazgo | Archivo | Estado |
|---|-----------|----------|---------|--------|
| 1 | CRITICAL | Singleton `CallbackHandler` rompe aislamiento de trazas entre requests concurrentes | `langfuse_client.py:44-55` | Resuelto |
| 2 | HIGH | Falta `as_type="generation"` en decoradores LLM — Langfuse no clasifica como generaciones | `client.py:130,197,260,348` | Resuelto |
| 3 | HIGH | `propagate_attributes()` no implementado — sin user_id/session_id/tags en trazas | `stream_response.py:89` | Resuelto |
| 4 | MEDIUM | `langfuse_host` no alineado con env var oficial `LANGFUSE_BASE_URL` | `settings.py:59` | Resuelto |
| 5 | LOW | Diagrama de arquitectura incompleto (faltaban nodos classify_query, validate_input) | spec | Resuelto |
| 6 | LOW | Sin `capture_input=False` en funciones que procesan PII | `client.py` | Deferred |

## Out of scope

- Dashboard custom en Langfuse (configuración manual post-deploy)
- Cost tracking por query (spec separada T1-S5-02)
- RAGAS evaluation integration con Langfuse (spec T3-S5-01)
- Métricas Prometheus/Grafana (spec T1-S4-02)
- Fixes secundarios del branch (admin routes, graph nodes, middleware) — no relacionados con observabilidad
