# T3-S7-03: Modo carpeta local para DAG load_demo_data

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Media |
| Estado | done |
| Bloqueante para | - |
| Depende de | T3-S4-01 (done) |
| Skill | `rag-indexing/SKILL.md` |
| Estimacion | S (1-2h) |

## Contexto

El DAG `load_demo_data` solo soporta indexación desde GCS. Para desarrollo local,
los documentos demo están montados en `/opt/airflow/data/demo/` (bind mount de
`tests/data/demo/`) pero el DAG no puede leerlos directamente. El docker-compose
ya intenta pasar `folder_path` en el trigger pero el DAG lo ignoraba.

Este cambio agrega un modo carpeta local al DAG existente, permitiendo indexar
los documentos de demo sin necesitar acceso a GCS.

## Spec

Modificar `dags/indexing/load_demo_data.py` para soportar un modo local bifurcando
la lógica de descubrimiento e indexación según el parámetro `folder_path` del conf.

## Acceptance Criteria

- [x] DAG acepta parámetro `folder_path` en el conf (además del existente `gcs_bucket`)
- [x] Si se recibe `folder_path`, escanea el filesystem local en vez de GCS
- [x] Constante `FILENAME_AREA_MAPPING` mapea prefijos de nombres de archivo a áreas funcionales
- [x] Helper `_determine_area_from_filename(filename)` determina área para archivos planos
- [x] Helper `_register_or_update_document_local()` busca registro existente por `file_path`
  y lo actualiza con `file_hash` (preserva IDs y ACLs de seed_data), o crea uno nuevo
- [x] `discover_documents`: en modo local, itera `Path.iterdir()` y filtra por extensión
- [x] `index_documents`: en modo local, usa `local_path` directamente sin llamar a GCS
- [x] El modo GCS existente no se modifica (bifurcación limpia por presencia de `folder_path`)
- [x] Trigger del docker-compose funciona sin cambios: `{"folder_path": "data/demo/", "skip_existing": true}`
- [x] Los `document_chunks` indexados quedan vinculados a los `document_id` de seed_data (con ACLs)
- [x] Linting ruff pasa sin errores

## Archivos modificados

- `dags/indexing/load_demo_data.py` (modificado)

## Decisiones de diseño

- **Bifurcación por `folder_path`**: Prioridad al parámetro local; si está ausente, usa GCS.
  Retrocompatibilidad total: sin `folder_path`, el DAG se comporta exactamente igual.
- **Upsert por `file_path`**: `_register_or_update_document_local` busca por `file_path`
  primero para reutilizar IDs de seed_data con sus ACLs. Solo crea registro nuevo si no
  existe. Esto garantiza que los chunks sean consultables con el sistema de permisos.
- **Mapping por nombre de archivo**: Los archivos de demo son planos (sin subcarpetas),
  por lo que `FOLDER_AREA_MAPPING` (diseñado para rutas GCS) no aplica. Se agrega
  `FILENAME_AREA_MAPPING` independiente para no contaminar la lógica GCS.
- **Campo `source` unificado**: Los resultados de `index_documents` usan `source` en vez
  de `gcs_uri` para funcionar con ambos modos sin romper el report task.

## Out of scope

- Soporte de subdirectorios recursivos en modo local
- Paralelismo en modo local (procesamiento secuencial, igual que GCS)
- Tests unitarios del DAG (el DAG ya tiene cobertura de integración via Airflow)

## Registro de implementación

Implementado 2026-03-19. Cambios en `dags/indexing/load_demo_data.py`:

1. Docstring actualizado para documentar el nuevo parámetro `folder_path`
2. Constante `FILENAME_AREA_MAPPING` agregada después de `SKIP_PREFIXES`
3. Helper `_determine_area_from_filename()` agregado antes de `_register_document`
4. Helper `_register_or_update_document_local()` agregado antes de `_register_document`
5. Param `folder_path: None` agregado al bloque `params` del DAG
6. `discover_documents` bifurcado: modo local primero (si `folder_path`), GCS como fallback
7. `index_documents` bifurcado en el paso de adquisición de archivo local
8. Campo `gcs_uri` reemplazado por `source` en los resultados para compatibilidad con ambos modos
9. Limpieza de archivo local omitida en modo local (no descargar = no borrar)
