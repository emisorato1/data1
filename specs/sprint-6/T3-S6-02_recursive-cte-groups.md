# T3-S6-02: Recursive CTE membersia de grupos

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T4-S6-01 |
| Depende de | T3-S6-01 |
| Skill | `security-mirror/SKILL.md` + `database-setup/SKILL.md` |
| Estimacion | M (2-4h) |

## Contexto

OpenText has nested groups (groups within groups). A user in Group A, which is member of Group B, inherits Group B's permissions. A recursive CTE efficiently resolves all transitive group memberships.

## Spec

Implement a recursive Common Table Expression (CTE) query to resolve all group memberships transitively, and integrate it into PermissionResolver.

## Acceptance Criteria

- [x] Recursive CTE SQL que resuelve membresia transitiva de grupos
- [x] Funcion `resolve_all_groups(user_id) -> set[str]` que retorna todos los grupos (directos + transitivos)
- [x] Proteccion contra ciclos en la jerarquia de grupos (max depth configurable, default: 10)
- [x] Integracion con PermissionResolver.get_accessible_document_ids()
- [x] Datos sinteticos con jerarquia de 3+ niveles de anidamiento
- [x] Performance: < 50ms para resolver grupos de un usuario con 100+ grupos
- [x] Tests: grupos anidados 3 niveles, ciclos detectados, usuario sin grupos

## Archivos a crear/modificar

- `src/infrastructure/security/group_resolver.py` (crear)
- `tests/unit/test_group_resolver.py` (crear)

## Decisiones de diseno

- **Recursive CTE sobre iteracion en Python**: DB-native, mas eficiente para grafos de grupos.
- **Max depth**: Previene loops infinitos en datos corruptos.

## Out of scope

- Group management UI
- Sync de grupos desde OpenText (CDC)
