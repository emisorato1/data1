# T4-S6-02: Sanitizacion PII en recuerdos almacenados via Cloud DLP

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Lautaro) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | - |
| Depende de | T4-S5-01 (done) |
| Skill | `chat-memory/SKILL.md` + `guardrails/SKILL.md` |
| Estimacion | M (2-4h) |

## Contexto

Las memorias episodicas (de T4-S5-01) pueden contener PII que los usuarios mencionan durante las conversaciones (nombres, numeros de documento, numeros de cuenta). Almacenar PII en memoria de largo plazo es un riesgo de compliance bajo la Ley 25.326 (PDPA Argentina). Las memorias deben ser sanitizadas antes del almacenamiento usando GCP Sensitive Data Protection (Cloud DLP) para garantizar deteccion de nivel enterprise, consistente con la arquitectura definida en el diagrama de secuencia UML incluido abajo.

## Spec

Implementar una capa de integracion con Cloud DLP que sanitice las memorias extraidas via `content.deidentify` antes de almacenarlas en la tabla `episodic_memories`. El cliente DLP wrappea la API de Google Cloud DLP y es reutilizable por specs futuras (T4-S9-01 para guardrails de salida).

## Criterios de Aceptacion

- [x] Cliente DLP reutilizable en `src/infrastructure/security/dlp_client.py`
- [x] Llamada a `content.deidentify` con InfoTypes argentinos configurados
- [x] InfoTypes: PERSON_NAME, PHONE_NUMBER, EMAIL_ADDRESS + custom: ARGENTINA_DNI, ARGENTINA_CUIT_CUIL, ARGENTINA_CBU
- [x] Custom InfoTypes definidos via regex en la configuracion del cliente DLP
- [x] Tokens de reemplazo semanticos: [NOMBRE], [DNI], [CUIT], [CBU], [TELEFONO], [EMAIL]
- [x] Sanitizacion ejecutada entre extraccion y almacenamiento de memorias (en `MemoryService`)
- [x] Memoria sanitizada mantiene utilidad semantica (el contexto se preserva)
- [x] Configurable: InfoTypes y tokens surrogate extensibles via diccionario
- [x] Fallback a regex local si Cloud DLP no esta disponible (resiliencia)
- [x] Setting `dlp_enabled: bool` en config para habilitar/deshabilitar
- [x] Tests unitarios con mocks de la API DLP para memorias con PII y memorias limpias
- [x] Tests del fallback regex local

## Archivos a crear/modificar

- `src/infrastructure/security/dlp_client.py` (crear — wrapper Cloud DLP reutilizable)
- `src/infrastructure/security/pii_sanitizer.py` (crear — fallback regex local)
- `src/application/services/memory_service.py` (modificar — integrar sanitizacion pre-storage)
- `src/config/settings.py` (modificar — agregar `dlp_enabled`, `dlp_min_likelihood`)
- `src/infrastructure/security/__init__.py` (modificar — exportar nuevos modulos)
- `tests/unit/test_dlp_client.py` (crear)
- `tests/unit/test_pii_sanitizer.py` (crear)
- `pyproject.toml` (modificar — agregar `google-cloud-dlp`)

## Decisiones de diseno

- **Cloud DLP como motor primario**: Usa `content.deidentify` de GCP Sensitive Data Protection. Los InfoTypes built-in (PERSON_NAME, PHONE_NUMBER, EMAIL_ADDRESS) se combinan con custom InfoTypes via regex para patrones argentinos (DNI, CUIT/CUIL, CBU).
- **Tokens surrogate**: La configuracion de deidentify usa `SurrogateType` para reemplazar cada InfoType con su token semantico (ej: `[DNI]`, `[NOMBRE]`). Esto preserva la utilidad del recuerdo.
- **Sanitizar antes de almacenar**: Una vez almacenado sin PII, no hay riesgo de fuga. Compliance by design (Ley 25.326 Art. 9).
- **Fallback regex local**: Si DLP no esta disponible (red, quota, permisos), se usa un sanitizer regex local con los mismos patrones argentinos como degradacion graceful.
- **Cliente reutilizable**: El `DLPClient` expone metodos `deidentify()` e `inspect()` que seran reutilizados por T4-S9-01 (deteccion PII en salida).
- **Auth via ADC**: Usa la misma infraestructura de credenciales del proyecto (ADC en dev, Workload Identity en GKE). No requiere service account keys adicionales.

## Diagrama UML

