"""FastAPI application factory and composition of routers + error handling."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routers import applications, contacts, cv, health, notes, tasks
from app.core.config import get_settings
from app.domain.exceptions import (
    AIGenerationError,
    AuthenticationError,
    DomainError,
    InvalidAIResponseError,
    InvalidStatusTransition,
    NotFoundError,
)

_API_V1_PREFIX = "/api/v1"


def _register_exception_handlers(app: FastAPI) -> None:
    """Map domain errors to HTTP responses so handlers never do it themselves."""

    def _body(exc: DomainError) -> dict[str, str]:
        # Every error carries both a human-readable ``detail`` and a stable,
        # machine-readable ``code`` (see DomainError.code) so clients branch on
        # the code, never on the message text.
        return {"detail": str(exc), "code": exc.code}

    @app.exception_handler(AuthenticationError)
    async def _handle_auth_error(_: Request, exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content=_body(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(NotFoundError)
    async def _handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content=_body(exc))

    @app.exception_handler(InvalidStatusTransition)
    async def _handle_invalid_transition(
        _: Request, exc: InvalidStatusTransition
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content=_body(exc))

    @app.exception_handler(InvalidAIResponseError)
    async def _handle_invalid_ai_response(
        _: Request, exc: InvalidAIResponseError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content=_body(exc))

    @app.exception_handler(AIGenerationError)
    async def _handle_ai_generation_error(
        _: Request, exc: AIGenerationError
    ) -> JSONResponse:
        return JSONResponse(status_code=502, content=_body(exc))

    @app.exception_handler(DomainError)
    async def _handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=400, content=_body(exc))


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(applications.router, prefix=_API_V1_PREFIX)
    app.include_router(notes.router, prefix=_API_V1_PREFIX)
    app.include_router(contacts.router, prefix=_API_V1_PREFIX)
    app.include_router(tasks.router, prefix=_API_V1_PREFIX)
    app.include_router(cv.router, prefix=_API_V1_PREFIX)

    _register_exception_handlers(app)
    return app


app = create_app()
