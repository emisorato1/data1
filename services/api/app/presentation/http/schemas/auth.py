from __future__ import annotations

from pydantic import BaseModel, EmailStr
from uuid import UUID


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_id: UUID | None = None
    # Opcional: especificar rol al registrarse (útil para testing)
    # Valores permitidos: "public", "private", "admin"
    role: str | None = None  # Por defecto será "private"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    tenant_id: UUID
    role: str
    is_active: bool
    auth_provider: str = "local"
    avatar_url: str | None = None
    full_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    user: UserResponse


class SessionResponse(BaseModel):
    user: UserResponse