```puml
@startuml
skinparam style strictuml
skinparam sequenceMessageAlign center
skinparam BoxPadding 12
skinparam ParticipantPadding 10
title Flujo RAG con GCP Sensitive Data Protection (DLP)\nCompliance: Ley 25.326 (PDPA Argentina) + PCI DSS
box "Infraestructura de Datos (Batch)" #F8F9FA
    participant "Origen\n(PDF / DOCX)" as DB
    participant "Pipeline Ingesta\n(Airflow DAG)" as ETL
    participant "Vector DB\n(pgvector)" as VDB
end box
box "GCP Sensitive\nData Protection" #E1F5FE
    participant "Cloud DLP\nService" as DLP
end box
box "Capa de Aplicacion (Real-time)" #FFF3E0
    participant "RAG Engine\n(FastAPI / LangGraph)" as APP
    participant "LLM\n(Vertex AI / Gemini)" as LLM
end box
actor "Usuario Final" as User
' ============================================================
' FASE 1: INDEXACION PROTEGIDA
' ============================================================
== FASE 1: INDEXACION PROTEGIDA (batch) ==
DB -> ETL: Documentos crudos (PDF, DOCX)
ETL -> ETL: Carga y chunking\n(LoaderFactory + AdaptiveChunker)
ETL -> DLP: content.deidentify\n(chunks de texto crudo)
note right of DLP
    Detecta Y anonimiza en un solo paso:
    - ARGENTINA_DNI_NUMBER  → [DNI]
    - CREDIT_CARD_NUMBER    → [TARJETA]
    - CUIT_CUIL (custom)    → [CUIT]
    - CBU (custom)          → [CBU]
    - IBAN_CODE             → [IBAN]
    - EMAIL_ADDRESS         → [EMAIL]
    - PHONE_NUMBER          → [TELEFONO]
    - PERSON_NAME           → [NOMBRE]
    - STREET_ADDRESS        → [DIRECCION]
end note
DLP --> ETL: Chunks anonimizados\n(tokens reemplazados, estructura preservada)
ETL -> ETL: Generacion de embeddings\n(GeminiEmbeddingService 768-d)
ETL -> VDB: Upsert vectores + metadata limpia
note over VDB
    El indice vectorial NUNCA
    contiene datos sensibles reales.
    Compliance by design.
end note
' ============================================================
' FASE 2: CONSULTA DEL USUARIO (INPUT GUARDRAIL)
' ============================================================
== FASE 2: CONSULTA Y CONTROL DE ENTRADA (real-time) ==
User -> APP: Query del usuario
APP -> DLP: content.inspect\n(query del usuario)
note right of DLP
    Fast-tier (baja latencia):
    - ARGENTINA_DNI_NUMBER
    - CREDIT_CARD_NUMBER
    - CUIT_CUIL (custom)
    - CBU (custom)
    - IBAN_CODE
    - EMAIL_ADDRESS
    - PHONE_NUMBER
    - SWIFT_CODE
    min_likelihood = LIKELY
end note
alt PII detectado en la query
    DLP --> APP: Findings (datos sensibles en la consulta)
    APP --> User: "Por seguridad no proceso datos personales.\nReformule su consulta sin incluir datos sensibles."
    note right of APP #FFE0E0
        Fail-closed.
        El dato sensible no ingresa
        al motor RAG ni al LLM.
        Ley 25.326 Art. 9 —
        principio de minima exposicion.
    end note
else Query segura
    DLP --> APP: Sin hallazgos
    APP -> VDB: Busqueda de similitud hibrida\n(vector + BM25 + RRF reranking)
    VDB --> APP: Contexto relevante (ya anonimizado)
    APP -> LLM: Prompt = contexto anonimizado + query
    LLM --> APP: Respuesta generada (tentativa)
    ' ============================================================
    ' FASE 3: CONTROL DE SALIDA (OUTPUT GUARDRAIL)
    ' ============================================================
    == FASE 3: CONTROL DE SALIDA (real-time) ==
    APP -> DLP: content.inspect\n(respuesta generada)
    note right of DLP
        Fast-tier identico al de la query.
        Detecta PII que el LLM pudo
        haber "alucinado" o reconstruido
        a partir del contexto.
    end note
    alt PII detectado en la respuesta
        DLP --> APP: Findings (patron sensible detectado)
        APP -> APP: Redaccion automatica\n(reemplazar hallazgo por [REDACTED])
        note right of APP #FFF9C4
            La respuesta sigue siendo util.
            Solo el dato sensible es enmascarado.
            Si la redaccion falla → fallback total
            (fail-closed como ultima linea de defensa).
        end note
    end
    APP -> LLM: Verificar fidelidad al contexto\n(faithfulness judge — Gemini Flash Lite)
    note right of LLM
        Unico uso del LLM como juez:
        detectar alucinaciones factuales
        que DLP no puede evaluar.
        Fail-open: si falla el LLM,
        la respuesta se permite.
    end note
    alt Respuesta no fiel al contexto (alucinacion)
        LLM --> APP: UNFAITHFUL
        APP --> User: Mensaje de fallback seguro
    else Respuesta fiel
        LLM --> APP: FAITHFUL
        APP --> User: Respuesta final segura\n(anonimizada si correspondia)
    end
end
@enduml
```

## Fuera de alcance

- Deteccion PII en respuestas del LLM (spec T4-S9-01 — usara `DLPClient.inspect()` de esta spec)
- Deteccion PII en queries de entrada (spec futura — usara `DLPClient.inspect()` de esta spec)
- Sanitizacion de chunks en pipeline de indexacion (spec futura — usara `DLPClient.deidentify()` de esta spec)
- Encriptacion de memorias
- GDPR delete (spec T3-S10-01)