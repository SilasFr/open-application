"""Request/response models for the CV tailoring API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.entities import TailoredCV


class CVTailorRequest(BaseModel):
    cv_text: str = Field(min_length=1)
    job_description: str = Field(min_length=1)
    source_cv_id: str | None = None


class TailoredCVRead(BaseModel):
    id: str
    source_cv_id: str | None
    job_description: str
    content: str
    created_at: datetime

    @classmethod
    def from_entity(cls, tailored: TailoredCV) -> TailoredCVRead:
        return cls(
            id=tailored.id,
            source_cv_id=tailored.source_cv_id,
            job_description=tailored.job_description,
            content=tailored.content,
            created_at=tailored.created_at,
        )
