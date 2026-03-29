"""Abstract repository interface for documents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.infrastructure.database.models.document import Document


@dataclass
class DocumentListResult:
    """Result of paginated document listing."""

    items: list[Document]
    total_count: int


@dataclass
class DocumentListFilters:
    """Filters for document listing."""

    status: str | None = None
    file_type: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    uploaded_by: int | None = None
    include_inactive: bool = False


class DocumentRepositoryBase(ABC):
    """Port for document persistence operations."""

    @abstractmethod
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

    @abstractmethod
    async def get_by_id(self, document_id: int) -> Document | None:
        """Get a document by its primary key. Returns None if not found."""

    @abstractmethod
    async def get_by_id_with_chunk_count(self, document_id: int) -> tuple[Document, int] | None:
        """Get document with its chunk count.

        Returns tuple of (Document, chunk_count) or None if not found.
        """

    @abstractmethod
    async def find_by_hash(self, file_hash: str) -> Document | None:
        """Find an active document by its SHA-256 file hash.

        Returns None if no active document matches.
        """

    @abstractmethod
    async def list_documents(
        self,
        *,
        filters: DocumentListFilters,
        limit: int = 20,
        offset: int = 0,
    ) -> DocumentListResult:
        """List documents with pagination and filters.

        Args:
            filters: Filter criteria for the query.
            limit: Maximum number of documents to return.
            offset: Number of documents to skip.

        Returns:
            DocumentListResult with items and total_count.
        """

    @abstractmethod
    async def soft_delete(self, document_id: int) -> bool:
        """Mark a document as deleted (is_active=False).

        Returns True if the document was found and marked deleted,
        False if not found.
        """

    @abstractmethod
    async def update_after_indexing(
        self,
        document_id: int,
        *,
        file_hash: str,
        chunk_count: int,
        areas: dict[str, int],
    ) -> Document | None:
        """Update document metadata after successful indexing.

        Stores indexing results in the JSONB ``metadata`` column.
        Returns None if the document was not found.
        """
