"""Composition root: wires concrete implementations to interfaces for FastAPI DI.

This is the ONLY place that knows how to construct Supabase clients and the Anthropic
client. Routers depend on the ``get_*_service`` providers, services depend on domain
interfaces, and swapping an implementation means changing only this file.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from supabase import Client, create_client

from app.core.config import Settings, get_settings
from app.domain.ai import AIClient
from app.domain.auth import TokenVerifier
from app.domain.repositories import ApplicationRepository
from app.infrastructure.ai.anthropic_client import AnthropicClient
from app.infrastructure.ai.prompts import load_prompt
from app.infrastructure.auth.supabase_verifier import SupabaseTokenVerifier
from app.infrastructure.supabase.application_repository import (
    SupabaseApplicationRepository,
)
from app.services.application_service import ApplicationService
from app.services.cv_tailoring_service import CVTailoringService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_supabase_client(settings: SettingsDep) -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)


SupabaseDep = Annotated[Client, Depends(get_supabase_client)]


def get_application_repository(client: SupabaseDep) -> ApplicationRepository:
    return SupabaseApplicationRepository(client)


ApplicationRepositoryDep = Annotated[
    ApplicationRepository, Depends(get_application_repository)
]


def get_application_service(repository: ApplicationRepositoryDep) -> ApplicationService:
    return ApplicationService(repository)


def get_ai_client(settings: SettingsDep) -> AIClient:
    return AnthropicClient(
        api_key=settings.anthropic_api_key,
        model=settings.ai_model,
        max_tokens=settings.ai_max_tokens,
    )


AIClientDep = Annotated[AIClient, Depends(get_ai_client)]


@lru_cache
def get_token_verifier() -> TokenVerifier:
    # Cached so JWKS keys are fetched once and reused across requests.
    settings = get_settings()
    return SupabaseTokenVerifier(
        jwt_secret=settings.supabase_jwt_secret,
        jwks_url=settings.supabase_jwks_url,
        issuer=settings.supabase_issuer,
        audience=settings.supabase_jwt_audience,
    )


TokenVerifierDep = Annotated[TokenVerifier, Depends(get_token_verifier)]


@lru_cache
def _cv_tailoring_prompt() -> str:
    return load_prompt("cv_tailoring")


def get_cv_tailoring_service(ai_client: AIClientDep) -> CVTailoringService:
    return CVTailoringService(ai_client, _cv_tailoring_prompt())


ApplicationServiceDep = Annotated[ApplicationService, Depends(get_application_service)]
CVTailoringServiceDep = Annotated[CVTailoringService, Depends(get_cv_tailoring_service)]
