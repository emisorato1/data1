# IA-35: Ajuste fino RAG con feedback usuarios reales

## Meta

| Campo | Valor |
|-------|-------|
| Track | T6 (Emi, Lautaro) |
| Prioridad | Alta |
| Estado | pending |
| Bloqueante para | T6-PS-03 |
| Depende de | T6-PS-01 |
| Skill | `rag-retrieval/SKILL.md` + `prompt-engineering/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

With real production usage data and feedback, the RAG pipeline can be fine-tuned for better performance. This includes adjusting retrieval parameters, prompts, and guardrail thresholds based on actual user patterns.

## Spec

Analyze production feedback and usage patterns, then optimize RAG parameters (retrieval, generation, guardrails) based on real data.

## Acceptance Criteria

- [ ] Analisis feedback usuarios: thumbs up/down patterns, queries fallidas
- [ ] Identificacion top queries problematicas (baja calidad, timeout, off-topic)
- [ ] Ajuste parametros retrieval: top-k, similarity threshold, reranking
- [ ] Ajuste prompts si necesario (system prompt, few-shot examples)
- [ ] Ajuste thresholds guardrails si false positive rate > target
- [ ] Re-evaluacion RAGAS con datos produccion (metricas antes vs despues)
- [ ] Deploy de ajustes via CD pipeline

## Archivos a crear/modificar

- `docs/calibration/production-tuning-report.md` (crear)

## Decisiones de diseno

- **Data-driven tuning**: Basado en datos reales, no en suposiciones.
- **Incremental adjustments**: Cambios pequenos, medibles.

## Out of scope

- Model fine-tuning (Gemini), new features, architecture changes
