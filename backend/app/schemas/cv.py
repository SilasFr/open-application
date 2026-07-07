"""Request/response models for the CV API (base resume + tailoring)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.entities import CV, TailoredCV


class BaseResumeRead(BaseModel):
    id: str
    filename: str
    created_at: datetime

    @classmethod
    def from_entity(cls, cv: CV) -> BaseResumeRead:
        return cls(id=cv.id, filename=cv.filename, created_at=cv.created_at)


class TailoredCVSectionRead(BaseModel):
    id: str
    heading: str
    body: str
    changed: bool
    explanation: str | None = None


class CVTailorRequest(BaseModel):
    job_description: str = Field(min_length=1)
    refinement_instructions: str | None = Field(default=None, min_length=1)
    previous_tailored_cv_id: str | None = None


class TailoredCVRead(BaseModel):
    id: str
    source_cv_id: str | None
    job_description: str
    content: str
    sections: list[TailoredCVSectionRead]
    application_id: str | None
    previous_tailored_cv_id: str | None
    created_at: datetime

    @classmethod
    def from_entity(cls, tailored: TailoredCV) -> TailoredCVRead:
        return cls(
            id=tailored.id,
            source_cv_id=tailored.source_cv_id,
            job_description=tailored.job_description,
            content=tailored.content,
            sections=[
                TailoredCVSectionRead(
                    id=section.id,
                    heading=section.heading,
                    body=section.body,
                    changed=section.changed,
                    explanation=section.explanation,
                )
                for section in tailored.sections
            ],
            application_id=tailored.application_id,
            previous_tailored_cv_id=tailored.previous_tailored_cv_id,
            created_at=tailored.created_at,
        )


class AttachTailoredCVRequest(BaseModel):
    application_id: str = Field(min_length=1)
