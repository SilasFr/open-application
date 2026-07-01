"""Request/response models for the application tracker API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.entities import Application
from app.domain.value_objects import ApplicationStatus


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    job_description: str | None = None


class StatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationRead(BaseModel):
    id: str
    company: str
    role: str
    status: ApplicationStatus
    job_description: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, application: Application) -> ApplicationRead:
        return cls(
            id=application.id,
            company=application.company,
            role=application.role,
            status=application.status,
            job_description=application.job_description,
            created_at=application.created_at,
            updated_at=application.updated_at,
        )
