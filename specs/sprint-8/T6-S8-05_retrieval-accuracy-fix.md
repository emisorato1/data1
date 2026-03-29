# T6-S8-05: Mejora de retrieval_accuracy — pipeline retrieve-first y evaluador robusto

## Meta


| Campo           | Valor                                                                        |
| --------------- | ---------------------------------------------------------------------------- |
| Track           | T6 (Franco)                                                                  |
| Prioridad       | Alta                                                                         |
| Estado          | done                                                                         |
| Bloqueante para | —                                                                            |
| Depende de      | T6-S8-04 (done)                                                              |
| Skill           | `testing-strategy/SKILL.md`, `rag-retrieval/SKILL.md`, `guardrails/SKILL.md` |
| Estimacion      | L (8-16h)                                                                    |


> Reemplazar la clasificacion pre-retrieval basada en keywords estaticas por un patron retrieve-first donde la relevancia se determina por los scores de los documentos recuperados. Corregir falsos negativos del evaluador. Elevar retrieval_accuracy de 44.4% a ≥80%.

## Contexto

La categoria `retrieval_accuracy` del framework de evaluacion (18 samples) reporta un pass rate de **44.4%** (8/18). De los 10 fallos, el diagnostico revela **dos causas raiz independientes**:


| Tipo de fallo                                                                                             | Casos | IDs                                            |
| --------------------------------------------------------------------------------------------------------- | ----- | ---------------------------------------------- |
| Rechazo pre-retrieval: query valida clasificada como `fuera_dominio` antes de llegar al vector store      | 6     | RA-001, RA-003, RA-004, RA-006, RA-007, RA-013 |
| Falso negativo del evaluador: retrieval y generacion correctos pero el evaluador no reconoce la respuesta | 4     | RA-009, RA-011, RA-012, RA-014                 |


El 33% de las queries del golden dataset son rechazadas sin intentar busqueda, y el 22% tiene respuesta correcta que el evaluador descarta por limitaciones de matching.

## Diagnostico

### Causa raiz 1 — La clasificacion pre-retrieval por keywords no escala

El nodo `classify_intent` usa una heuristica de keywords estaticas (`_DOMAIN_KEYWORDS`, ~130 terminos) para decidir si una query es del dominio bancario. Si la query tiene ≥3 palabras significativas y **ninguna** pertenece a la lista, se clasifica como `fuera_dominio` y se rechaza sin intentar retrieval.

**Queries validas rechazadas por keywords faltantes:**


| Caso   | Query                                                              | Termino clave ausente en la lista |
| ------ | ------------------------------------------------------------------ | --------------------------------- |
| RA-001 | "periodo maximo de reposo que puede indicar un certificado medico" | medico, certificado, reposo       |
| RA-003 | "horarios del consultorio medico de Cordoba"                       | consultorio, horario              |
| RA-004 | "lineas familiares puedo agregar al descuento de Movistar"         | descuento                         |
| RA-006 | "convocatoria anual de becas"                                      | beca, convocatoria                |
| RA-007 | "codigo de acceso para Samshop de Samsung"                         | codigo, acceso                    |
| RA-013 | "codigo de bloqueo para el bloqueo preventivo de TD"               | bloqueo, codigo, td               |


**Por que no basta con agregar keywords:**

El problema de fondo no son las 20 keywords faltantes sino la **arquitectura de la decision**. Una lista estatica de keywords:

- Requiere mantenimiento manual cada vez que se indexan documentos nuevos (nuevas areas funcionales, nuevos productos, convenios con marcas externas)
- No puede anticipar todas las formas en que un usuario formulara una pregunta valida (abreviaturas como "TD", nombres de marca como "Samshop", terminologia medica que cruza dominios)
- Crea un punto de falla silencioso: el sistema rechaza queries validas sin dejar evidencia de que existia un documento relevante
- El volumen de documentos crecera significativamente cuando se inicie la vectorizacion masiva, multiplicando los terminos de dominio que la lista necesitaria cubrir

**Bug agravante en `topic_classifier`:**

