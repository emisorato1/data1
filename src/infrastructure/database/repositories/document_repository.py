"""SQLAlchemy implementation of DocumentRepositoryBase."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import func, select

from src.domain.repositories.document_repository import (
    DocumentListFilters,
    DocumentListResult,
    DocumentRepositoryBase,
)
from src.infrastructure.database.models.document import Document, DocumentChunk

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DocumentRepository(DocumentRepositoryBase):
    """Postgres-backed document repository.

    Does NOT call ``session.commit()`` — the caller is responsible for
    transaction boundaries.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        document_id: int,
        filename: str,
        file_path: str,
        file_type: str | None = None,
        file_size: int | None = None,
        file_hash: str | None = None,
        uploaded_by: int | None = None,
    ) -> Document:
        """Create a new document record and return it."""
        document = Document(
            id=document_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            file_hash=file_hash,
            uploaded_by=uploaded_by,
        )
        self._session.add(document)
        await self._session.flush()

        logger.info(
            "document_created document_id=%s filename=%s",
            document_id,
            filename,
        )
        return document

    async def get_by_id(self, document_id: int) -> Document | None:
        """Get a document by its primary key."""
        result = await self._session.execute(
            select(Document).where(Document.id == document_id),
        )
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def find_by_hash(self, file_hash: str) -> Document | None:
        """Find an active document by its SHA-256 file hash."""
        result = await self._session.execute(
            select(Document).where(
                Document.file_hash == file_hash,
                Document.is_active.is_(True),
            ),
        )
        return result.scalars().first()  # type: ignore[no-any-return]

    async def update_after_indexing(
        self,
        document_id: int,
        *,
        file_hash: str,
        chunk_count: int,
        areas: dict[str, int],
    ) -> Document | None:
        """Update document metadata after successful indexing.

        Stores ``chunk_count`` and ``areas`` in the JSONB ``metadata`` column
        (no ``chunk_count`` column exists on the table).
        """
        document = await self.get_by_id(document_id)
        if document is None:
            return None

        document.file_hash = file_hash

        # Merge indexing results into existing JSONB metadata
        current_meta = dict(document.metadata_) if document.metadata_ else {}
        current_meta["indexing"] = {
            "chunk_count": chunk_count,
            "areas": areas,
        }
        document.metadata_ = current_meta

        await self._session.flush()

        logger.info(
            "document_updated_after_indexing document_id=%s chunks=%d",
            document_id,
            chunk_count,
        )
        return document

    async def get_by_id_with_chunk_count(self, document_id: int) -> tuple[Document, int] | None:
        """Get document with its chunk count."""
        # Get document
        doc_result = await self._session.execute(
            select(Document).where(Document.id == document_id),
        )
        document = doc_result.scalar_one_or_none()
        if document is None:
            return None

        # Count chunks
        count_result = await self._session.execute(
            select(func.count(DocumentChunk.id)).where(
                DocumentChunk.document_id == document_id,
            ),
        )
        chunk_count = count_result.scalar() or 0

        return document, chunk_count

    async def list_documents(
        self,
        *,
        filters: DocumentListFilters,
        limit: int = 20,
        offset: int = 0,
    ) -> DocumentListResult:
        """List documents with pagination and filters."""
        # Base query
        query = select(Document)

        # Apply filters
        if not filters.include_inactive:
            query = query.where(Document.is_active.is_(True))

        if filters.status:
            query = query.where(Document.status == filters.status)

        if filters.file_type:
            query = query.where(Document.file_type == filters.file_type)

        if filters.date_from:
            query = query.where(Document.created_at >= filters.date_from)

        if filters.date_to:
            query = query.where(Document.created_at <= filters.date_to)

        if filters.uploaded_by:
            query = query.where(Document.uploaded_by == filters.uploaded_by)

        # Get total count (before pagination)
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self._session.execute(count_query)
        total_count = count_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Document.created_at.desc()).offset(offset).limit(limit)

        result = await self._session.execute(query)
        items = list(result.scalars().all())

        logger.debug(
            "list_documents total=%d returned=%d offset=%d",
            total_count,
            len(items),
            offset,
        )

        return DocumentListResult(items=items, total_count=total_count)

    async def soft_delete(self, document_id: int) -> bool:
        """Mark a document as deleted (is_active=False)."""
        document = await self.get_by_id(document_id)
        if document is None:
            return False

        document.is_active = False
        await self._session.flush()

        logger.info("document_soft_deleted document_id=%s", document_id)
        return True
