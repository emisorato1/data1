"""
Google OAuth 2.0 Client

Handles interaction with Google OAuth APIs for authentication.
"""
from dataclasses import dataclass
from urllib.parse import urlencode
import secrets

import httpx

from app.core.config import settings


# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# OAuth scopes for authentication
GOOGLE_SCOPES = ["openid", "email", "profile"]


@dataclass
class GoogleUserInfo:
    """User information from Google OAuth."""
    id: str
    email: str
    verified_email: bool
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    picture: str | None = None


class GoogleOAuthClient:
    """Client for Google OAuth 2.0 authentication."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
    ):
        self.client_id = client_id or settings.GOOGLE_CLIENT_ID
        self.client_secret = client_secret or settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI

    def generate_state(self) -> str:
        """Generate a random state token for CSRF protection."""
        return secrets.token_urlsafe(32)

    def get_authorization_url(self, state: str | None = None) -> tuple[str, str]:
        """
        Generate Google OAuth authorization URL.
        
        Returns:
            Tuple of (authorization_url, state_token)
        """
        if state is None:
            state = self.generate_state()

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPES),
            "state": state,
            "access_type": "online",  # We don't need refresh tokens
            "prompt": "select_account",  # Always show account picker
        }

        url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
        return url, state

    async def exchange_code_for_tokens(self, code: str) -> dict:
        """
        Exchange authorization code for tokens.
        
        Args:
            code: Authorization code from Google callback
            
        Returns:
            Token response from Google (access_token, id_token, etc.)
            
        Raises:
            ValueError: If token exchange fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                },
            )

            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(
                    f"Token exchange failed: {error_data.get('error_description', error_data.get('error', 'Unknown error'))}"
                )

            return response.json()

    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        """
        Get user information from Google using access token.
        
        Args:
            access_token: Valid Google access token
            
        Returns:
            GoogleUserInfo with user details
            
        Raises:
            ValueError: If user info request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                raise ValueError("Failed to get user info from Google")

            data = response.json()
            return GoogleUserInfo(
                id=data["id"],
                email=data["email"],
                verified_email=data.get("verified_email", False),
                name=data.get("name"),
                given_name=data.get("given_name"),
                family_name=data.get("family_name"),
                picture=data.get("picture"),
            )

    async def authenticate(self, code: str) -> GoogleUserInfo:
        """
        Complete OAuth flow: exchange code and get user info.
        
        Args:
            code: Authorization code from Google callback
            
        Returns:
            GoogleUserInfo with user details
        """
        tokens = await self.exchange_code_for_tokens(code)
        access_token = tokens["access_token"]
        return await self.get_user_info(access_token)


# Singleton instance
google_oauth_client = GoogleOAuthClient()
