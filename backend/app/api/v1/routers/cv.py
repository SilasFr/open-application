"""CV base-resume and tailoring endpoints. Handlers stay thin: parse, call one
service, shape the response."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import Response

from app.core.dependencies import CVServiceDep, CVTailoringServiceDep
from app.core.security import get_current_user_id
from app.schemas.cv import (
    AttachTailoredCVRequest,
    BaseResumeRead,
    CVTailorRequest,
    TailoredCVRead,
)

router = APIRouter(prefix="/cv", tags=["cv"])

UserIdDep = Annotated[str, Depends(get_current_user_id)]


@router.post(
    "/base", response_model=BaseResumeRead, status_code=status.HTTP_201_CREATED
)
async def upload_base_resume(
    user_id: UserIdDep,
    service: CVServiceDep,
    file: Annotated[UploadFile, File()],
) -> BaseResumeRead:
    file_bytes = await file.read()
    cv = await service.upload(
        user_id=user_id,
        filename=file.filename or "resume",
        content_type=file.content_type or "application/octet-stream",
        file_bytes=file_bytes,
    )
    return BaseResumeRead.from_entity(cv)


@router.get("/base", response_model=BaseResumeRead)
async def get_base_resume(
    user_id: UserIdDep, service: CVServiceDep
) -> BaseResumeRead:
    cv = await service.get_current(user_id)
    return BaseResumeRead.from_entity(cv)


@router.delete("/base", status_code=status.HTTP_204_NO_CONTENT)
async def delete_base_resume(user_id: UserIdDep, service: CVServiceDep) -> None:
    await service.delete(user_id)


@router.post(
    "/tailor", response_model=TailoredCVRead, status_code=status.HTTP_201_CREATED
)
async def tailor_cv(
    payload: CVTailorRequest,
    user_id: UserIdDep,
    service: CVTailoringServiceDep,
) -> TailoredCVRead:
    tailored = await service.tailor(
        user_id=user_id,
        job_description=payload.job_description,
        refinement_instructions=payload.refinement_instructions,
        previous_tailored_cv_id=payload.previous_tailored_cv_id,
    )
    return TailoredCVRead.from_entity(tailored)


@router.get("/tailored/{tailored_id}", response_model=TailoredCVRead)
async def get_tailored_cv(
    tailored_id: str,
    user_id: UserIdDep,
    service: CVTailoringServiceDep,
) -> TailoredCVRead:
    tailored = await service.get_owned(user_id, tailored_id)
    return TailoredCVRead.from_entity(tailored)


@router.post("/tailored/{tailored_id}/attach", response_model=TailoredCVRead)
async def attach_tailored_cv(
    tailored_id: str,
    payload: AttachTailoredCVRequest,
    user_id: UserIdDep,
    service: CVTailoringServiceDep,
) -> TailoredCVRead:
    tailored = await service.attach(user_id, tailored_id, payload.application_id)
    return TailoredCVRead.from_entity(tailored)


@router.get("/tailored/{tailored_id}/download")
async def download_tailored_cv(
    tailored_id: str,
    user_id: UserIdDep,
    service: CVTailoringServiceDep,
    format: Annotated[str, Query()] = "pdf",
) -> Response:
    tailored = await service.get_owned(user_id, tailored_id)
    data, content_type, filename = await service.render(tailored, format=format)
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
