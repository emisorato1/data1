"""Schemas for document management API."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class DocumentStatus(StrEnum):
    """Document processing status."""

    pending = "pending"
    indexing = "indexing"
    indexed = "indexed"
    failed = "failed"


class DocumentUploadResponse(BaseModel):
    """Response schema for a successfully uploaded document."""

    document_id: str = Field(..., description="Unique identifier of the uploaded document (pending processing)")
    filename: str = Field(..., description="Original name of the uploaded file")
    mime_type: str = Field(..., description="Detected MIME type of the file")
    size_bytes: int = Field(..., description="Size of the file in bytes")
    file_hash: str = Field(..., description="SHA-256 hash of the file content")
    status: str = Field("pending", description="Current status of the document")
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Upload timestamp")


class DocumentListItem(BaseModel):
    """Document item in list response."""

    id: int = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    file_type: str | None = Field(None, description="MIME type")
    file_size: int | None = Field(None, description="Size in bytes")
    status: str = Field(..., description="Processing status")
    area: str = Field("general", description="Functional area")
    uploaded_by: int | None = Field(None, description="User ID who uploaded")
    created_at: datetime = Field(..., description="Upload timestamp")

    model_config = {"from_attributes": True}


class PaginationLinks(BaseModel):
    """Pagination navigation links."""

    next: str | None = Field(None, description="URL for next page")
    prev: str | None = Field(None, description="URL for previous page")


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    items: list[DocumentListItem] = Field(..., description="List of documents")
    total_count: int = Field(..., description="Total number of documents matching filters")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Current offset")
    links: PaginationLinks = Field(..., description="Navigation links")


class DocumentDetailResponse(BaseModel):
    """Detailed document information."""

    id: int = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Storage path/URI")
    file_type: str | None = Field(None, description="MIME type")
    file_size: int | None = Field(None, description="Size in bytes")
    file_hash: str | None = Field(None, description="SHA-256 hash")
    version: int = Field(1, description="Document version")
    status: str = Field(..., description="Processing status")
    area: str = Field("general", description="Functional area")
    classification_level: str | None = Field(None, description="Security classification")
    uploaded_by: int | None = Field(None, description="User ID who uploaded")
    chunk_count: int = Field(0, description="Number of indexed chunks")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class DocumentDeleteResponse(BaseModel):
    """Response after document deletion."""

    id: int = Field(..., description="Deleted document ID")
    deleted: bool = Field(True, description="Deletion status")
    message: str = Field("Document marked for deletion", description="Status message")
