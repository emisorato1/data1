# T3-S1-01: FileValidator y document loaders

## Meta

| Campo | Valor |
|-------|-------|
| Track | T3 (Gaston) |
| Prioridad | Alta |
| Estado | done |
| Bloqueante para | T3-S1-02 |
| Depende de | T1-S1-02 |
| Skill | `rag-indexing/SKILL.md` + `api-design/references/magic-bytes-validation.md` |
| Estimacion | L (4-8h) |

## Contexto

Primera pieza del pipeline de ingesta: validar y cargar documentos. Este codigo debe ser reutilizable tanto desde la API (upload futuro) como desde Airflow DAGs (indexacion batch). Los documentos bancarios pueden ser PDF o DOCX con tablas, texto denso y metadata.

## Spec

Implementar `FileValidator` para validacion de archivos por magic bytes y loaders especializados para PDF y DOCX que extraigan texto + metadata preservando estructura de tablas.

## Acceptance Criteria

- [x] `FileValidator` en `src/infrastructure/rag/loaders/` con:
  - Validacion de magic bytes para PDF (`%PDF`) y DOCX (PK zip signature)
  - Rechazo de archivos que no coincidan mime type con extension
  - Limite de tamano configurable (default 50MB)
- [x] Loader PDF con PyMuPDF:
  - Extrae texto completo
  - Extrae metadata: titulo, paginas, autor
  - Preserva estructura de tablas (como texto formateado)
- [x] Loader DOCX con python-docx:
  - Extrae texto completo
  - Extrae metadata: titulo, paginas (estimadas), autor
  - Preserva estructura de tablas (como texto formateado)
- [x] Interface comun `DocumentLoader` con metodo `load(file_path: Path) -> LoadedDocument`
- [x] `LoadedDocument` dataclass con: `text`, `metadata`, `pages`, `tables_count`
- [x] Codigo en `src/infrastructure/rag/loaders/` (importable desde API y DAGs)
- [x] Tests unitarios con archivos de ejemplo (PDF y DOCX validos e invalidos)

## Archivos a crear/modificar

- `src/infrastructure/rag/loaders/validator.py` (crear)
- `src/infrastructure/rag/loaders/pdf_loader.py` (crear)
- `src/infrastructure/rag/loaders/docx_loader.py` (crear)
- `src/infrastructure/rag/loaders/__init__.py` (modificar — exports)
- `tests/unit/test_file_validator.py` (crear)
- `tests/unit/test_pdf_loader.py` (crear)
- `tests/unit/test_docx_loader.py` (crear)
- `tests/fixtures/sample.pdf` (crear)
- `tests/fixtures/sample.docx` (crear)
- `tests/fixtures/invalid_file.txt` (crear — renamed as .pdf)

## Decisiones de diseno

- PyMuPDF sobre pdfplumber/pypdf: mejor extraccion de tablas, mas rapido, mejor soporte unicode
- Magic bytes sobre extension-only: previene upload de archivos maliciosos renombrados
- Interface comun `DocumentLoader`: permite agregar nuevos formatos (PPT, XLS) sin modificar codigo existente

## Out of scope

- Chunking del texto extraido (spec T3-S1-02)
- Deteccion de area funcional (spec T3-S1-02)
- Upload via API (post-MVP)
- OCR para PDFs escaneados (post-MVP)
