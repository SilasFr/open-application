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
from app.domain.repositories import (
    ApplicationRepository,
    ContactRepository,
    CVRepository,
    NoteRepository,
    TailoredCVRepository,
    TaskRepository,
)
from app.infrastructure.ai.anthropic_client import AnthropicClient
from app.infrastructure.ai.gemini_client import GeminiClient
from app.infrastructure.ai.prompts import load_prompt
from app.infrastructure.auth.supabase_verifier import SupabaseTokenVerifier
from app.infrastructure.supabase.application_repository import (
    SupabaseApplicationRepository,
)
from app.infrastructure.supabase.contact_repository import SupabaseContactRepository
from app.infrastructure.supabase.cv_repository import (
    SupabaseCVRepository,
    SupabaseTailoredCVRepository,
)
from app.infrastructure.supabase.note_repository import SupabaseNoteRepository
from app.infrastructure.supabase.task_repository import SupabaseTaskRepository
from app.services.application_service import ApplicationService
from app.services.contact_service import ContactService
from app.services.cv_service import CVService
from app.services.cv_tailoring_service import CVTailoringService
from app.services.note_service import NoteService
from app.services.task_service import TaskService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_supabase_client(settings: SettingsDep) -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)


SupabaseDep = Annotated[Client, Depends(get_supabase_client)]


def get_application_repository(client: SupabaseDep) -> ApplicationRepository:
    return SupabaseApplicationRepository(client)


ApplicationRepositoryDep = Annotated[
    ApplicationRepository, Depends(get_application_repository)
]


def get_note_repository(client: SupabaseDep) -> NoteRepository:
    return SupabaseNoteRepository(client)


NoteRepositoryDep = Annotated[NoteRepository, Depends(get_note_repository)]


def get_application_service(
    repository: ApplicationRepositoryDep, note_repository: NoteRepositoryDep
) -> ApplicationService:
    return ApplicationService(repository, note_repository)


def get_note_service(
    repository: NoteRepositoryDep, application_repository: ApplicationRepositoryDep
) -> NoteService:
    return NoteService(repository, application_repository)


NoteServiceDep = Annotated[NoteService, Depends(get_note_service)]


def get_contact_repository(client: SupabaseDep) -> ContactRepository:
    return SupabaseContactRepository(client)


ContactRepositoryDep = Annotated[ContactRepository, Depends(get_contact_repository)]


def get_contact_service(
    repository: ContactRepositoryDep, application_repository: ApplicationRepositoryDep
) -> ContactService:
    return ContactService(repository, application_repository)


ContactServiceDep = Annotated[ContactService, Depends(get_contact_service)]


def get_task_repository(client: SupabaseDep) -> TaskRepository:
    return SupabaseTaskRepository(client)


TaskRepositoryDep = Annotated[TaskRepository, Depends(get_task_repository)]


def get_task_service(
    repository: TaskRepositoryDep, application_repository: ApplicationRepositoryDep
) -> TaskService:
    return TaskService(repository, application_repository)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


def get_ai_client(settings: SettingsDep) -> AIClient:
    if settings.ai_provider == "anthropic":
        return AnthropicClient(
            api_key=settings.anthropic_api_key,
            model=settings.ai_model,
            max_tokens=settings.ai_max_tokens,
        )
    return GeminiClient(
        api_key=settings.gemini_api_key,
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


def get_cv_repository(client: SupabaseDep) -> CVRepository:
    return SupabaseCVRepository(client)


CVRepositoryDep = Annotated[CVRepository, Depends(get_cv_repository)]


def get_tailored_cv_repository(client: SupabaseDep) -> TailoredCVRepository:
    return SupabaseTailoredCVRepository(client)


TailoredCVRepositoryDep = Annotated[
    TailoredCVRepository, Depends(get_tailored_cv_repository)
]


def get_cv_service(repository: CVRepositoryDep) -> CVService:
    return CVService(repository)


CVServiceDep = Annotated[CVService, Depends(get_cv_service)]


@lru_cache
def _cv_tailoring_structured_prompt() -> str:
    return load_prompt("cv_tailoring_structured")


def get_cv_tailoring_service(
    ai_client: AIClientDep,
    cv_repository: CVRepositoryDep,
    tailored_cv_repository: TailoredCVRepositoryDep,
    application_repository: ApplicationRepositoryDep,
) -> CVTailoringService:
    return CVTailoringService(
        ai_client,
        _cv_tailoring_structured_prompt(),
        cv_repository,
        tailored_cv_repository,
        application_repository,
    )


ApplicationServiceDep = Annotated[ApplicationService, Depends(get_application_service)]
CVTailoringServiceDep = Annotated[CVTailoringService, Depends(get_cv_tailoring_service)]
