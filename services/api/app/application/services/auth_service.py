from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    decode_access_token,  # <- esto lo agregás si no existe (abajo te digo)
)
from app.domain.enums.role_name import RoleName
from app.infrastructure.db.repositories.role_repo import RoleRepository
from app.infrastructure.db.repositories.user_repo import UserRepository
from app.infrastructure.db.session import get_db
from app.infrastructure.http.google_oauth import GoogleUserInfo


bearer = HTTPBearer(auto_error=False)

# Default tenant for OAuth users (organization default)
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


class AuthService:
    def __init__(self, user_repo: UserRepository, role_repo: RoleRepository):
        self.user_repo = user_repo
        self.role_repo = role_repo

    async def register(self, *, email: str, password: str, tenant_id: UUID, role_name: str | None = None):
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ValueError("EMAIL_ALREADY_REGISTERED")

        # Usar el rol especificado o "private" por defecto
        target_role_name = role_name or RoleName.PRIVATE.value
        
        # Validar que el rol existe
        role = await self.role_repo.get_by_name(target_role_name)
        if not role:
            raise RuntimeError(f"ROLE_{target_role_name.upper()}_NOT_SEEDED")

        user = await self.user_repo.create(
            email=email,
            password_hash=hash_password(password),
            tenant_id=tenant_id,
            role_id=role.id,
        )
        return user

    async def login(self, *, email: str, password: str):
        user = await self.user_repo.get_by_email(email)
        if not user or not user.password_hash or not verify_password(password, user.password_hash):
            raise ValueError("INVALID_CREDENTIALS")

        if not user.is_active:
            raise ValueError("USER_INACTIVE")

        token = create_access_token(
            subject=str(user.id),
            role=user.role.name,
            tenant_id=str(user.tenant_id),
        )
        return token, user

    async def google_login(self, *, google_user: GoogleUserInfo, tenant_id: UUID | None = None):
        """
        Handle Google OAuth login/registration.
        
        Logic:
        1. Check if user exists by google_id -> login
        2. Check if user exists by email -> link Google account and login
        3. Create new user with Google data
        
        Args:
            google_user: User info from Google OAuth
            tenant_id: Optional tenant, defaults to organization default
            
        Returns:
            Tuple of (access_token, user)
        """
        # Check by Google ID first (already linked)
        user = await self.user_repo.get_by_google_id(google_user.id)
        if user:
            if not user.is_active:
                raise ValueError("USER_INACTIVE")
            
            token = create_access_token(
                subject=str(user.id),
                role=user.role.name,
                tenant_id=str(user.tenant_id),
            )
            return token, user

        # Check by email (link account if exists)
        user = await self.user_repo.get_by_email(google_user.email)
        if user:
            if not user.is_active:
                raise ValueError("USER_INACTIVE")
            
            # Link Google account to existing user
            user = await self.user_repo.update_google_info(
                user.id,
                google_id=google_user.id,
                avatar_url=google_user.picture,
                full_name=google_user.name,
            )
            
            token = create_access_token(
                subject=str(user.id),
                role=user.role.name,
                tenant_id=str(user.tenant_id),
            )
            return token, user

        # Create new user with Google data
        role = await self.role_repo.get_by_name(RoleName.PRIVATE.value)
        if not role:
            raise RuntimeError("ROLE_PRIVATE_NOT_SEEDED")

        user = await self.user_repo.create(
            email=google_user.email,
            password_hash=None,  # OAuth users don't have password
            tenant_id=tenant_id or DEFAULT_TENANT_ID,
            role_id=role.id,
            auth_provider="google",
            google_id=google_user.id,
            avatar_url=google_user.picture,
            full_name=google_user.name,
        )

        token = create_access_token(
            subject=str(user.id),
            role=user.role.name,
            tenant_id=str(user.tenant_id),
        )
        return token, user

    @classmethod
    async def current_user(
        cls,
        creds: HTTPAuthorizationCredentials | None = Depends(bearer),
        db: AsyncSession = Depends(get_db),
    ):
        if not creds or not creds.credentials:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="NOT_AUTHENTICATED")

        token = creds.credentials

        try:
            payload = decode_access_token(token)  # debe devolver dict con "sub"
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("missing sub")
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN")

        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(UUID(user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER_NOT_FOUND")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="USER_INACTIVE")

        return user

