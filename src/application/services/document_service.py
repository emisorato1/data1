"""Document CRUD service.

Application service for listing, retrieving, and deleting documents.
Handles authorization checks and delegates to repository for data access.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.domain.repositories.document_repository import DocumentListFilters, DocumentListResult
from src.shared.exceptions import AuthorizationError, NotFoundError

if TYPE_CHECKING:
    from datetime import datetime

    from src.domain.repositories.document_repository import DocumentRepositoryBase
    from src.infrastructure.database.models.document import Document
    from src.infrastructure.database.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class DocumentDetail:
    """Detailed document information including pipeline status."""

    id: int
    filename: str
    file_path: str
    file_type: str | None
    file_size: int | None
    file_hash: str | None
    version: int
    status: str
    area: str
    classification_level: str | None
    uploaded_by: int | None
    chunk_count: int
    metadata: dict
    created_at: datetime
    updated_at: datetime


class DocumentService:
    """Service for document CRUD operations.

    Implements authorization logic:
    - Regular users can only access their own documents
    - Admin users (is_superuser=True) can access all documents
    """

    def __init__(self, document_repository: DocumentRepositoryBase) -> None:
        """Initialize the service.

        Args:
            document_repository: Repository for document persistence.
        """
        self._repo = document_repository

    async def list_documents(
        self,
        *,
        user: User,
        status: str | None = None,
        file_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> DocumentListResult:
        """List documents accessible to the user.

        Admin users see all documents. Regular users see only their own.

        Args:
            user: The authenticated user making the request.
            status: Filter by document status (pending, indexing, indexed, failed).
            file_type: Filter by MIME type.
            date_from: Filter documents created on or after this date.
            date_to: Filter documents created on or before this date.
            limit: Maximum number of documents to return.
            offset: Number of documents to skip.

        Returns:
            DocumentListResult with items and total_count.
        """
        filters = DocumentListFilters(
            status=status,
            file_type=file_type,
            date_from=date_from,
            date_to=date_to,
            # Only filter by uploaded_by for non-admin users
            uploaded_by=None if user.is_superuser else user.id,
            include_inactive=False,
        )

        result = await self._repo.list_documents(
            filters=filters,
            limit=limit,
            offset=offset,
        )

        logger.info(
            "list_documents user_id=%s is_admin=%s total=%d",
            user.id,
            user.is_superuser,
            result.total_count,
        )

        return result

    async def get_document(self, document_id: int, user: User) -> DocumentDetail:
        """Get detailed document information.

        Args:
            document_id: ID of the document to retrieve.
            user: The authenticated user making the request.

        Returns:
            DocumentDetail with full metadata and chunk count.

        Raises:
            NotFoundError: If document doesn't exist or is inactive.
            AuthorizationError: If user doesn't have access to the document.
        """
        result = await self._repo.get_by_id_with_chunk_count(document_id)

        if result is None:
            raise NotFoundError(
                message=f"Document {document_id} not found.",
                details={"document_id": document_id},
            )

        document, chunk_count = result

        # Check if document is active
        if not document.is_active:
            raise NotFoundError(
                message=f"Document {document_id} not found.",
                details={"document_id": document_id},
            )

        # Authorization check
        if not self._can_access(document, user):
            raise AuthorizationError(
                message="You don't have permission to access this document.",
                details={"document_id": document_id},
            )

        logger.info(
            "get_document document_id=%s user_id=%s",
            document_id,
            user.id,
        )

        return self._to_detail(document, chunk_count)

    async def delete_document(self, document_id: int, user: User) -> bool:
        """Soft delete a document.

        Marks the document as inactive. Actual cleanup of chunks,
        embeddings, and GCS files is handled asynchronously.

        Args:
            document_id: ID of the document to delete.
            user: The authenticated user making the request.

        Returns:
            True if document was deleted.

        Raises:
            NotFoundError: If document doesn't exist or is already deleted.
            AuthorizationError: If user doesn't have permission to delete.
        """
        document = await self._repo.get_by_id(document_id)

        if document is None or not document.is_active:
            raise NotFoundError(
                message=f"Document {document_id} not found.",
                details={"document_id": document_id},
            )

        # Authorization check
        if not self._can_delete(document, user):
            raise AuthorizationError(
                message="You don't have permission to delete this document.",
                details={"document_id": document_id},
            )

        success = await self._repo.soft_delete(document_id)

        logger.info(
            "delete_document document_id=%s user_id=%s",
            document_id,
            user.id,
        )

        return success

    def _can_access(self, document: Document, user: User) -> bool:
        """Check if user can access a document.

        Admins can access all documents.
        Regular users can only access documents they uploaded.
        """
        if user.is_superuser:
            return True
        return document.uploaded_by == user.id

    def _can_delete(self, document: Document, user: User) -> bool:
        """Check if user can delete a document.

        Same rules as access - admins can delete all, users their own.
        """
        return self._can_access(document, user)

    def _to_detail(self, document: Document, chunk_count: int) -> DocumentDetail:
        """Convert Document model to DocumentDetail."""
        return DocumentDetail(
            id=document.id,
            filename=document.filename,
            file_path=document.file_path,
            file_type=document.file_type,
            file_size=document.file_size,
            file_hash=document.file_hash,
            version=document.version,
            status=document.status,
            area=str(document.area.value) if document.area else "general",
            classification_level=document.classification_level,
            uploaded_by=document.uploaded_by,
            chunk_count=chunk_count,
            metadata=dict(document.metadata_) if document.metadata_ else {},
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
