"""
====================================================
Application Configuration
====================================================
Centralized settings using Pydantic v2.
Loads from environment variables and .env file.
====================================================
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ----- Application -----
    APP_NAME: str = "crime-intelligence-backend"
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    APP_VERSION: str = "1.0.0"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_LOG_LEVEL: str = "INFO"
    APP_TIMEZONE: str = "UTC"
    ALLOWED_HOSTS: List[str] = ["*"]

    # ----- CORS -----
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ----- Supabase -----
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    # Dev-only fallback secret so /auth/login can mint a JWT in demos
    # without a real Supabase project. Override in production.
    SUPABASE_JWT_SECRET: str = "dev-only-crime-intel-secret-do-not-use-in-prod"

    # ----- Database -----
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/crime_intel"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # ----- Redis -----
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""
    REDIS_MAX_CONNECTIONS: int = 50
    CACHE_TTL_SECONDS: int = 300

    # ----- Auth -----
    JWT_ALGORITHM: str = "HS256"
    JWT_AUDIENCE: str = "authenticated"
    JWT_ISSUER: str = "supabase"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    RATE_LIMIT_PER_MINUTE: int = 100

    # ----- ML Artifacts -----
    # Default points to backend/app/ml_artifacts/ — where the ML team
    # drops their exported outputs. Override via env var
    # ML_ARTIFACTS_PATH for non-standard layouts.
    ML_ARTIFACTS_PATH: str = "./app/ml_artifacts"
    ML_CACHE_REFRESH_SECONDS: int = 900
    ML_HOTSPOT_TOP_N: int = 20

    # ----- Mapbox -----
    MAPBOX_PUBLIC_TOKEN: str = ""
    MAPBOX_SECRET_TOKEN: str = ""

    # ----- Observability -----
    SENTRY_DSN: str = ""
    PROMETHEUS_ENABLED: bool = False
    LOG_FORMAT: Literal["json", "text"] = "text"

    # ----- Feature Flags -----
    FEATURE_WEBSOCKETS: bool = True
    FEATURE_REPORTS_PDF: bool = True
    FEATURE_REPORTS_CSV: bool = True
    FEATURE_REPORTS_GEOJSON: bool = True

    # ----- Paths -----
    @property
    def PREDICTIONS_DIR(self) -> str:
        return f"{self.ML_ARTIFACTS_PATH}/predictions"

    @property
    def SHAP_DIR(self) -> str:
        return f"{self.ML_ARTIFACTS_PATH}/shap"

    @property
    def IS_PRODUCTION(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def IS_DEVELOPMENT(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def IS_TEST(self) -> bool:
        return self.APP_ENV == "test"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
