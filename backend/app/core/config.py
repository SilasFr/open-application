"""Application configuration, loaded from the environment / ``.env``."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven settings. Secrets default to empty so the app and tests
    can boot without a live Supabase/Anthropic configuration; the routes that need
    them fail loudly only when actually invoked."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Open Application"
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"

    supabase_url: str = ""
    supabase_service_key: str = ""
    # Legacy HS256 projects set this; asymmetric-key projects leave it empty and
    # tokens are verified against the JWKS endpoint derived from supabase_url.
    supabase_jwt_secret: str = ""
    supabase_jwt_audience: str = "authenticated"

    ai_provider: str = "gemini"
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    ai_model: str = "gemini-2.0-flash"
    ai_max_tokens: int = Field(default=4096, gt=0)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def supabase_issuer(self) -> str:
        base = self.supabase_url.rstrip("/")
        return f"{base}/auth/v1" if base else ""

    @property
    def supabase_jwks_url(self) -> str:
        base = self.supabase_url.rstrip("/")
        return f"{base}/auth/v1/.well-known/jwks.json" if base else ""


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (single source of truth for config)."""

    return Settings()
