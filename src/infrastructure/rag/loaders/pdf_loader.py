import logging
from pathlib import Path
from typing import Any

import fitz

from .base import DocumentLoader
from .models import LoadedDocument

logger = logging.getLogger(__name__)


class PDFLoader(DocumentLoader):
    """Cargador de documentos PDF usando PyMuPDF."""

    def load(self, file_path: Path) -> LoadedDocument:
        """Extrae texto, metadata y tablas de un PDF."""
        doc = None
        try:
            doc = fitz.open(str(file_path))
            full_text = []
            tables_count = 0

            for page in doc:
                full_text.append(page.get_text())

                try:
                    tabs = page.find_tables()
                    if tabs and tabs.tables:
                        tables_count += len(tabs.tables)
                        for table in tabs.tables:
                            df = table.to_pandas()
                            full_text.append("\n[TABLA]\n" + df.to_markdown(index=False) + "\n[/TABLA]\n")
                except Exception as exc:
                    logger.warning("table_extraction_failed page=%s error=%s", page.number, str(exc))

            metadata = self._extract_metadata(doc, file_path)

            return LoadedDocument(
                text="\n".join(full_text), metadata=metadata, pages=len(doc), tables_count=tables_count
            )
        except Exception as e:
            raise Exception(f"Error cargando PDF {file_path}: {e}") from e
        finally:
            if doc:
                doc.close()

    def _extract_metadata(self, doc: fitz.Document, file_path: Path) -> dict[str, Any]:
        info = doc.metadata or {}
        return {
            "source": str(file_path.name),
            "title": info.get("title") or file_path.stem,
            "author": info.get("author") or "Unknown",
            "subject": info.get("subject") or "",
            "keywords": info.get("keywords") or "",
            "creator": info.get("creator") or "",
            "producer": info.get("producer") or "",
            "file_size": file_path.stat().st_size,
        }
