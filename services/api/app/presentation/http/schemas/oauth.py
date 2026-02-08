"""
OAuth schemas for request/response validation.
"""
from pydantic import BaseModel


class GoogleAuthUrlResponse(BaseModel):
    """Response for Google OAuth authorization URL."""
    auth_url: str
    state: str


class GoogleCallbackRequest(BaseModel):
    """Request body for Google OAuth callback."""
    code: str
    state: str | None = None
