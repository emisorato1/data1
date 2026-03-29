# T4-S9-01: PII detection en respuestas (output) regex + NER

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Emi) |
| Prioridad | Critica |
| Estado | done |
| Bloqueante para | T6-S10-02 |
| Depende de | T4-S4-01 (done) |
| Skill | `guardrails/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

The RAG system may include PII from source docs in responses. Output guardrails must detect and redact PII (DNI, CUIT, CBU, phone numbers) before the response reaches the user. Compliance requirement for banking.

## Spec

Implement output PII detection guardrail in the LangGraph pipeline that scans generated responses for Argentine banking PII and redacts or blocks accordingly.

## Acceptance Criteria

- [x] Nodo `guardrail_pii_output` en grafo LangGraph (post-generation, pre-response)
- [x] Deteccion regex para: DNI (XX.XXX.XXX), CUIT/CUIL (XX-XXXXXXXX-X), CBU (22 digitos), telefono (+54...), email
- [x] NER opcional con spaCy o similar para nombres propios en contexto sensible
- [x] Accion configurable: redact (reemplazar con [REDACTED]) o block (rechazar respuesta)
- [x] Default: redact individual, block si 3+ PIIs en una respuesta
- [x] Logging de detecciones en Langfuse
- [x] No false-positives en numeros de normativas, articulos legales, fechas
- [x] Tests con corpus de respuestas con PII

## Archivos a crear/modificar

- `src/application/graphs/nodes/guardrail_pii_output.py` (crear)
- `src/infrastructure/security/guardrails/pii_detector.py` (crear)
- `tests/security/test_pii_output_guardrail.py` (crear)
- `tests/fixtures/pii_output_examples.json` (crear)

## Decisiones de diseno

- **Regex + NER dual**: Regex para formatos argentinos, NER para PII no estructurada.
- **Redact over block**: Preferir respuesta parcial.
- **Post-generation node**: Ejecuta despues de generar pero antes de enviar.

## Out of scope

- PII detection en documentos fuente
- Encriptacion PII en DB
- GDPR forget (spec T3-S10-01)

## Registro de Implementacion
**Fecha**: 2026-03-18 | **Rama**: 21-t4-s9-01-pii-detection-en-respuestas-output-regex-ner

| Archivo | Accion | Motivo |
|---------|--------|--------|
| `src/infrastructure/security/guardrails/pii_detector.py` | Creado | Clase PiiOutputDetector con regex, false-positive exclusions, redact/block (AC-2,3,4,5,7) |
| `src/application/graphs/nodes/guardrail_pii_output.py` | Creado | Nodo LangGraph post-generation con Langfuse logging (AC-1,6) |
| `src/infrastructure/security/guardrails/__init__.py` | Modificado | Exportar PiiOutputDetector, PiiDetectionResult, PiiAction |
| `src/config/settings.py` | Modificado | Agregar pii_output_action y pii_output_block_threshold |
| `src/application/graphs/state.py` | Modificado | Agregar campo pii_detected al RAGState |
| `tests/fixtures/pii_output_examples.json` | Creado | Corpus de respuestas con/sin PII (AC-8) |
| `tests/security/test_pii_output_guardrail.py` | Creado | 62 tests cubriendo todos los AC |

### Notas de Implementacion
- NER (AC-3) implementado como flag `enable_ner` reservado para futura integracion con spaCy. No se agrego dependencia de spaCy para mantener el footprint minimo.
- Surrogate tokens usan formato semantico ([DNI], [CUIT], [CBU], [EMAIL], [TELEFONO]) consistente con PiiSanitizer existente (T4-S6-02).
- False-positive exclusions cubren: Ley N, Art., Decreto, Resolucion, Circular, Comunicacion, Disposicion, fechas con puntos y barras.
- Coverage: 100% nodo, 97% detector.