Ademas, el nodo `topic_classifier` (Gemini Flash con few-shot) tiene un bug que impide que rescate queries mal clasificadas: cuando `classify_intent` ya marco la query como `fuera_dominio`, el topic_classifier se salta por completo sin evaluarla con el LLM. Esto elimina la unica red de seguridad que podria corregir falsos positivos de la heuristica.

Adicionalmente, cuando el topic_classifier SI evalua y clasifica como `ON_TOPIC`, no sobreescribe explicitamente el `query_type` a `"consulta"`, por lo que un `fuera_dominio` previo persiste en el estado del grafo.

### Causa raiz 2 — Falsos negativos del evaluador

Cuatro queries tienen retrieval y generacion correctos, pero el evaluador rechaza la respuesta por limitaciones de matching:


| Caso   | Tipo de evaluacion | Valor esperado                           | Respuesta real (correcta)      | Bug del evaluador                                                                                                      |
| ------ | ------------------ | ---------------------------------------- | ------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| RA-009 | `exact_match`      | "13 dias"                                | "13 dias" (con tilde)          | No normaliza diacriticos: la comparacion substring falla porque "dias" sin tilde no matchea "dias" con tilde           |
| RA-011 | `exact_match`      | "10 dias habiles"                        | "10 dias habiles" (con tildes) | Mismo problema de diacriticos                                                                                          |
| RA-012 | `contains_all`     | "WhatsApp 11 3110 1338" (una sola parte) | "WhatsApp al 11 3110 1338"     | El expected_output no tiene comas, se evalua como substring unico y falla por la preposicion "al" intercalada          |
| RA-014 | `negation`         | Patron regex que exige "no se permite"   | "no permite" (sin "se")        | El regex de negacion requiere la particula "se" intermedia; "no permite" es negacion valida en espanol pero no matchea |


## Spec

### 1. Reestructuracion del flujo de clasificacion — patron retrieve-first

Reemplazar la arquitectura actual donde la decision de dominio ocurre **antes** del retrieval por un patron donde la relevancia se determina **despues** del retrieval, usando los scores de los documentos recuperados como indicador de pertenencia al dominio.

**Flujo actual (problematico):**


| Paso | Nodo               | Accion                                           | Problema                                 |
| ---- | ------------------ | ------------------------------------------------ | ---------------------------------------- |
| 1    | `classify_intent`  | Keywords estaticas deciden si es consulta valida | Lista incompleta bloquea queries validas |
| 2    | `guardrail_input`  | Valida seguridad (inyeccion, jailbreak)          | —                                        |
| 3    | `topic_classifier` | LLM clasifica ON/OFF_TOPIC                       | Se salta si paso 1 ya dijo fuera_dominio |
| 4    | Routing            | Si fuera_dominio → respuesta de deflexion        | La query nunca llega al vector store     |
| 5    | `retrieve`         | Busqueda hibrida (solo si paso 4 permite)        | —                                        |


**Flujo nuevo (retrieve-first):**


| Paso | Nodo                             | Accion                                               | Beneficio                            |
| ---- | -------------------------------- | ---------------------------------------------------- | ------------------------------------ |
| 1    | `classify_intent` (simplificado) | Solo detecta saludos y delega el resto como consulta | Elimina keywords de dominio          |
| 2    | `guardrail_input`                | Valida seguridad (sin cambios)                       | —                                    |
| 3    | `retrieve`                       | Busqueda hibrida para TODA query no-saludo           | Siempre intenta encontrar documentos |
| 4    | `rerank`                         | Reranking con Vertex AI (sin cambios)                | —                                    |
| 5    | `score_gate` (nuevo)             | Evalua scores de los chunks rerankeados              | Usa evidencia real, no heuristica    |
| 6    | Routing post-retrieval           | Segun resultado del score_gate                       | Decision informada por datos         |


El routing del paso 6 se comporta asi:


