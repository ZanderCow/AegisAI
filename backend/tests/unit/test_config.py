from pathlib import Path

import pytest
from dotenv import dotenv_values

from src.core.config import Settings, get_settings

# Load every key/value from .env.example once at module level.
# dotenv_values strips inline comments, so entries like
# "ENVIRONMENT=development   # development | staging | production"
# are read as just "development".
ENV_EXAMPLE = dotenv_values(Path(__file__).parents[2] / ".env.example")


class TestEnvExample:
    """Settings should correctly load every value defined in .env.example."""

    @pytest.fixture(autouse=True)
    def set_env(self, monkeypatch):
        """Set all .env.example values as real environment variables."""
        for key, value in ENV_EXAMPLE.items():
            if value is not None:
                monkeypatch.setenv(key, value)

    def test_app_name(self):
        assert Settings().app_name == ENV_EXAMPLE["APP_NAME"]

    def test_app_version(self):
        assert Settings().app_version == ENV_EXAMPLE["APP_VERSION"]

    def test_environment(self):
        assert Settings().environment == ENV_EXAMPLE["ENVIRONMENT"]

    def test_debug(self):
        # "false" in the file should become a Python bool
        assert Settings().debug is False

    def test_database_url(self):
        assert Settings().database_url == ENV_EXAMPLE["DATABASE_URL"]

    def test_secret_key(self):
        assert Settings().secret_key == ENV_EXAMPLE["SECRET_KEY"]

    def test_algorithm(self):
        assert Settings().algorithm == ENV_EXAMPLE["ALGORITHM"]

    def test_access_token_expire_minutes(self):
        assert Settings().access_token_expire_minutes == int(ENV_EXAMPLE["ACCESS_TOKEN_EXPIRE_MINUTES"])

    def test_cors_origins(self):
        origins = Settings().cors_origins
        assert "http://localhost:3000" in origins
        assert "http://localhost:5173" in origins


class TestDefaults:
    """Settings should have sensible defaults with no env vars set."""

    def test_app_name(self):
        assert Settings().app_name == "AegisAI"

    def test_app_version(self):
        assert Settings().app_version == "0.1.0"

    def test_environment(self):
        assert Settings().environment == "development"

    def test_debug(self):
        assert Settings().debug is False

    def test_database_url(self):
        assert Settings().database_url.startswith("postgresql+asyncpg://")

    def test_algorithm(self):
        assert Settings().algorithm == "HS256"

    def test_access_token_expire_minutes(self):
        assert Settings().access_token_expire_minutes == 30

    def test_cors_origins(self):
        origins = Settings().cors_origins
        assert "http://localhost:3000" in origins
        assert "http://localhost:5173" in origins


class TestEnvOverrides:
    """Any setting should be overridable via environment variable."""

    def test_database_url(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@db:5432/mydb")
        assert Settings().database_url == "postgresql+asyncpg://user:pass@db:5432/mydb"

    def test_secret_key(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "supersecret")
        assert Settings().secret_key == "supersecret"

    def test_environment_staging(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "staging")
        assert Settings().environment == "staging"

    def test_environment_production(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "a" * 64)
        monkeypatch.setenv("ALLOWED_HOSTS", '["api.example.com"]')
        assert Settings().environment == "production"

    def test_debug(self, monkeypatch):
        monkeypatch.setenv("DEBUG", "true")
        assert Settings().debug is True

    def test_access_token_expire_minutes(self, monkeypatch):
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        assert Settings().access_token_expire_minutes == 60

    def test_cors_origins(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", '["http://example.com"]')
        assert Settings().cors_origins == ["http://example.com"]


class TestValidation:
    """Invalid values should raise an error at startup."""

    def test_invalid_environment(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "not_valid")
        with pytest.raises(Exception):
            Settings()

    def test_production_requires_strong_secret(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("ALLOWED_HOSTS", '["api.example.com"]')
        monkeypatch.setenv("SECRET_KEY", "weak")
        with pytest.raises(Exception):
            Settings()

    def test_production_disallows_wildcard_allowed_hosts(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "a" * 64)
        monkeypatch.setenv("ALLOWED_HOSTS", '["*"]')
        with pytest.raises(Exception):
            Settings()


class TestGetSettings:
    """get_settings() should return a cached singleton."""

    def test_returns_settings_instance(self):
        assert isinstance(get_settings(), Settings)

    def test_is_cached(self):
        assert get_settings() is get_settings()
