"""Request/response models for the application contacts API."""

from __future__ import annotations

from datetime import datetime

from pydantic import AnyUrl, BaseModel, EmailStr, Field

from app.domain.entities import ApplicationContact


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    role: str | None = Field(default=None, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    linkedin_url: AnyUrl | None = None
    notes: str | None = None


class ContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    role: str | None = Field(default=None, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    linkedin_url: AnyUrl | None = None
    notes: str | None = None


class ContactRead(BaseModel):
    id: str
    application_id: str
    name: str
    role: str | None
    email: str | None
    phone: str | None
    linkedin_url: str | None
    notes: str | None
    created_at: datetime

    @classmethod
    def from_entity(cls, contact: ApplicationContact) -> ContactRead:
        return cls(
            id=contact.id,
            application_id=contact.application_id,
            name=contact.name,
            role=contact.role,
            email=contact.email,
            phone=contact.phone,
            linkedin_url=contact.linkedin_url,
            notes=contact.notes,
            created_at=contact.created_at,
        )