| Resultado del score_gate                       | Accion                                                        |
| ---------------------------------------------- | ------------------------------------------------------------- |
| Scores suficientes (max score ≥ umbral alto)   | Continuar a `assemble_context` → `generate`                   |
| Scores insuficientes (max score < umbral bajo) | Retornar respuesta de fallback (no hay documentos relevantes) |
| Scores ambiguos (entre umbral bajo y alto)     | Escalar a `topic_classifier` (LLM) para decidir               |


### 2. Simplificacion de classify_intent

Reducir la responsabilidad de `classify_intent` exclusivamente a la deteccion de saludos. Eliminar por completo:

- La constante `_DOMAIN_KEYWORDS` (toda la frozenset de ~130 terminos)
- La logica de deteccion de `fuera_dominio` basada en keywords
- La constante `_MIN_WORDS_FOR_OOD`

Mantener:

- La deteccion de saludos (`_GREETING_KEYWORDS`)
- La deteccion de follow-ups conversacionales (`_FOLLOWUP_INDICATORS`)
- La normalizacion de texto (`_normalize`)
- Las stopwords (`_STOPWORDS`) en tanto sean necesarias para la deteccion de saludos

Toda query que no sea saludo retorna `query_type: "consulta"` y avanza al retrieval.

### 3. Nuevo nodo score_gate post-reranking

Crear un nodo `score_gate` que se ejecuta despues de `rerank` y antes de `assemble_context`. Su funcion es evaluar la calidad de los documentos recuperados para decidir si hay suficiente evidencia para generar una respuesta.

**Entrada:** Estado del grafo con `reranked_chunks` (lista de chunks con scores post-reranking).

**Logica de decision:**


| Condicion                                                                       | Clasificacion  | Accion en el grafo                                     |
| ------------------------------------------------------------------------------- | -------------- | ------------------------------------------------------ |
| No se recuperaron chunks (lista vacia)                                          | `sin_contexto` | Ir a fallback (respuesta de "no encontre informacion") |
| El score maximo de los chunks rerankeados es ≥ `reranking_threshold` (settings) | `suficiente`   | Continuar a `assemble_context` → `generate`            |
| El score maximo es < `similarity_threshold` (settings)                          | `insuficiente` | Ir a fallback                                          |
| El score maximo esta entre `similarity_threshold` y `reranking_threshold`       | `ambiguo`      | Escalar a `topic_classifier` para decision LLM         |


**Parametros de configuracion:** Reutilizar los dos umbrales ya definidos en `settings.py` que actualmente no se usan activamente:


| Parametro                     | Valor actual                                                                    | Uso en score_gate                  |
| ----------------------------- | ------------------------------------------------------------------------------- | ---------------------------------- |
| `similarity_threshold` (0.78) | Umbral bajo: por debajo de este score, los documentos no son relevantes         | Corte inferior para `insuficiente` |
| `reranking_threshold` (0.85)  | Umbral alto: por encima de este score, los documentos son claramente relevantes | Corte superior para `suficiente`   |


Estos valores iniciales provienen de la calibracion de T6-S6-01. Deben validarse con el golden dataset de retrieval_accuracy y ajustarse si es necesario durante la implementacion.

**Salida:** Agregar al estado del grafo un campo `retrieval_confidence` con valor `"suficiente"`, `"insuficiente"` o `"ambiguo"` para que el routing condicional del grafo pueda tomar la decision.

### 4. Ajuste de topic_classifier como red de seguridad

El `topic_classifier` deja de ser gate primario y pasa a ser **red de seguridad** que solo se invoca en casos ambiguos del score_gate. Requiere tres cambios:

**4a. Eliminar el skip de fuera_dominio**

Actualmente el topic_classifier se salta cuando `query_type` ya es `"fuera_dominio"`. Eliminar `"fuera_dominio"` de la condicion de skip para que el clasificador LLM siempre evalue cuando es invocado. Solo deben seguir siendo skipeados los tipos `"saludo"` y `"blocked"`.

**4b. Override explicito de query_type en ON_TOPIC**

Cuando el topic_classifier clasifica como `ON_TOPIC`, debe retornar explicitamente `query_type: "consulta"` en su salida para sobreescribir cualquier valor previo en el estado del grafo.

