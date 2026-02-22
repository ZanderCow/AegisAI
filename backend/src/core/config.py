from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "AegisAI"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] | None = None
    json_logs: bool | None = None
    uvicorn_access_log: bool | None = None
    enable_docs: bool | None = None
    enforce_https: bool = False
    allowed_hosts: list[str] = ["*"]

    # Database
    database_url: str = "postgresql+asyncpg://test_admin:test_password@localhost:5433/aegis_test_db"
    sql_echo: bool | None = None
    auto_create_tables: bool | None = None

    # JWT
    secret_key: str = "CHANGE_ME_use_openssl_rand_hex_32_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS — in .env use a JSON array: CORS_ORIGINS=["http://localhost:3000"]
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def effective_log_level(self) -> str:
        if self.log_level is not None:
            return self.log_level
        return "DEBUG" if self.is_development else "WARNING"

    @property
    def json_logs_enabled(self) -> bool:
        if self.json_logs is not None:
            return self.json_logs
        return self.environment == "production"

    @property
    def should_log_uvicorn_access(self) -> bool:
        if self.uvicorn_access_log is not None:
            return self.uvicorn_access_log
        return self.is_development

    @property
    def should_echo_sql(self) -> bool:
        if self.sql_echo is not None:
            return self.sql_echo
        return self.is_development

    @property
    def should_auto_create_tables(self) -> bool:
        if self.auto_create_tables is not None:
            return self.auto_create_tables
        return self.is_development

    @property
    def docs_enabled(self) -> bool:
        if self.enable_docs is not None:
            return self.enable_docs
        return self.environment != "production"

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.environment != "production":
            return self

        if self.secret_key.startswith("CHANGE_ME") or len(self.secret_key) < 32:
            raise ValueError("SECRET_KEY must be a strong random value in production.")

        if "*" in self.allowed_hosts:
            raise ValueError("ALLOWED_HOSTS cannot include '*' in production.")

        if any(origin.strip() == "*" for origin in self.cors_origins):
            raise ValueError("CORS_ORIGINS cannot include '*' in production.")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
