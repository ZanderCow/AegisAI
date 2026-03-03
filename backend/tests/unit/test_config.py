"""Unit tests for the application configuration module.

This module contains tests verifying that the environment variables and
application settings are loaded correctly via Pydantic BaseSettings, and
that validation fails appropriately when required variables are missing.
"""
from typing import Any
import pytest
from pydantic import ValidationError
from pytest import MonkeyPatch

from src.core.config import Settings

def test_config_loads_defaults(monkeypatch: MonkeyPatch) -> None:
    """Tests that default settings are loaded correctly.
    
    Verifies that when minimal required environment variables are provided,
    Pydantic successfully instantiates the Settings object with the correct
    default fallback values for optional attributes.
    
    Args:
        monkeypatch (MonkeyPatch): Pytest fixture for safely modifying env vars.
    """
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "super_secret_test_key_32_chars_now")
    
    # Optional values should use defaults
    monkeypatch.delenv("ALGORITHM", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    
    settings = Settings()
    
    assert settings.PROJECT_NAME == "FastAPI Auth API"
    assert settings.DATABASE_URL == "sqlite+aiosqlite:///:memory:"
    assert settings.SECRET_KEY == "super_secret_test_key_32_chars_now"
    assert settings.ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert settings.ENVIRONMENT == "development"

def test_config_overrides_defaults(monkeypatch: MonkeyPatch) -> None:
    """Tests overriding default settings via environment variables.
    
    Verifies that explicit environment variables properly override the
    hardcoded Pydantic default field values.
    
    Args:
        monkeypatch (MonkeyPatch): Pytest fixture for safely modifying env vars.
    """
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("SECRET_KEY", "custom_key")
    monkeypatch.setenv("PROJECT_NAME", "Custom Testing App")
    monkeypatch.setenv("ALGORITHM", "HS512")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("ENVIRONMENT", "production")
    
    settings = Settings()
    
    assert settings.PROJECT_NAME == "Custom Testing App"
    assert settings.ALGORITHM == "HS512"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60
    assert settings.ENVIRONMENT == "production"

def test_config_validation_error_missing_db(monkeypatch: MonkeyPatch) -> None:
    """Tests Pydantic validation when DATABASE_URL is missing.
    
    Verifies that `Settings` raises a standard ValidationError during 
    instantiation if the required `DATABASE_URL` variable is omittted.
    
    Args:
        monkeypatch (MonkeyPatch): Pytest fixture for safely modifying env vars.
    """
    monkeypatch.setenv("SECRET_KEY", "some_key")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    
    with pytest.raises(ValidationError) as exc_info:
        Settings()
        
    error_msg = str(exc_info.value)
    assert "DATABASE_URL" in error_msg
    assert "Field required" in error_msg

def test_config_validation_error_missing_secret_key(monkeypatch: MonkeyPatch) -> None:
    """Tests Pydantic validation when SECRET_KEY is missing.
    
    Verifies that `Settings` raises a standard ValidationError during 
    instantiation if the required `SECRET_KEY` variable is omittted.
    
    Args:
        monkeypatch (MonkeyPatch): Pytest fixture for safely modifying env vars.
    """
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    
    with pytest.raises(ValidationError) as exc_info:
        Settings()
        
    error_msg = str(exc_info.value)
    assert "SECRET_KEY" in error_msg
    assert "Field required" in error_msg
