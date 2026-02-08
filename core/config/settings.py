from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    env: str = "dev"
    cors_origins: str = "http://localhost:5173"

    database_url: str = "sqlite:///./dev.db"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 120

    # Google OAuth 2.0 settings
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:3000/api/auth/callback/google"

    class Config:
        env_file = ".env"


settings = Settings()