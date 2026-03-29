"""Configuracion centralizada via Pydantic BaseSettings."""

import logging
from typing import Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: SecretStr = SecretStr("postgresql+asyncpg://raguser:password@localhost:5432/rag_db")

    # Redis
    redis_url: SecretStr = SecretStr("redis://localhost:6379/0")

    # Auth
    jwt_secret: SecretStr

    # Google / Vertex AI
    use_vertex_ai: bool = False
    gemini_api_key: SecretStr = SecretStr("CHANGE_ME")
    gcp_project_id: str = ""
    gcp_quota_project_id: str = ""
    gcp_location: str = "us-central1"
    gcs_bucket_name: str = "itmind-rag-documents-dev"
    # CMEK: KMS key for GCS server-side encryption.
    # Format: projects/{project}/locations/{location}/keyRings/{ring}/cryptoKeys/{key}
    # Leave empty to use Google-managed encryption (default).
    gcs_kms_key_name: str = ""
    tenant_id: str = "default"

    @model_validator(mode="after")
    def _validate_vertex_ai_config(self) -> Self:
        """Require gcp_project_id when use_vertex_ai is enabled."""
        if self.use_vertex_ai and not self.gcp_project_id:
            raise ValueError(
                "gcp_project_id is required when use_vertex_ai=True. Set GCP_PROJECT_ID in your .env file."
            )
        return self

    gemini_model_flash: str = "gemini-2.0-flash"
    gemini_model_flash_lite: str = "gemini-2.0-flash-lite"
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_temperature: float = 0.2
    gemini_max_tokens: int = 2048

    # Langfuse
    langfuse_enabled: bool = True
    langfuse_public_key: SecretStr = SecretStr("pk-lf-CHANGE_ME")
    langfuse_secret_key: SecretStr = SecretStr("sk-lf-CHANGE_ME")
    langfuse_host: str = Field("http://localhost:3000", validation_alias="LANGFUSE_HOST")

    # Airflow
    airflow_api_url: str = "http://localhost:8080"

    # CORS (comma-separated string; parsed via property)
    cors_origins: str = "http://localhost:3000"

    # Security middleware
    trusted_hosts: str = "localhost,127.0.0.1,test"
    max_request_size_bytes: int = 50 * 1024 * 1024  # 50 MB

    # Rate limiting
    rate_limit_enabled: bool = True

    # Legacy IP-based limits (fallback for unauthenticated)
    rate_limit_ip_max_requests: int = 100
    rate_limit_ip_window_seconds: int = 60

    # Token Bucket limits (Authenticated users)
    # Default authenticated endpoint
    rate_limit_default_capacity: int = 20
    rate_limit_default_rate: float = 2.0  # tokens/sec

    # Chat endpoint
    rate_limit_chat_capacity: int = 5
    rate_limit_chat_rate: float = 0.5  # tokens/sec

    # Upload endpoint
    rate_limit_upload_capacity: int = 10
    rate_limit_upload_rate: float = 1.0  # tokens/sec

    # Admin users override
    rate_limit_admin_capacity: int = 100
    rate_limit_admin_rate: float = 10.0  # tokens/sec

    # Retrieval tuning (spec T3-S4-02)
    # ef_search: HNSW search precision. Higher = better recall, more latency.
    # Values: 40 (fast), 100 (balanced/production), 200 (high precision), 400 (max)
    # Ref: database-setup/references/ef-search-tuning.md
    retrieval_ef_search: int = 100
    # RRF weights: balance between vector and BM25 search (1.0/1.0 = equal weight)
    retrieval_vector_weight: float = 1.0
    retrieval_bm25_weight: float = 1.0
    # RRF smoothing constant (k=60 is the literature standard)
    retrieval_rrf_k: int = 60
    # Number of chunks after hybrid search fusion (input to reranker)
    retrieval_top_k: int = 20
    # Number of chunks after reranking (input to generation)
    reranker_top_k: int = 5
    # Memory retrieval tuning
    memory_retrieval_threshold: float = 0.7
    memory_top_k: int = 5
    # Max tokens/characters allocated to memories vs documents
    # ~2000 chars is roughly 500 tokens. This prevents memories from taking too much context length vs documents.
    memory_max_chars: int = 2000

    # Cloud DLP (spec T4-S6-02)
    # dlp_enabled: set True to use Cloud DLP API for PII sanitization.
    # When False (default), the local regex PiiSanitizer is used as fallback.
    dlp_enabled: bool = False
    # Minimum DLP finding likelihood to act on.
    # Options: VERY_UNLIKELY, UNLIKELY, POSSIBLE, LIKELY, VERY_LIKELY
    dlp_min_likelihood: str = "POSSIBLE"

    # Chunking (spec T6-S6-01 calibration)
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Similarity thresholds (spec T6-S6-01 calibration)
    similarity_threshold: float = 0.78
    reranking_threshold: float = 0.85

    # Faithfulness scoring (spec T4-S9-02)
    # Minimum faithfulness score (0.0-1.0) from LLM-as-judge.
    # Below this threshold the response is re-generated or blocked.
    faithfulness_threshold: float = 0.7

    # PII output detection (spec T4-S9-01)
    # Action when PII is detected in output: "redact" or "block"
    pii_output_action: str = "redact"
    # Number of PII detections that triggers automatic block
    pii_output_block_threshold: int = 3

    # Memory deduplication
    memory_dedup_threshold: float = 0.9

    # SSE / Chat
    sse_timeout_seconds: int = 60

    # App
    environment: str = "development"
    debug: bool = False
    app_version: str = "0.1.0"
    log_level: str = "INFO"

    @model_validator(mode="after")
    def _reject_placeholder_secrets(self) -> Self:
        """Reject CHANGE_ME placeholder secrets in non-development environments."""
        if self.environment == "development":
            return self
        secrets_to_check = {
            "gemini_api_key": self.gemini_api_key,
            "langfuse_public_key": self.langfuse_public_key,
            "langfuse_secret_key": self.langfuse_secret_key,
            "jwt_secret": self.jwt_secret,
        }
        for name, secret in secrets_to_check.items():
            if "CHANGE_ME" in secret.get_secret_value():
                raise ValueError(
                    f"{name} contains placeholder value 'CHANGE_ME'. "
                    f"Set a real value for environment '{self.environment}'."
                )
        # HS256 requires a strong secret
        if len(self.jwt_secret.get_secret_value()) < 32:
            raise ValueError(
                "jwt_secret must be at least 32 characters for HS256. "
                f"Current length: {len(self.jwt_secret.get_secret_value())}."
            )
        return self

    @model_validator(mode="after")
    def _warn_localhost_trusted_hosts(self) -> Self:
        """Warn when trusted_hosts only contains localhost entries in production."""
        if self.environment == "development":
            return self
        localhost_values = {"localhost", "127.0.0.1", "::1"}
        hosts = {h.strip() for h in self.trusted_hosts.split(",") if h.strip()}
        if hosts and hosts.issubset(localhost_values):
            logger.warning(
                "trusted_hosts contains only localhost entries (%s) in '%s' environment. "
                "Set TRUSTED_HOSTS to include your actual domain(s) to avoid 400 errors.",
                self.trusted_hosts,
                self.environment,
            )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [h.strip() for h in self.trusted_hosts.split(",") if h.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
