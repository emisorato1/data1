# T3-S3-01: Seed data sintético para OpenText Mirror

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Media |
| Estado | done |
| Bloqueante para | - (prepara terreno para Security Mirror post-MVP) |
| Depende de | T1-S2-01 |
| Skill | `security-mirror/SKILL.md` > Sección "Modelo de Datos OpenText" |
| Estimación | S (1-2h) |

## Contexto

Las tablas del Espejo de Seguridad (`dtree`, `kuaf`, `dtreeacl`, `kuafchildren`, `dtreeancestors`) y la vista materializada `kuaf_membership_flat` ya existen en el esquema (migración `002`). Esta tarea consiste en poblar dichas tablas con datos sintéticos coherentes que representen una estructura bancaria (Roles de Riesgos, Compliance, Usuarios, Jerarquía de carpetas y permisos).

## Spec

Crear un script de seed robusto que inserte una estructura jerárquica de permisos y refresque la vista materializada para permitir testeos de "Late Binding" post-MVP.

## Acceptance Criteria

- [ ] Script de seed `scripts/seed_data.py` funcional y reproducible.
- [ ] Datos sintéticos generados:
    - 5 Usuarios (Analistas de Riesgos, Auditores, Gerentes).
    - 3 Grupos (Riesgos_Corp, Compliance_Team, Audit_Internal) con membresía cruzada.
    - 20 Documentos distribuidos en una jerarquía de carpetas (Ej: `/Procesos/Riesgos/2024/`).
    - ACLs variadas para validar que usuarios en grupos vean solo lo que les corresponde (específicamente bit `2` - SeeContents).
- [ ] El script debe ejecutar `REFRESH MATERIALIZED VIEW kuaf_membership_flat` al finalizar la carga.
- [ ] Validación: Una query de prueba contra `kuaf_membership_flat` debe devolver la expansión correcta de grupos para un analista de riesgos.
- [ ] Documentado: Un pequeño README/comentario en el script explicando la estructura "lógica" inyectada.

## Archivos a crear/modificar

- `scripts/seed_data.py` (modificar/verificar)
- `src/infrastructure/database/models/permission.py` (referencia — ya existe)

## Decisiones de diseño

- **Nombres Reales**: Usar las tablas existentes `kuaf`, `dtree`, etc. sin prefijos adicionales para mantener consistencia con los modelos de SQLAlchemy.
- **Jerarquía Realista**: Simular carpetas reales (SubType=0) que contienen documentos (SubType=144) para validar herencia de permisos en el futuro.
- **Seguridad por Bitmask**: Asegurar que los permisos insertados en `dtreeacl.permissions` respeten el bitmask de OpenText (See=1, SeeContents=2).

## Out of scope

- PermissionResolver service (post-MVP, spec POST-07)
- Integración con hybrid search (post-MVP, spec POST-08)
- Automatización del refresco de la vista (se hace manual en el seed por ahora)
