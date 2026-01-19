"""Application settings using Pydantic BaseSettings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.
    
    Loads configuration from environment variables and .env file.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    app_name: str = Field(default="Hyper-Porto API", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    app_host: str = Field(default="0.0.0.0", description="Server host")
    app_port: int = Field(default=8000, description="Server port")
    app_debug: bool = Field(default=False, description="Debug mode")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment",
    )
    
    # Database
    db_url: str = Field(
        default="sqlite:///data/app.db",
        description="Database URL",
    )
    
    # Redis (for cache and background tasks)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL",
    )
    
    # JWT
    jwt_secret: str = Field(
        default="your-super-secret-key-change-in-production",
        description="JWT secret key",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT access token expiration in hours")
    jwt_refresh_expiration_days: int = Field(default=7, description="JWT refresh token expiration in days")
    
    # Security
    bcrypt_rounds: int = Field(default=12, description="Bcrypt hashing rounds")
    
    # CORS
    cors_allow_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow CORS credentials")
    cors_allow_methods: list[str] = Field(
        default=["*"],
        description="Allowed CORS methods",
    )
    cors_allow_headers: list[str] = Field(
        default=["*"],
        description="Allowed CORS headers",
    )
    
    # Logfire
    logfire_token: str | None = Field(default=None, description="Logfire token")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.
    
    Returns:
        Cached Settings instance.
    """
    return Settings()

