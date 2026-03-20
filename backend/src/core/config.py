"""Core configuration settings for the FastAPI application.

This module defines the global settings required for the application,
including database connections and security tokens. These settings are
loaded from environment variables or a local .env file using Pydantic.
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings and environment variables.
    
    Attributes:
        PROJECT_NAME (str): The name of the project shown in OpenAPI docs.
        DATABASE_URL (str): The PostgreSQL connection string using asyncpg.
        SECRET_KEY (str): The cryptographic key used for signing JWTs.
        ALGORITHM (str): The algorithm used for JWT signatures.
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Token expiration time in minutes.
        ENVIRONMENT (str): The current environment (e.g., development, production).
    """
    PROJECT_NAME: str = Field(default="FastAPI Auth API", description="The name of the project shown in OpenAPI docs.")
    DATABASE_URL: str = Field(..., description="The PostgreSQL connection string using asyncpg.")
    SECRET_KEY: str = Field(..., description="The cryptographic key used for signing JWTs.")
    ALGORITHM: str = Field(default="HS256", description="The algorithm used for JWT signatures.")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Token expiration time in minutes.")
    ENVIRONMENT: str = Field(default="development", description="The current environment (e.g., development, production, testing).")
    GROQ_API_KEY: str = Field(default="", description="Groq API key for LLM access.")
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key for LLM access.")
    DEEPSEEK_API_KEY: str = Field(default="", description="DeepSeek API key for LLM access.")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
