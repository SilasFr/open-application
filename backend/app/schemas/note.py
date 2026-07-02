"""Request/response models for the application timeline/notes API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.entities import ApplicationNote
from app.domain.value_objects import NoteType


class NoteCreate(BaseModel):
    type: NoteType = NoteType.NOTE
    content: str = Field(min_length=1)


class NoteUpdate(BaseModel):
    content: str = Field(min_length=1)


class NoteRead(BaseModel):
    id: str
    application_id: str
    type: NoteType
    content: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, note: ApplicationNote) -> NoteRead:
        return cls(
            id=note.id,
            application_id=note.application_id,
            type=note.type,
            content=note.content,
            created_at=note.created_at,
            updated_at=note.updated_at,
        )