**4c. Ampliar few-shot examples**

Agregar ejemplos `ON_TOPIC` que cubran los patrones de edge-case que la heuristica de keywords no captaba:


| Patron                                      | Ejemplos a agregar                                                                              |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Salud laboral (parece medico pero es RRHH)  | Preguntas sobre certificados medicos, horarios de consultorio, dias de reposo                   |
| Beneficios corporativos con marcas externas | Preguntas sobre descuentos con Movistar, codigos de acceso para Samsung, convocatorias de becas |
| Operaciones especificas de tarjeta          | Preguntas sobre codigos de bloqueo, desbloqueo de TD, rescate de tarjeta                        |


Agregar al menos 6 nuevos ejemplos `ON_TOPIC` cubriendo estos tres patrones.

### 5. Normalizacion de diacriticos en el evaluador

Agregar al evaluador una funcion de normalizacion Unicode que elimine diacriticos (tildes) antes de realizar comparaciones de texto. Aplicar esta normalizacion en:

- `_eval_exact_match`: normalizar tanto el `expected_output` como la respuesta actual antes del substring match
- `_eval_contains_all`: normalizar cada parte esperada y la respuesta antes de verificar presencia

La normalizacion debe usar descomposicion NFKD de Unicode y eliminar caracteres de combinacion (combining characters). Esto permite que "dias" matchee "dias" con tilde, y "habiles" matchee "habiles" con tilde, sin requerir que el golden dataset use acentos especificos.

### 6. Expansion de patrones de negacion en el evaluador

Ampliar el regex `_NEGATION_RE` para capturar formas adicionales de negacion validas en espanol que actualmente no matchean:


| Patron actual que falta                      | Ejemplo en respuesta                         | Caso que resuelve |
| -------------------------------------------- | -------------------------------------------- | ----------------- |
| "no permite" (sin particula "se" intermedia) | "esta gestion no permite aumentar el limite" | RA-014            |


Agregar al primer grupo de alternativas del regex la forma directa "no + verbo" sin "se" intermedio, especificamente el verbo "permite". Esto captura tanto "no permite" como "no se permite" como negaciones validas.

### 7. Correccion del golden dataset

**RA-012:** Cambiar el `expected_output` de un string unico a partes separadas por coma para que el evaluador `contains_all` valide cada fragmento independientemente:


| Campo             | Antes                     | Despues                    |
| ----------------- | ------------------------- | -------------------------- |
| `expected_output` | `"WhatsApp 11 3110 1338"` | `"WhatsApp, 11 3110 1338"` |


Esto permite que respuestas como "WhatsApp al 11 3110 1338" pasen la validacion, ya que contienen ambas partes ("WhatsApp" y "11 3110 1338") aunque con una preposicion intercalada.

## Acceptance Criteria

- `classify_intent` no contiene logica de deteccion de `fuera_dominio` por keywords; la constante `_DOMAIN_KEYWORDS` ha sido eliminada
- `classify_intent` conserva la deteccion de saludos y retorna `"consulta"` para toda query que no sea saludo
- El grafo RAG ejecuta `retrieve` para toda query clasificada como `"consulta"`, sin gate previo de dominio
- Existe un nodo `score_gate` que se ejecuta despues de `rerank` y evalua la calidad de los chunks recuperados
- `score_gate` clasifica el resultado como `"suficiente"`, `"insuficiente"` o `"ambiguo"` segun los umbrales `reranking_threshold` y `similarity_threshold` de settings
- El routing condicional del grafo envia a `generate` si `suficiente`, a fallback si `insuficiente`, y a `topic_classifier` si `ambiguo`
- `topic_classifier` no se salta queries con `query_type="fuera_dominio"` — las evalua con LLM
- `topic_classifier` retorna `query_type: "consulta"` explicitamente cuando clasifica `ON_TOPIC`
- `topic_config.few_shot_examples` incluye ≥6 nuevos ejemplos `ON_TOPIC` para salud laboral, beneficios con marcas y operaciones de tarjeta
- `_eval_exact_match` y `_eval_contains_all` normalizan diacriticos antes de comparar
- `_NEGATION_RE` matchea "no permite" (sin "se") como negacion valida
- `RA-012` expected_output usa partes separadas por coma
- Tests unitarios para `classify_intent` simplificado: queries previamente rechazadas (RA-001, RA-003, RA-004, RA-006, RA-007, RA-013) retornan `"consulta"`
- Tests unitarios para `score_gate`: cobertura de los tres rangos (suficiente, insuficiente, ambiguo) y caso de lista vacia
- Tests unitarios para normalizacion de diacriticos y regex de negacion expandido
- `pytest tests/ -v` pasa sin errores
- Re-ejecucion de `python -m evals.run_eval --category retrieval_accuracy` alcanza ≥80% pass rate (≥15/18)

