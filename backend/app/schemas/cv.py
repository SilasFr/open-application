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


class ContactLinkRead(BaseModel):
    label: str
    url: str


class TailoredCVContactRead(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[ContactLinkRead] = Field(default_factory=list)


class TailoredCVEntryRead(BaseModel):
    title: str
    organization: str | None = None
    date_range: str | None = None
    context: str | None = None
    bullets: list[str] = Field(default_factory=list)


class TailoredCVSectionRead(BaseModel):
    id: str
    heading: str
    bullets: list[str] = Field(default_factory=list)
    entries: list[TailoredCVEntryRead] = Field(default_factory=list)


class CVTailorRequest(BaseModel):
    job_description: str = Field(min_length=1)
    refinement_instructions: str | None = Field(default=None, min_length=1)
    previous_tailored_cv_id: str | None = None


class TailoredCVRead(BaseModel):
    id: str
    source_cv_id: str | None
    job_description: str
    content: str
    contact: TailoredCVContactRead | None = None
    sections: list[TailoredCVSectionRead]
    application_id: str | None
    previous_tailored_cv_id: str | None
    created_at: datetime

    @classmethod
    def from_entity(cls, tailored: TailoredCV) -> TailoredCVRead:
        contact = tailored.contact
        return cls(
            id=tailored.id,
            source_cv_id=tailored.source_cv_id,
            job_description=tailored.job_description,
            content=tailored.content,
            contact=(
                TailoredCVContactRead(
                    name=contact.name,
                    email=contact.email,
                    phone=contact.phone,
                    location=contact.location,
                    links=[
                        ContactLinkRead(label=link.label, url=link.url)
                        for link in contact.links
                    ],
                )
                if contact is not None
                else None
            ),
            sections=[
                TailoredCVSectionRead(
                    id=section.id,
                    heading=section.heading,
                    bullets=list(section.bullets),
                    entries=[
                        TailoredCVEntryRead(
                            title=entry.title,
                            organization=entry.organization,
                            date_range=entry.date_range,
                            context=entry.context,
                            bullets=list(entry.bullets),
                        )
                        for entry in section.entries
                    ],
                )
                for section in tailored.sections
            ],
            application_id=tailored.application_id,
            previous_tailored_cv_id=tailored.previous_tailored_cv_id,
            created_at=tailored.created_at,
        )


class AttachTailoredCVRequest(BaseModel):
    application_id: str = Field(min_length=1)
