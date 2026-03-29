# Escenarios de Demo - Enterprise AI Platform

> **Spec:** T4-S4-02 | **Fecha:** Sprint 4 | **Estado:** Validado

## Requisitos previos

1. Dataset de demo indexado (18 documentos via Airflow DAG `load_demo_data`).
2. Stack corriendo: FastAPI + PostgreSQL/pgvector + Redis.
3. Usuario autenticado con sesion activa.

## Target de rendimiento

| Metrica | Target | Notas |
|---------|--------|-------|
| Latencia E2E (p95) | < 3 segundos | Desde envio de query hasta primer token SSE |
| Streaming | Tokens incrementales | El usuario ve la respuesta construyendose |

---

## Escenario 1: Consulta con documentos relevantes (happy path)

**Objetivo:** Demostrar el flujo RAG completo con retrieval, reranking, generacion y citaciones.

**Query:**
```
Cuales son las medidas disponibles de cajas de seguridad?
```

**Documento target:** CS001 - Manual del producto.docx

**Respuesta esperada:**
- Informacion sobre las medidas/tamanios de cajas de seguridad extraida del manual.
- Citaciones con formato `[N]` referenciando la fuente.
- Sources en el evento `done` incluyendo `CS001 - Manual del producto.docx`.

**Que verificar:**
- [ ] La respuesta contiene informacion factual del documento (no inventada).
- [ ] Aparecen citaciones `[1]`, `[2]`, etc. en el texto.
- [ ] El evento `done` incluye `sources` con `document_name` y `page`.
- [ ] Latencia < 3 segundos hasta primer token.
- [ ] Streaming funcional (tokens aparecen incrementalmente).

---

## Escenario 2: Consulta sin documentos relevantes (edge case)

**Objetivo:** Demostrar manejo graceful cuando no hay informacion disponible.

**Query:**
```
Cual es el procedimiento para abrir una cuenta en dolares en Suiza?
```

**Documento target:** Ninguno (no existe en el dataset de demo).

**Respuesta esperada:**
```
No tengo informacion suficiente en la documentacion disponible para responder esta consulta. Te sugiero contactar al area correspondiente.
```

**Que verificar:**
- [ ] Respuesta de fallback exacta (no intenta adivinar).
- [ ] No hay `sources` en el evento `done` (lista vacia).
- [ ] No se invoca al LLM (respuesta directa, baja latencia).
- [ ] Tono profesional y no apologetico en exceso.

---

## Escenario 3: Query fuera de dominio bancario (edge case)

**Objetivo:** Demostrar que el sistema identifica y rechaza consultas no relacionadas con el dominio bancario.

**Query:**
```
Dame la receta para hacer empanadas tucumanas
```

**Documento target:** Ninguno (fuera de dominio).

**Respuesta esperada:**
```
Esa consulta esta fuera de mi area de conocimiento. Estoy preparado para responder preguntas sobre documentacion bancaria interna, politicas, procedimientos y temas de RRHH. En que puedo ayudarte?
```

**Que verificar:**
- [ ] Clasificacion como `fuera_dominio` (no llega al retrieval).
- [ ] Respuesta especifica de fuera de dominio (no el fallback generico).
- [ ] Respuesta rapida (< 1 segundo, sin retrieval ni LLM).
- [ ] El sistema invita al usuario a reformular dentro del dominio.

---

## Escenario 4: Conversacion multi-turno (continuidad de contexto)

**Objetivo:** Demostrar que el sistema mantiene contexto entre mensajes.

**Turno 1 - Query:**
```
Que requisitos tiene un prestamo personal?
```

**Documento target turno 1:** PP001 - Manual del producto.docx

**Turno 2 - Query (follow-up):**
```
Y como se realiza el otorgamiento?
```

**Documento target turno 2:** PP002 - Otorgamiento de prestamo personal.docx

**Que verificar:**
- [ ] Turno 1: respuesta con requisitos del prestamo personal y citaciones.
- [ ] Turno 2: el sistema entiende que "el otorgamiento" se refiere a prestamos personales (por el historial).
- [ ] Turno 2: respuesta con procedimiento de otorgamiento y citaciones del documento PP002.
- [ ] Ambas respuestas dentro de la misma conversacion (mismo `conversation_id`).
- [ ] Cada turno con latencia < 3 segundos.

---

## Escenario 5: Consulta RRHH + citaciones verificables

**Objetivo:** Demostrar que el sistema cubre documentacion RRHH y que las citaciones son verificables.

**Query:**
```
Que debo hacer si sufro un accidente de trabajo?
```

**Documento target:** 008 RRHH - Salud, Prevencion y Medio Ambiente.pdf

**Respuesta esperada:**
- Procedimiento de denuncia/reporte de accidentes laborales.
- Citaciones `[N]` referenciando el documento de RRHH.
- Sources con `008 RRHH - Salud, Prevencion y Medio Ambiente.pdf`.

**Que verificar:**
- [ ] Informacion factual del documento de RRHH sobre accidentes.
- [ ] Citacion `[N]` verificable contra el contenido del chunk.
- [ ] Source metadata incluye nombre del PDF y pagina.
- [ ] Respuesta con tono profesional y corporativo.
- [ ] Latencia < 3 segundos hasta primer token.

---

## Resumen de cobertura

| # | Tipo de escenario | Capacidad demostrada |
|---|-------------------|---------------------|
| 1 | Happy path con documentos | Retrieval + reranking + generacion + citaciones |
| 2 | Sin documentos relevantes | Fallback graceful sin alucinaciones |
| 3 | Fuera de dominio | Clasificacion de intent + rechazo educado |
| 4 | Multi-turno | Persistencia de contexto conversacional |
| 5 | RRHH + citaciones | Cobertura multi-area + verificabilidad |

## Notas para el presentador

- **Orden sugerido:** Escenario 1 -> 5 -> 4 -> 2 -> 3 (de happy path a edge cases).
- **Si la latencia excede 3s:** Verificar que el reranker Vertex AI no este en cold start. La segunda query suele ser mas rapida.
- **Si las citaciones no aparecen:** Es comportamiento del LLM, no un bug. Las instrucciones estan en el system prompt pero Gemini puede omitirlas ocasionalmente. Repetir la query suele resolverlo.
- **Multi-turno:** Asegurarse de usar la misma conversacion (no crear una nueva entre turno 1 y turno 2).