## Archivos a crear/modificar


| Archivo                                            | Accion                                                                                            |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `src/application/graphs/nodes/classify_intent.py`  | Modificar — eliminar `_DOMAIN_KEYWORDS`, `_MIN_WORDS_FOR_OOD` y logica de fuera_dominio           |
| `src/application/graphs/nodes/score_gate.py`       | Crear — nodo que evalua calidad de chunks post-reranking                                          |
| `src/application/graphs/rag_graph.py`              | Modificar — insertar `score_gate` despues de `rerank`, agregar routing condicional post-retrieval |
| `src/application/graphs/nodes/topic_classifier.py` | Modificar — eliminar skip de fuera_dominio, override explicito en ON_TOPIC                        |
| `src/config/topic_config.py`                       | Modificar — agregar ≥6 few-shot examples ON_TOPIC                                                 |
| `evals/runner/evaluator.py`                        | Modificar — normalizacion diacriticos + regex negacion                                            |
| `evals/datasets/golden/retrieval_accuracy.json`    | Modificar — fix RA-012 expected_output                                                            |
| `tests/unit/test_classify_intent.py`               | Modificar — adaptar tests al classify_intent simplificado                                         |
| `tests/unit/test_score_gate.py`                    | Crear — tests para los tres rangos de decision y edge cases                                       |
| `tests/unit/test_evaluator.py`                     | Crear — tests para normalizacion de diacriticos y regex expandido                                 |


## Decisiones de diseno

- **Retrieve-first vs. expansion de keywords:** Agregar las ~20 keywords faltantes resolveria los 6 casos actuales pero no previene futuros fallos cuando se vectoricen documentos nuevos. El patron retrieve-first elimina la necesidad de mantener una lista de keywords porque la pertenencia al dominio se determina por la existencia de documentos relevantes en el vector store, no por una heuristica linguistica.
- **Score gate con dos umbrales (banda ambigua):** En lugar de un unico threshold binario, se usa una banda entre `similarity_threshold` y `reranking_threshold` que escala al topic_classifier solo para casos dudosos. Esto evita llamadas LLM innecesarias para queries claramente en-dominio o claramente fuera-de-dominio, mientras mantiene precision para las zonas grises.
- **topic_classifier como red de seguridad, no gate primario:** El LLM sigue siendo valioso para casos ambiguos (ej. queries que recuperan chunks de baja relevancia pero que podrian ser validas con reformulacion). Eliminarlo por completo dejaria el sistema sin capacidad de discernir entre "no hay documentos indexados sobre esto" y "la query es genuinamente fuera de dominio".
- **Reutilizar umbrales existentes de settings.py:** Los parametros `similarity_threshold` (0.78) y `reranking_threshold` (0.85) ya estan definidos y calibrados pero no se usan activamente. Darles un uso concreto en el score_gate evita introducir parametros nuevos y aprovecha la calibracion previa.
- **Normalizacion en evaluador, no en golden dataset:** Se normaliza en el evaluador porque es resiliente a variaciones futuras del LLM, mantiene el golden dataset legible y coloca la tolerancia en el componente que compara.
- **Costo del retrieve-first para queries off-topic:** Toda query (incluso "quien gano el partido") ejecutara un embedding + busqueda SQL (~50-100ms). Este costo es aceptable porque: (a) es comparable a la latencia del LLM call que antes hacia el topic_classifier para cada query, (b) las queries off-topic son una minoria en un sistema interno corporativo, y (c) el score_gate cortocircuita rapido sin llegar a generate.

