# T4-S5-01: Extraccion automatica recuerdos episodicos

## Meta

| Campo | Valor |
|-------|-------|
| Track | T4 (Emi) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T4-S5-02, T4-S6-02 |
| Depende de | - |
| Skill | `chat-memory/SKILL.md` |
| Estimacion | L (4-8h) |

## Contexto

The current system has short-term memory via LangGraph checkpointers. For a truly intelligent assistant, it needs long-term memory that extracts and stores key facts from conversations for future reference.

## Spec

Implement an episodic memory extraction node that runs post-generation, identifies key facts/preferences from the conversation, and stores them as memory entries in the database.

## Acceptance Criteria

- [x] Nodo `extract_memories` en el grafo LangGraph (post-generation)
- [x] Extraccion de hechos clave usando Gemini Flash (prompt dedicado)
- [x] Tipos de recuerdos: preferencia_usuario, hecho_mencionado, contexto_laboral, instruccion_explicita
- [x] Tabla `episodic_memories` con: user_id, memory_type, content, embedding, confidence, created_at, last_accessed
- [x] Migracion Alembic para tabla `episodic_memories`
- [x] Deduplicacion: no almacenar recuerdos redundantes (similarity check con embeddings)
- [x] Confidence score: solo almacenar recuerdos con confidence > 0.7
- [x] Tests unitarios de extraccion y deduplicacion

## Archivos a crear/modificar

- `src/application/graphs/nodes/extract_memories.py` (crear)
- `src/application/services/memory_service.py` (crear)
- `src/domain/models/episodic_memory.py` (crear)
- `alembic/versions/xxx_add_episodic_memories_table.py` (crear)
- `tests/unit/test_memory_extraction.py` (crear)

## Decisiones de diseno

- **Post-generation (no pre-generation)**: Extraer recuerdos del intercambio completo, no solo de la pregunta.
- **Gemini Flash para extraccion**: Rapido y barato, no necesita modelo grande para identificar hechos.
- **Embedding para deduplicacion**: Similarity search (> 0.9 cosine) evita duplicados semanticos.
- **Confidence threshold**: Evita almacenar recuerdos ambiguos o irrelevantes.

## Out of scope

- Retrieval de memorias en busqueda (spec T4-S5-02)
- Sanitizacion PII de memorias (spec T4-S6-02)
- UI para ver/editar memorias
