"""Abstract repository interface for conversations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid

    from src.infrastructure.database.models.conversation import Conversation


class ConversationRepositoryBase(ABC):
    """Port for conversation persistence operations."""

    @abstractmethod
    async def create(self, user_id: int, title: str | None = None) -> Conversation:
        """Create a new conversation and return it."""

    @abstractmethod
    async def list_by_user(
        self,
        user_id: int,
        cursor: str | None = None,
        limit: int = 20,
    ) -> list[Conversation]:
        """List active conversations for a user with cursor pagination.

        Returns up to ``limit + 1`` rows so the caller can detect *has_more*.
        """

    @abstractmethod
    async def get_by_id(self, conversation_id: uuid.UUID, user_id: int) -> Conversation | None:
        """Get a single conversation with messages. Returns None if not found or not owned."""

    @abstractmethod
    async def update(
        self,
        conversation_id: uuid.UUID,
        user_id: int,
        title: str | None = None,
        is_pinned: bool | None = None,
        is_favorite: bool | None = None,
    ) -> Conversation | None:
        """Update a conversation. Returns None if not found or not owned."""

    @abstractmethod
    async def soft_delete(self, conversation_id: uuid.UUID, user_id: int) -> bool:
        """Soft-delete a conversation. Returns True if deleted, False if not found/owned."""
