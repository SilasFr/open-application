"""Application tracker endpoints. Handlers stay thin: parse, call one service, shape."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import ApplicationServiceDep
from app.core.security import get_current_user_id
from app.schemas.application import ApplicationCreate, ApplicationRead, StatusUpdate

router = APIRouter(prefix="/applications", tags=["applications"])

UserIdDep = Annotated[str, Depends(get_current_user_id)]


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate,
    user_id: UserIdDep,
    service: ApplicationServiceDep,
) -> ApplicationRead:
    application = await service.create(
        user_id=user_id,
        company=payload.company,
        role=payload.role,
        job_description=payload.job_description,
    )
    return ApplicationRead.from_entity(application)


@router.get("", response_model=list[ApplicationRead])
async def list_applications(
    user_id: UserIdDep,
    service: ApplicationServiceDep,
) -> list[ApplicationRead]:
    applications = await service.list(user_id)
    return [ApplicationRead.from_entity(app) for app in applications]


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(
    application_id: str,
    user_id: UserIdDep,
    service: ApplicationServiceDep,
) -> ApplicationRead:
    application = await service.get(user_id, application_id)
    return ApplicationRead.from_entity(application)


@router.patch("/{application_id}/status", response_model=ApplicationRead)
async def change_application_status(
    application_id: str,
    payload: StatusUpdate,
    user_id: UserIdDep,
    service: ApplicationServiceDep,
) -> ApplicationRead:
    application = await service.change_status(user_id, application_id, payload.status)
    return ApplicationRead.from_entity(application)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: str,
    user_id: UserIdDep,
    service: ApplicationServiceDep,
) -> None:
    await service.delete(user_id, application_id)
