"""Ring-Fenced RAG — configuration management.

Uses pydantic-settings for type-safe configuration with multiple override layers:
1. Environment variables (highest priority)
2. Config file (~/.rfr/config.toml or $RFR_CONFIG_PATH)
3. Default values (lowest priority)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_config_path() -> Path:
    """Return the default config file path."""
    return Path.home() / ".rfr" / "config.toml"


class LLMConfig(BaseSettings):
    """Configuration for the LLM provider."""

    model_config = SettingsConfigDict(env_prefix="rfr_llm_")

    provider: Literal["vllm", "ollama", "lm-studio", "openai", "custom"] = Field(
        default="ollama",
        description="LLM provider type",
    )
    base_url: str = Field(
        default="http://localhost:11434/v1",
        description="Base URL for the OpenAI-compatible API endpoint",
    )
    model: str = Field(
        default="llama3.2:3b",
        description="Model name to use for generation",
    )
    api_key: str = Field(
        default="not-needed",
        description="API key for the LLM provider (if required)",
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Generation temperature (lower = more deterministic)",
    )
    max_tokens: int = Field(
        default=1024,
        ge=64,
        le=32768,
        description="Maximum tokens in the generated response",
    )
    timeout_seconds: int = Field(
        default=60,
        ge=5,
        le=300,
        description="Timeout for LLM API calls in seconds",
    )


class EmbeddingConfig(BaseSettings):
    """Configuration for the embedding model."""

    model_config = SettingsConfigDict(env_prefix="rfr_embed_")

    model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence-transformers model name for embeddings",
    )
    dimension: int = Field(
        default=384,
        ge=64,
        le=4096,
        description="Vector dimension (must match the model output)",
    )
    device: str = Field(
        default="cpu",
        description="Device for embedding inference: 'cpu' or 'cuda'",
    )
    batch_size: int = Field(
        default=32,
        ge=1,
        le=512,
        description="Batch size for embedding generation",
    )


class IngestionConfig(BaseSettings):
    """Configuration for the ingestion pipeline."""

    model_config = SettingsConfigDict(env_prefix="rfr_ingest_")

    chunk_size: int = Field(
        default=512,
        ge=64,
        le=8192,
        description="Target chunk size in tokens",
    )
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        le=512,
        description="Token overlap between consecutive chunks",
    )
    default_role: str = Field(
        default="user",
        description="Default role assigned when no role metadata is provided",
    )
    cleanup_mode: Literal["incremental", "full", "none"] = Field(
        default="incremental",
        description="SQLRecordManager cleanup mode for idempotent indexing",
    )
    max_file_size_mb: int = Field(
        default=100,
        ge=1,
        le=1024,
        description="Maximum allowed file size for ingestion in MB",
    )


class DatabaseConfig(BaseSettings):
    """Configuration for the database connection."""

    model_config = SettingsConfigDict(env_prefix="rfr_db_")

    url: str = Field(
        default="",
        description="Full database connection URL. "
        "MUST be set via RFR_DB__URL environment variable in production. "
        "Example: postgresql+psycopg://user:password@host:5432/dbname",
    )
    _require_url: bool = False
    pool_size: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Database connection pool size",
    )
    max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Maximum overflow connections",
    )
    echo: bool = Field(
        default=False,
        description="Enable SQL statement logging",
    )

    @property
    def sync_url(self) -> str:
        """Return the sync-compatible URL (psycopg, not async)."""
        return self.url


class RedisConfig(BaseSettings):
    """Configuration for the Redis connection."""

    model_config = SettingsConfigDict(env_prefix="rfr_redis_")

    url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )


class AuthConfig(BaseSettings):
    """Configuration for API key authentication."""

    model_config = SettingsConfigDict(env_prefix="rfr_auth_")

    enabled: bool = Field(
        default=True,
        description="Enable API key authentication",
    )
    admin_roles: list[str] = Field(
        default=["admin"],
        description="Roles that have admin-level access",
    )
    allowed_roles: list[str] = Field(
        default=["admin", "senior_engineer", "junior_engineer", "user"],
        description="All valid role names in the system",
    )


class TelemetryConfig(BaseSettings):
    """Configuration for observability and tracing."""

    model_config = SettingsConfigDict(env_prefix="rfr_telemetry_")

    enabled: bool = Field(
        default=False,
        description="Enable LLM observability tracing",
    )
    provider: Literal["langfuse", "phoenix", "none"] = Field(
        default="none",
        description="Observability provider",
    )
    endpoint: str = Field(
        default="",
        description="Observability endpoint URL",
    )
    trace_retention_days: int = Field(
        default=7,
        ge=1,
        le=90,
        description="Days to retain full traces before aggregation",
    )


class ServerConfig(BaseSettings):
    """Configuration for the FastAPI server."""

    model_config = SettingsConfigDict(env_prefix="rfr_server_")

    host: str = Field(
        default="0.0.0.0",
        description="Server bind address",
    )
    port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="Server port",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level",
    )
    workers: int = Field(
        default=1,
        ge=1,
        le=16,
        description="Number of uvicorn workers",
    )
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:8000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8000",
        ],
        description="Allowed CORS origins for browser requests",
    )
    rate_limit_per_minute: int = Field(
        default=60,
        ge=0,
        le=10000,
        description="Max requests per minute per API key (0 = unlimited)",
    )
    ssl_certfile: str = Field(
        default="",
        description=(
            "Path to SSL certificate file for HTTPS. "
            "Set via RFR_SERVER__SSL_CERTFILE env var. "
            "Leave empty for plain HTTP."
        ),
    )
    ssl_keyfile: str = Field(
        default="",
        description=(
            "Path to SSL private key file for HTTPS. "
            "Set via RFR_SERVER__SSL_KEYFILE env var. "
            "Leave empty for plain HTTP."
        ),
    )


class AppConfig(BaseSettings):
    """Root configuration model for Ring-Fenced RAG.

    Loads from environment variables (RFR_* prefix), config file, and defaults.
    """

    model_config = SettingsConfigDict(
        env_prefix="rfr_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Nested config sections
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)

    # Top-level settings
    data_dir: str = Field(
        default=str(Path.home() / ".rfr" / "data"),
        description="Directory for local data storage",
    )
    standalone: bool = Field(
        default=False,
        description="Run in standalone mode (SQLite, no Docker)",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode with verbose logging",
    )

    @field_validator("data_dir")
    @classmethod
    def _ensure_data_dir(cls, v: str) -> str:
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @model_validator(mode="after")
    def _require_db_url(self) -> AppConfig:
        """Require database URL when not in standalone mode."""
        if not self.standalone and not self.database.url:
            raise ValueError(
                "Database URL (RFR_DB__URL) is required when not in standalone mode. "
                "Set RFR_DB__URL or use RFR_STANDALONE=true for SQLite."
            )
        return self

    def save(self, path: Path | None = None) -> None:
        """Save the current config to a TOML file."""
        import tomllib  # noqa: F401

        save_path = path or _default_config_path()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        # Use model_dump to serialize and write as TOML
        data = self.model_dump(mode="python")
        lines = ["# Ring-Fenced RAG Configuration\n"]
        for section, values in data.items():
            if isinstance(values, dict):
                lines.append(f"\n[{section}]")
                for k, v in values.items():
                    if isinstance(v, list):
                        v_str = ", ".join(repr(x) for x in v)
                        lines.append(f"{k} = [{v_str}]")
                    elif isinstance(v, str):
                        lines.append(f'{k} = "{v}"')
                    else:
                        lines.append(f"{k} = {v}")
            elif isinstance(v, str):
                lines.append(f'{section} = "{v}"')
            else:
                lines.append(f"{section} = {v}")
        save_path.write_text("\n".join(lines) + "\n")


def load_config(path: str | Path | None = None) -> AppConfig:
    """Load configuration from file and environment variables.

    Args:
        path: Optional explicit path to the config file. If None,
              uses the default location (~/.rfr/config.toml).

    Returns:
        Resolved AppConfig instance with all overrides applied.

    """
    if path is not None:
        os.environ["RFR_CONFIG_PATH"] = str(path)
    return AppConfig()  # type: ignore[call-arg]
