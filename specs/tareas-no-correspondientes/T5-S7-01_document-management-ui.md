# T5-S7-01: Frontend gestion documentos (upload, lista, estado, eliminar)

## Meta

| Campo | Valor |
|-------|-------|
| Track | T5 (Ema) |
| Prioridad | Alta |
| Estado | pending |
| Bloqueante para | - |
| Depende de | T2-S7-01, T1-S5-01 |
| Skill | `frontend/SKILL.md` + `document-management/SKILL.md` |
| Estimacion | XL (8+h) |

> POST-06

## Contexto

The backend APIs for document management need a user-facing interface. Users need to upload documents, see their list with indexing status, and manage (delete) existing documents.

## Spec

Build a full document management page in the Next.js frontend with upload dropzone, document list with status indicators, and delete functionality.

## Acceptance Criteria

- [ ] Nueva pagina `/documents` accesible desde sidebar
- [ ] Drag-and-drop upload zone con progress bar
- [ ] Validacion client-side de tipo y tamano de archivo (mismos limites que backend)
- [ ] Lista de documentos con columnas: nombre, tipo, tamano, status, fecha upload
- [ ] Status indicators visuales: pending (amarillo), indexing (azul/spinner), indexed (verde), failed (rojo)
- [ ] Polling automatico de status mientras hay documentos en `pending` o `indexing`
- [ ] Boton eliminar con confirmacion modal
- [ ] Paginacion en la lista de documentos
- [ ] Responsive design (funcional en tablet)
- [ ] Empty state amigable cuando no hay documentos
- [ ] Tests de componentes principales

## Archivos a crear/modificar

- `frontend/src/app/documents/page.tsx` (crear)
- `frontend/src/components/documents/UploadDropzone.tsx` (crear)
- `frontend/src/components/documents/DocumentList.tsx` (crear)
- `frontend/src/components/documents/DocumentStatusBadge.tsx` (crear)
- `frontend/src/components/documents/DeleteConfirmModal.tsx` (crear)
- `frontend/src/hooks/useDocuments.ts` (crear)
- `frontend/src/services/documentApi.ts` (crear)

## Decisiones de diseno

- **Polling sobre WebSocket para status**: Mas simple, status cambia en minutos no segundos
- **Drag-and-drop**: UX estandar para upload, mas intuitivo que solo boton
- **Client-side validation**: Feedback inmediato sin round-trip al server

## Out of scope

- Bulk upload (upload uno a uno)
- Document preview/viewer
- Document editing/annotation
- Admin view de documentos de todos los usuarios (spec T5-S8-01)
