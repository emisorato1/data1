# Core

Componentes compartidos y reutilizables del sistema. Contiene la gestión centralizada de modelos LLM con múltiples providers (OpenAI, Ollama, vLLM), modelos de base de datos (PostgreSQL + pgvector), repositorios, schemas Pydantic, configuración global, seguridad (autenticación, guardrails de input/output) y el checkpointer custom de LangGraph integrado con trace_id. Todo servicio backend depende de este núcleo para garantizar consistencia en la comunicación con LLMs, manejo de datos y políticas de seguridad.