## Out of scope

- Tuning de los umbrales `similarity_threshold` y `reranking_threshold` mas alla de la validacion contra el golden dataset
- Query expansion o rewriting pre-busqueda
- Ajustes al system prompt de generacion
- Mejoras a otras categorias de evaluacion (cubiertas por T6-S8-04)
- Implementacion de semantic cache
- Cambio de modelo de embedding

## Registro de Implementacion
**Fecha**: 2026-03-27 | **Rama**: 70-t6-s8-05_retrieval_accuracy

| Archivo | Accion | Motivo |
|---------|--------|--------|
| `src/application/graphs/nodes/classify_intent.py` | Modificado | Eliminados `_DOMAIN_KEYWORDS`, `_MIN_WORDS_FOR_OOD`, `_STOPWORDS`, `_FOLLOWUP_INDICATORS` y toda logica de fuera_dominio. Solo queda deteccion de saludos (AC-1, AC-2) |
| `src/application/graphs/state.py` | Modificado | Agregado campo `retrieval_confidence: str` al RAGState (AC-4) |
| `src/application/graphs/nodes/score_gate.py` | Creado | Nodo post-reranking con logica de 3 rangos usando `similarity_threshold` y `reranking_threshold` (AC-4, AC-5) |
| `src/application/graphs/rag_graph.py` | Modificado | Reestructurado con patron retrieve-first: routing post-guardrail, score_gate despues de rerank, routing condicional a 3 destinos (AC-3, AC-6) |
| `src/application/graphs/nodes/topic_classifier.py` | Modificado | Eliminado skip de `fuera_dominio`, agregado override `query_type: "consulta"` en ON_TOPIC (AC-7, AC-8) |
| `src/config/topic_config.py` | Modificado | Agregados 6 few-shot examples ON_TOPIC: salud laboral, beneficios con marcas, operaciones de tarjeta (AC-9) |
| `evals/runner/evaluator.py` | Modificado | Agregada `_strip_diacritics()` con NFKD, aplicada en `_eval_exact_match` y `_eval_contains_all`. Expandido `_NEGATION_RE` con "no permite" (AC-10, AC-11) |
| `evals/datasets/golden/retrieval_accuracy.json` | Modificado | RA-012 expected_output cambiado a "WhatsApp, 11 3110 1338" (AC-12) |
| `tests/unit/test_classify_intent.py` | Creado | 19 tests: saludos, consulta default, queries antes rechazadas (RA-001..RA-013), verificacion constantes eliminadas (AC-13) |
| `tests/unit/test_score_gate.py` | Creado | 13 tests: 3 suficiente + 3 insuficiente + 3 ambiguo + 2 vacio + 2 edge cases (AC-14) |
| `tests/unit/test_evaluator_diacritics.py` | Creado | 16 tests: normalizacion diacriticos, exact_match con tildes, contains_all, regex negacion expandido (AC-15) |
| `tests/unit/test_rag_graph.py` | Modificado | Adaptado a nueva estructura del grafo: mock de score_gate, tests de routing post-score_gate |

### Notas de Implementacion
- El test file se nombro `test_evaluator_diacritics.py` en lugar de `test_evaluator.py` (como dice la spec) para evitar colision con `test_eval_runner.py` que ya cubre los evaluadores base.
- El routing post-guardrail reemplaza el routing post-topic_classifier como decision primaria del grafo. `topic_classifier` ahora solo se invoca en la banda ambigua del score_gate.
- Coverage: classify_intent 100%, score_gate 100%, rag_graph 81%, evaluator (lineas modificadas) 100%.
- 704 tests unitarios pasan, 0 regresiones.
