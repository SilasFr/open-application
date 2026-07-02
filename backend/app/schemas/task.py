"""Request/response models for the application tasks/checklist API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.entities import ApplicationTask


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    is_completed: bool | None = None
    due_date: datetime | None = None


class TaskRead(BaseModel):
    id: str
    application_id: str
    title: str
    is_completed: bool
    due_date: datetime | None
    created_at: datetime

    @classmethod
    def from_entity(cls, task: ApplicationTask) -> TaskRead:
        return cls(
            id=task.id,
            application_id=task.application_id,
            title=task.title,
            is_completed=task.is_completed,
            due_date=task.due_date,
            created_at=task.created_at,
        )
