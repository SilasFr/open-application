"""Application contacts endpoints. Handlers stay thin: parse, call one service, shape."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import ContactServiceDep
from app.core.security import get_current_user_id
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate

router = APIRouter(prefix="/applications/{application_id}/contacts", tags=["contacts"])

UserIdDep = Annotated[str, Depends(get_current_user_id)]


@router.get("", response_model=list[ContactRead])
async def list_contacts(
    application_id: str,
    user_id: UserIdDep,
    service: ContactServiceDep,
) -> list[ContactRead]:
    contacts = await service.list(user_id, application_id)
    return [ContactRead.from_entity(contact) for contact in contacts]


@router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def create_contact(
    application_id: str,
    payload: ContactCreate,
    user_id: UserIdDep,
    service: ContactServiceDep,
) -> ContactRead:
    contact = await service.create(
        user_id=user_id,
        application_id=application_id,
        name=payload.name,
        role=payload.role,
        email=payload.email,
        phone=payload.phone,
        linkedin_url=str(payload.linkedin_url) if payload.linkedin_url else None,
        notes=payload.notes,
    )
    return ContactRead.from_entity(contact)


@router.patch("/{contact_id}", response_model=ContactRead)
async def update_contact(
    application_id: str,
    contact_id: str,
    payload: ContactUpdate,
    user_id: UserIdDep,
    service: ContactServiceDep,
) -> ContactRead:
    contact = await service.update(
        user_id,
        application_id,
        contact_id,
        name=payload.name,
        role=payload.role,
        email=payload.email,
        phone=payload.phone,
        linkedin_url=str(payload.linkedin_url) if payload.linkedin_url else None,
        notes=payload.notes,
    )
    return ContactRead.from_entity(contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    application_id: str,
    contact_id: str,
    user_id: UserIdDep,
    service: ContactServiceDep,
) -> None:
    await service.delete(user_id, application_id, contact_id)
