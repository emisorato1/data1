"""
Tests for auth routes including Google OAuth endpoints.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import UUID

from httpx import AsyncClient

from app.infrastructure.http.google_oauth import GoogleUserInfo


class TestAuthRoutes:
    """Tests for authentication routes."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "tenant_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["is_active"] is True
        assert data["auth_provider"] == "local"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email."""
        # Register first user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password123",
                "tenant_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        
        # Try to register with same email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "differentpassword",
                "tenant_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        
        assert response.status_code == 409
        assert response.json()["detail"] == "EMAIL_ALREADY_REGISTERED"

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        # Register user first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "logintest@example.com",
                "password": "testpassword123",
                "tenant_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "logintest@example.com",
                "password": "testpassword123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "logintest@example.com"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            },
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "INVALID_CREDENTIALS"


class TestGoogleOAuthRoutes:
    """Tests for Google OAuth routes."""

    @pytest.mark.asyncio
    async def test_get_google_auth_url(self, client: AsyncClient):
        """Test getting Google auth URL."""
        response = await client.get("/api/v1/auth/google/url")
        
        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "state" in data
        assert "accounts.google.com" in data["auth_url"]
        assert len(data["state"]) > 0

    @pytest.mark.asyncio
    async def test_google_callback_new_user(self, client: AsyncClient):
        """Test Google OAuth callback for new user."""
        mock_google_user = GoogleUserInfo(
            id="google-123456",
            email="newgoogleuser@example.com",
            verified_email=True,
            name="Google User",
            picture="https://example.com/photo.jpg",
        )
        
        with patch(
            "app.presentation.http.routes.auth.google_oauth_client.authenticate",
            new_callable=AsyncMock,
        ) as mock_auth:
            mock_auth.return_value = mock_google_user
            
            response = await client.post(
                "/api/v1/auth/google/callback",
                json={"code": "test-auth-code", "state": "test-state"},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["user"]["email"] == "newgoogleuser@example.com"
            assert data["user"]["auth_provider"] == "google"
            assert data["user"]["full_name"] == "Google User"

    @pytest.mark.asyncio
    async def test_google_callback_existing_user_link(self, client: AsyncClient):
        """Test Google OAuth linking to existing email/password user."""
        # First register a regular user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "existing@example.com",
                "password": "password123",
                "tenant_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        
        # Now login with Google using same email
        mock_google_user = GoogleUserInfo(
            id="google-existing-user",
            email="existing@example.com",
            verified_email=True,
            name="Existing User",
            picture="https://example.com/photo.jpg",
        )
        
        with patch(
            "app.presentation.http.routes.auth.google_oauth_client.authenticate",
            new_callable=AsyncMock,
        ) as mock_auth:
            mock_auth.return_value = mock_google_user
            
            response = await client.post(
                "/api/v1/auth/google/callback",
                json={"code": "test-auth-code"},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["email"] == "existing@example.com"
            # User should now have Google linked
            assert data["user"]["full_name"] == "Existing User"

    @pytest.mark.asyncio
    async def test_google_callback_unverified_email(self, client: AsyncClient):
        """Test Google OAuth callback with unverified email."""
        mock_google_user = GoogleUserInfo(
            id="google-unverified",
            email="unverified@example.com",
            verified_email=False,
            name="Unverified User",
        )
        
        with patch(
            "app.presentation.http.routes.auth.google_oauth_client.authenticate",
            new_callable=AsyncMock,
        ) as mock_auth:
            mock_auth.return_value = mock_google_user
            
            response = await client.post(
                "/api/v1/auth/google/callback",
                json={"code": "test-auth-code"},
            )
            
            assert response.status_code == 400
            assert "GOOGLE_EMAIL_NOT_VERIFIED" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_google_callback_auth_failure(self, client: AsyncClient):
        """Test Google OAuth callback when authentication fails."""
        with patch(
            "app.presentation.http.routes.auth.google_oauth_client.authenticate",
            new_callable=AsyncMock,
        ) as mock_auth:
            mock_auth.side_effect = ValueError("Token exchange failed")
            
            response = await client.post(
                "/api/v1/auth/google/callback",
                json={"code": "invalid-code"},
            )
            
            assert response.status_code == 400
            assert "GOOGLE_AUTH_FAILED" in response.json()["detail"]


class TestSessionRoutes:
    """Tests for session/me routes."""

    @pytest.mark.asyncio
    async def test_get_session_authenticated(self, client: AsyncClient):
        """Test getting session for authenticated user."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "sessiontest@example.com",
                "password": "password123",
                "tenant_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "sessiontest@example.com",
                "password": "password123",
            },
        )
        token = login_response.json()["access_token"]
        
        # Get session
        response = await client.get(
            "/api/v1/auth/session",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        assert response.json()["user"]["email"] == "sessiontest@example.com"

    @pytest.mark.asyncio
    async def test_get_session_unauthenticated(self, client: AsyncClient):
        """Test getting session without authentication."""
        response = await client.get("/api/v1/auth/session")
        
        assert response.status_code == 401
