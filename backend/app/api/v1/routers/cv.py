"""CV tailoring endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import CVTailoringServiceDep
from app.core.security import get_current_user_id
from app.schemas.cv import CVTailorRequest, TailoredCVRead

router = APIRouter(prefix="/cv", tags=["cv"])

UserIdDep = Annotated[str, Depends(get_current_user_id)]


@router.post("/tailor", response_model=TailoredCVRead)
async def tailor_cv(
    payload: CVTailorRequest,
    user_id: UserIdDep,
    service: CVTailoringServiceDep,
) -> TailoredCVRead:
    tailored = await service.tailor(
        user_id=user_id,
        cv_text=payload.cv_text,
        job_description=payload.job_description,
        source_cv_id=payload.source_cv_id,
    )
    # NOTE: persistence of the tailored CV (Supabase) is a follow-up in the CV feature spec.
    return TailoredCVRead.from_entity(tailored)
