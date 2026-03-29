"""DTOs (Data Transfer Objects) para el modulo de autenticacion."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request body para POST /api/v1/auth/login."""

    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)


class AuthUserResponse(BaseModel):
    """Datos de usuario retornados tras login/refresh exitoso."""

    user_id: int
    email: str
    full_name: str | None
    role: str


class TokenPayload(BaseModel):
    """Payload decodificado de un JWT access token."""

    sub: str
    exp: int
    iat: int
    role: str


class LogoutResponse(BaseModel):
    """Response body para POST /api/v1/auth/logout."""

    message: str = "Logged out successfully."
