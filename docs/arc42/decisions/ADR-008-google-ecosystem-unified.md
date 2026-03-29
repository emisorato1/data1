# ADR-008: Ecosistema Google Unificado (Gemini + Vertex AI)

## Status

**Accepted**

## Date

2026-02-13

## Context

El sistema RAG requiere múltiples servicios de IA:
- **Embeddings**: Vectorizar documentos y queries
- **Generación LLM**: Producir respuestas a partir de contexto
- **Reranking**: Reordenar resultados por relevancia
- **Guardrails**: Clasificación de inputs/outputs (prompt injection, faithfulness)
- **Evaluación**: Métricas RAGAS offline

Debemos decidir si usar un solo ecosistema o múltiples proveedores.

## Considered Options

### Opción 1: Ecosistema Google unificado

Gemini para embeddings y generación, Vertex AI para reranking.

### Opción 2: Multi-proveedor

OpenAI para generación, Cohere para embeddings/reranking, Gemini como fallback.

### Opción 3: Open-source local

Modelos locales (Llama, Mistral) para generación, sentence-transformers para embeddings.

## Decision

**Ecosistema Google unificado (Opción 1). Prohibido OpenAI y Cohere.**

### Asignación de modelos por función

| Función | Modelo | Justificación |
|---------|--------|---------------|
| **Embeddings** | Gemini text-embedding-004 (768d) | Gratuito (cuota generosa), excelente español, Matryoshka |
| **Generación (complejo)** | Gemini 2.0 Flash | Balance costo/calidad para razonamiento largo |
| **Generación (simple)** | Gemini 2.0 Flash Lite | Latencia ultra-baja, consultas directas |
| **Guardrails input** | Gemini 2.0 Flash Lite | Latencia mínima, clasificación rápida |
| **Reranking** | Vertex AI semantic-ranker-512@latest | Diseñado para reordenamiento, español |
| **Evaluación RAGAS** | Gemini 2.0 Flash Lite | Offline, bajo costo, batch |

### Costos estimados

| Componente | Costo / 1K queries |
|------------|-------------------|
| Embeddings (Gemini) | $0 (cuota gratuita) |
| Reranking (Vertex AI) | ~$0.30 |
| Generación (Gemini 2.0 Flash) | ~$0.30 - $0.60 |
| **Total** | **~$0.60 - $1.20 / 1K queries** |

### Justificación sobre alternativas

| Criterio | Google unificado | Multi-proveedor | Open-source local |
|----------|------------------|----------------|-------------------|
| Costo embeddings | Gratis | $0.10-0.20/1M tokens | Infra de GPU |
| Calidad español | Excelente (Gemini) | Variable | Inferior |
| Vendor management | 1 proveedor, 1 SDK | 3+ proveedores, 3+ SDKs | Self-managed |
| Latencia | Red interna GCP | Network hops entre clouds | Depende de GPU |
| Consistencia | Misma tokenización | Diferentes tokenizadores | Diferentes modelos |
| Compliance | Google Cloud (SOC2, ISO27001) | Múltiples contratos | Self-managed |
| Soporte bancario | Google Cloud enterprise | Múltiples SLAs | Sin soporte |

## Consequences

### Positivas

- Un solo proveedor: simplifica contratos, billing, soporte, compliance
- Un solo SDK: `langchain-google-genai` / `langchain-google-vertexai`
- Consistencia de tokenización entre embeddings y generación
- Embeddings gratuitos con cuota generosa
- Red interna GCP: latencia mínima entre servicios (deploy en GKE)
- Compliance simplificada: un solo acuerdo de procesamiento de datos

### Negativas

- Vendor lock-in a Google Cloud (mitigado: LangChain abstrae los providers)
- Si Gemini degrada calidad, no hay fallback inmediato a otro LLM
- Dependencia de cuota gratuita de embeddings (si se excede, hay costo)

### Mitigación de vendor lock-in

La arquitectura hexagonal con `src/infrastructure/llm/client.py` abstrae el proveedor LLM. Cambiar de Gemini a otro modelo requiere:
1. Implementar un nuevo client en `infrastructure/llm/`
2. Cambiar la inyección de dependencias
3. No se toca domain ni application layer

## References

- [Gemini Embeddings](https://ai.google.dev/gemini-api/docs/embeddings)
- [Vertex AI Gemini](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)
- [Vertex AI Ranking API](https://cloud.google.com/vertex-ai/docs/generative-ai/ranking)
