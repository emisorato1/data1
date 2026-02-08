from __future__ import annotations

from urllib.parse import quote

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    ENV: str = "dev"
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = ""

    DB_DRIVER: str = "postgresql+asyncpg"
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 120

    ACCESS_TOKEN_EXPIRES_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRES_DAYS: int = 30
    JWT_ISSUER: str = "enterprise-ai-platform"
    JWT_AUDIENCE: str = "enterprise-ai-platform-api"

    # Cookies
    COOKIE_NAME: str = "eai_access_token"
    
    @computed_field
    @property
    def COOKIE_SECURE(self) -> bool:
        return self.ENV != "dev"  # Secure=True en prod/staging


    RAG_BASE_URL: str = "http://rag-generation:2024"
    RAG_ASSISTANT_ID: str = "rag_generation"
    RAG_TIMEOUT_SECONDS: int = 60

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # Langfuse Observability    
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_BASE_URL: str = "https://us.cloud.langfuse.com"
    LANGFUSE_ENABLED: bool = False  # Toggle para habilitar/deshabilitar

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        user = quote(self.DB_USER)
        pwd = quote(self.DB_PASSWORD)
        return f"{self.DB_DRIVER}://{user}:{pwd}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()