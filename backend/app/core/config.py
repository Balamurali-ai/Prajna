"""
====================================================
Application Configuration
====================================================
Centralized settings using Pydantic v2.
Loads from environment variables and .env file.
====================================================
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
BACKEND_ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_ENV_FILE,
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
    ALLOWED_HOSTS: List[str] = Field(default=["*"])

    # ----- CORS -----
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:5173"])
    CORS_ALLOW_CREDENTIALS: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        """
        Accept both:
        1. JSON array:
           ["http://localhost:5173","https://frontend.onrender.com"]

        2. Comma-separated string:
           http://localhost:5173,https://frontend.onrender.com
        """
        if value is None:
            return ["http://localhost:5173"]

        if isinstance(value, list):
            return value

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return ["http://localhost:5173"]

            # JSON array
            if value.startswith("["):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    raise ValueError(
                        "CORS_ORIGINS must be a valid JSON array."
                    )

            # Comma-separated string
            return [origin.strip() for origin in value.split(",") if origin.strip()]

        return ["http://localhost:5173"]

    # ----- Supabase -----
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = "dev-only-crime-intel-secret-do-not-use-in-prod"

    # ----- Database -----
    DATABASE_URL: str = ""
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # ----- Redis -----
    REDIS_URL: str = ""
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
