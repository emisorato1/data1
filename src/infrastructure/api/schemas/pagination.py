"""Cursor-based pagination schemas.

Keyset pagination using (created_at, id) as cursor.
O(1) performance vs O(n) for offset-based pagination.
"""

import base64
import json
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class CursorPage(BaseModel, Generic[T]):  # noqa: UP046
    """Response wrapper for cursor-based pagination."""

    items: list[T]
    next_cursor: str | None = Field(None, description="Cursor opaco para obtener la siguiente pagina.")
    has_more: bool
    limit: int

    @classmethod
    def create(
        cls,
        items: list[T],
        limit: int,
        cursor_field: str = "created_at",
        id_field: str = "id",
    ) -> "CursorPage[T]":
        """Build a CursorPage, trimming the extra detection row."""
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]

        next_cursor = None
        if items and has_more:
            last = items[-1]
            # Support both dicts and objects with attributes
            if isinstance(last, dict):
                ts = last[cursor_field]
                rid = last[id_field]
            else:
                ts = getattr(last, cursor_field)
                rid = getattr(last, id_field)
            next_cursor = encode_cursor(ts, rid)

        return cls(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
            limit=limit,
        )


def encode_cursor(timestamp: datetime, record_id: str | object) -> str:
    """Encode an opaque base64 cursor from timestamp + id."""
    payload = json.dumps(
        {
            "ts": timestamp.isoformat(),
            "id": str(record_id),
        }
    )
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    """Decode an opaque cursor. Raises ValueError on bad input."""
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        return datetime.fromisoformat(payload["ts"]), payload["id"]
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise ValueError(f"Invalid cursor: {e}") from e
