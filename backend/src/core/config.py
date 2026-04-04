"""Core configuration settings for the FastAPI application.

This module defines the global settings required for the application,
including database connections, security tokens, and the remote Chroma
server used by the RAG pipeline. These settings are loaded from
environment variables or a local .env file using Pydantic.
"""
import json
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_DEFAULT_CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://frontend:5173",
]


class Settings(BaseSettings):
    """Application settings and environment variables."""

    PROJECT_NAME: str = Field(
        default="FastAPI Auth API",
        description="The name of the project shown in OpenAPI docs.",
    )
    DATABASE_URL: str = Field(
        ...,
        description=(
            "Database connection string. Standard PostgreSQL URLs are normalized "
            "to the asyncpg driver automatically."
        ),
    )
    SECRET_KEY: str = Field(
        ...,
        description="The cryptographic key used for signing JWTs.",
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="The algorithm used for JWT signatures.",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Token expiration time in minutes.",
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="The current environment (e.g., development, production, testing).",
    )
    CORS_ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: _DEFAULT_CORS_ALLOWED_ORIGINS.copy(),
        description=(
            "Browser origins allowed to call the API via CORS. Accepts a "
            "comma-separated string or JSON array."
        ),
    )
    AUTO_CREATE_TABLES: bool | None = Field(
        default=None,
        description=(
            "When true, create SQL tables automatically on application startup. "
            "Defaults to enabled outside production and disabled in production."
        ),
    )
    GROQ_API_KEY: str = Field(default="", description="Groq API key for LLM access.")
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key for LLM access.")
    DEEPSEEK_API_KEY: str = Field(default="", description="DeepSeek API key for LLM access.")
    MOCK_PROVIDER_RESPONSES: bool = Field(
        default=False,
        description=(
            "When enabled, bypass external LLM providers and return deterministic "
            "local responses for end-to-end testing."
        ),
    )
    CHROMA_HOST: str = Field(
        default="localhost",
        description="Hostname for the remote Chroma server.",
    )
    CHROMA_PORT: int = Field(
        default=8000,
        description="Port for the remote Chroma server.",
    )
    CHROMA_SSL: bool = Field(
        default=False,
        description="Whether to use HTTPS when connecting to Chroma.",
    )
    CHROMA_COLLECTION_NAME: str = Field(
        default="rag_documents",
        description="Collection name used for RAG document storage.",
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Normalize Railway-style PostgreSQL URLs to the asyncpg dialect."""
        if not isinstance(value, str):
            return value

        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)

        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)

        return value

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def normalize_cors_allowed_origins(cls, value: str | list[str]) -> list[str]:
        """Normalize CORS origins from env-friendly strings to a clean list."""
        if isinstance(value, list):
            return [origin.strip() for origin in value if origin.strip()]

        if not isinstance(value, str):
            return value

        stripped = value.strip()
        if stripped.startswith("["):
            parsed = json.loads(stripped)
            return [origin.strip() for origin in parsed if origin.strip()]

        return [origin.strip() for origin in stripped.split(",") if origin.strip()]

    @model_validator(mode="after")
    def apply_environment_defaults(self) -> "Settings":
        """Apply environment-aware defaults after base field parsing.

        Production should not mutate schema automatically during startup.
        Development and testing keep the current convenient bootstrap behavior
        unless explicitly overridden with ``AUTO_CREATE_TABLES``.
        """
        if self.AUTO_CREATE_TABLES is None:
            self.AUTO_CREATE_TABLES = self.ENVIRONMENT.lower() != "production"

        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
