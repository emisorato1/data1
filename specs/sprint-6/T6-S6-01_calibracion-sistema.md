# T6-S6-01: Calibracion sistema — parametros y respuestas

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Franco, Emi) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T6-S7-01 |
| Depende de | T3-S4-01 (done), T3-S4-02 (done), T4-S4-01 (done), [Entregable #5: Escenarios de prueba] |
| Skill | `prompt-engineering/SKILL.md` + `rag-retrieval/SKILL.md` |
| Estimacion | XL (8+h) |

## Contexto

With the MVP functional and test scenarios from the bank (Entregable #5), the system needs calibration: tuning RAG parameters (top-k, similarity thresholds, chunk overlap) and validating response quality against expected answers.

## Spec

Execute systematic calibration of RAG parameters and prompt engineering, validating against bank-provided test scenarios.

## Acceptance Criteria

- [x] Parametros RAG calibrados: top-k, similarity_threshold, reranking_threshold
- [x] System prompt optimizado para personalidad y tono del banco
- [x] Al menos 20 escenarios de prueba ejecutados y evaluados
- [x] Respuestas comparadas con expected answers del banco
- [x] Metricas de calidad: faithfulness > 0.8, relevancy > 0.8
- [x] Ajustes de filtros de seguridad validados con casos reales
- [x] Documento de calibracion con parametros finales y justificacion
- [x] Parametros comprometidos en configuracion (no hardcoded)

## Archivos a crear/modificar

- `docs/calibration/calibration-report.md` (crear)
- `docs/calibration/parameters.md` (crear)
- `src/config/settings.py` (modificar — parametros RAG calibrados)

## Decisiones de diseno

- **Iterativo**: Multiples rondas de ajuste basado en resultados.
- **Parametros en config**: Facil de ajustar sin redeploy.

## Out of scope

- Fine-tuning del modelo LLM
- Calibracion automatica
- A/B testing
