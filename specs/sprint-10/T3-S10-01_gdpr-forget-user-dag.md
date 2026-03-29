# POST-26: DAG limpieza datos GDPR forget-user retencion

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Alta |
| Estado | pending |
| Bloqueante para | - |
| Depende de | - |
| Skill | `database-setup/references/gdpr-forget-user.md` |
| Estimacion | M (2-4h) |

## Contexto

GDPR and Argentine data protection law (Ley 25.326) require the ability to delete all user data on request. A dedicated Airflow DAG handles data cleanup: conversations, memories, feedback, audit anonymization.

## Spec

Create Airflow DAG `gdpr_forget_user` that deletes all personal data for a given user across all tables, with audit trail.

## Acceptance Criteria

- [ ] DAG `gdpr_forget_user` en `dags/maintenance/gdpr_forget_user.py`
- [ ] Trigger manual con `user_id` como parameter
- [ ] Tasks: `delete_conversations` -> `delete_memories` -> `delete_feedback` -> `anonymize_audit_logs` -> `confirm_deletion`
- [ ] Conversaciones y mensajes del usuario eliminados
- [ ] Episodic memories del usuario eliminadas
- [ ] Feedback del usuario eliminado
- [ ] Audit logs anonimizados (actor_id reemplazado con hash, no eliminados)
- [ ] Confirmacion: query de verificacion que no quedan datos personales
- [ ] Log de ejecucion para compliance (quien solicito, cuando se ejecuto)
- [ ] Tests de estructura del DAG

## Archivos a crear/modificar

- `dags/maintenance/gdpr_forget_user.py` (crear)
- `dags/maintenance/__init__.py` (crear)
- `tests/unit/test_dag_gdpr.py` (crear)

## Decisiones de diseno

- **Anonimizar audit logs (no eliminar)**: Los logs de auditoria deben mantenerse para compliance, pero sin PII.
- **Trigger manual**: Solo se ejecuta bajo solicitud formal, no automatico.
- **Verificacion post-delete**: Confirma que no quedan datos.

## Out of scope

- Data retention policies automaticas, right-to-portability (export datos), GDPR consent management
