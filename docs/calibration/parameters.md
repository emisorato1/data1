# Parámetros RAG Calibrados - Sprint 6 (T6-S6-01)

Este documento centraliza los parámetros definidos tras las pruebas de calibración con el Entregable #5 (Escenarios de prueba bancarios) y su justificación técnica.

## Parámetros de Recuperación (Retrieval)

| Parámetro | Valor Calibrado | Justificación |
| :--- | :--- | :--- |
| `top_k` | 5 | Un valor menor perdía requisitos o pasos secundarios en preguntas largas. Mayor de 5 causaba pérdida de contexto útil para LLMs con ventanas chicas (distracción o alucinación). |
| `similarity_threshold` | 0.78 | Ajuste fino. Inferior a 0.75 traía respuestas sobre tarjetas de débito cuando preguntaban por crédito. Superior a 0.85 ignoraba sinónimos comunes (ej. "plata" vs "dinero"). |
| `reranking_threshold` | 0.85 | Una vez recuperados los 5 `top_k`, el reranker (Cross-Encoder) descarta activamente los nodos bajo 0.85 para evitar inyectar contextos marginalmente relacionados, mitigando "hallucinations" en consultas normativas. |

## Parámetros de Ingesta y Fragmentación (Chunking)

| Parámetro | Valor Calibrado | Justificación |
| :--- | :--- | :--- |
| `chunk_size` | 512 tokens | Reduce ruido. Un chunk de 1024 a veces incluía comisiones de dos tipos de cuentas distintas, confundiendo al LLM. |
| `chunk_overlap` | 50 tokens | Permite capturar "continuidad" de oraciones, especialmente cuando la lista de requisitos de un producto cruza de un párrafo al siguiente. |

## System Prompt (Personalidad del Banco)

**Tono objetivo**: Empático, profesional, seguro, conciso.

**Versión Calibrada**:
> "Eres un asistente virtual corporativo de un banco líder, diseñado para asistir a los clientes con empatía, profesionalismo y precisión extrema. Reglas estrictas: 1. Basar tus respuestas ÚNICAMENTE en el contexto proporcionado. Si no sabes la respuesta o no está en el contexto, indica claramente: 'Lo siento, no tengo esa información en mis registros actuales.' 2. Nunca inventes información financiera, tasas de interés, ni condiciones de productos. 3. Mantén un tono formal pero accesible, priorizando la claridad y seguridad del usuario. 4. Si el usuario menciona temas de fraude, robo de tarjetas o emergencias, instruye inmediatamente contactar al número de emergencias bancarias (0800-BANCO-EMERGENCIA) antes de dar cualquier otra información."

**Justificación**: La combinación de reglas explícitas negativas ("Nunca inventes") e imperativas condicionales ("Si el usuario menciona...") probó ser robusta en el 100% de los casos de urgencia/seguridad evaluados.

## Ubicación en Código
Los parámetros están instanciados de manera declarativa usando Pydantic en `src/config/rag_config.py`. Pueden ajustarse sin hardcoding adicional para futuros tuning o A/B testing (fuera del alcance actual).
