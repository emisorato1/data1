# Backlog Post-MVP: Sistema RAG Enterprise Bancario

> Estas tareas se priorizan y planifican al finalizar Sprint 4, basandose en feedback de la demo MVP.
> Cada bloque es independiente y puede planificarse como un sprint dedicado.

---

## Bloque A: Document Management (Upload via API)
**Prioridad estimada:** Alta (primer bloque post-MVP)

- **POST-01:** API de upload de documentos (`POST /documents`) con multipart/form-data
- **POST-02:** Validacion de archivo (tipo, tamano) en endpoint
- **POST-03:** Guardar archivo en storage (GCS o filesystem) y registrar en tabla `documents` con status `pending`
- **POST-04:** Trigger de Airflow DAG `rag_indexing` via REST API desde el endpoint de upload
- **POST-05:** Endpoints `GET /documents` (lista con paginacion), `GET /documents/{id}` (metadata + status pipeline), `DELETE /documents/{id}`
- **POST-06:** Frontend: pantalla de gestion de documentos (upload, lista, estado de indexacion, eliminar)
- **Skill:** `document-management/SKILL.md` + `api-design/SKILL.md`

---

## Bloque B: Security Mirror + Permisos Granulares

- **POST-07:** Implementar `PermissionResolver` con datos sinteticos de OpenText
- **POST-08:** Inyectar filtros de permisos en hybrid search (late binding)
- **POST-09:** Airflow DAG de CDC para sincronizar con OpenText real (event-driven o programado)
- **POST-10:** Recursive CTE para membersia de grupos
- **Skill:** `security-mirror/SKILL.md`

---

## Bloque C: Memoria Avanzada

- **POST-11:** Extraccion automatica de recuerdos episodicos post-generacion
- **POST-12:** Long-term memory retrieval integrado en busqueda
- **POST-13:** Sanitizacion de PII en recuerdos almacenados
- **Skill:** `chat-memory/SKILL.md`

---

## Bloque D: Guardrails Avanzados

- **POST-14:** PII detection en respuestas (output) con regex + NER
- **POST-15:** Faithfulness scoring con LLM-as-judge
- **POST-16:** Topic control (solo dominio bancario)
- **Skill:** `guardrails/SKILL.md`

---

## Bloque E: Observabilidad + Evaluacion

- **POST-17:** Airflow DAG programado para evaluacion RAGAS (faithfulness, answer_relevancy, context_precision)
- **POST-18:** Audit logging forense con SHA-256 hashing
- **POST-19:** Dashboard de costos de API (Vertex AI) en Google Cloud Monitoring
- **Skill:** `observability/SKILL.md` + `observability/references/ragas-evaluator.md`

---

## Bloque F: Frontend Avanzado

- **POST-20:** Admin dashboard (metricas RAG, gestion documentos, logs)
- **POST-21:** Widget de feedback (thumbs up/down por respuesta)
- **POST-22:** Dark mode
- **POST-23:** Vista de estado de pipelines Airflow (documentos en proceso de indexacion)
- **Skill:** `frontend/SKILL.md` + `frontend/references/admin-dashboard.md`

---

## Bloque G: Pipelines Airflow Avanzados

- **POST-24:** DAG de re-indexacion batch programada (cron semanal/diario)
- **POST-25:** DAG de CDC OpenText (event-driven via Kafka/PubSub o polling)
- **POST-26:** DAG de limpieza de datos (GDPR forget-user, retencion)
- **Skill:** `database-setup/references/gdpr-forget-user.md`

---

## Bloque H: Hardening + Production

- **POST-27:** Pentesting OWASP Top 10 + LLM Top 10
- **POST-28:** Rate limiting avanzado por usuario + token bucket
- **POST-29:** CD automatico (push to main -> Helm upgrade en K8s)
- **POST-30:** Load testing con K6/Locust
- **POST-31:** Document versioning y re-indexacion
- **POST-32:** Helm chart: valores para multi-entorno (dev, staging, prod) con sealed-secrets
- **Skill:** `security-pentesting/SKILL.md`
