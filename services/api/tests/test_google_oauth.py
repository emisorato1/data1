"""
Tests for Google OAuth client.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.infrastructure.http.google_oauth import (
    GoogleOAuthClient,
    GoogleUserInfo,
    GOOGLE_AUTH_URL,
    GOOGLE_SCOPES,
)


class TestGoogleOAuthClient:
    """Tests for GoogleOAuthClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = GoogleOAuthClient(
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:3000/callback",
        )

    def test_generate_state(self):
        """Test state token generation."""
        state1 = self.client.generate_state()
        state2 = self.client.generate_state()
        
        # States should be non-empty strings
        assert isinstance(state1, str)
        assert len(state1) > 0
        
        # States should be unique
        assert state1 != state2

    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        url, state = self.client.get_authorization_url()
        
        # URL should start with Google auth endpoint
        assert url.startswith(GOOGLE_AUTH_URL)
        
        # URL should contain required parameters
        assert "client_id=test-client-id" in url
        assert "redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fcallback" in url
        assert "response_type=code" in url
        assert "scope=" in url
        assert f"state={state}" in url
        
        # State should be returned
        assert isinstance(state, str)
        assert len(state) > 0

    def test_get_authorization_url_with_custom_state(self):
        """Test authorization URL with custom state."""
        custom_state = "my-custom-state-token"
        url, state = self.client.get_authorization_url(state=custom_state)
        
        assert f"state={custom_state}" in url
        assert state == custom_state

    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_success(self):
        """Test successful token exchange."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test-access-token",
            "id_token": "test-id-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            tokens = await self.client.exchange_code_for_tokens("test-auth-code")
            
            assert tokens["access_token"] == "test-access-token"
            assert tokens["id_token"] == "test-id-token"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_failure(self):
        """Test failed token exchange."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Code has expired",
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(ValueError) as exc_info:
                await self.client.exchange_code_for_tokens("expired-code")
            
            assert "Code has expired" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_user_info_success(self):
        """Test successful user info retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123456789",
            "email": "user@example.com",
            "verified_email": True,
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": "https://example.com/photo.jpg",
        }
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            user_info = await self.client.get_user_info("test-access-token")
            
            assert isinstance(user_info, GoogleUserInfo)
            assert user_info.id == "123456789"
            assert user_info.email == "user@example.com"
            assert user_info.verified_email is True
            assert user_info.name == "Test User"
            assert user_info.picture == "https://example.com/photo.jpg"

    @pytest.mark.asyncio
    async def test_get_user_info_failure(self):
        """Test failed user info retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            with pytest.raises(ValueError) as exc_info:
                await self.client.get_user_info("invalid-token")
            
            assert "Failed to get user info" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_full_flow(self):
        """Test full authentication flow."""
        # Mock token exchange
        token_response = MagicMock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test-access-token",
            "token_type": "Bearer",
        }
        
        # Mock user info
        userinfo_response = MagicMock()
        userinfo_response.status_code = 200
        userinfo_response.json.return_value = {
            "id": "123456",
            "email": "user@example.com",
            "verified_email": True,
            "name": "Test User",
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_post.return_value = token_response
                mock_get.return_value = userinfo_response
                
                user_info = await self.client.authenticate("test-code")
                
                assert user_info.id == "123456"
                assert user_info.email == "user@example.com"
