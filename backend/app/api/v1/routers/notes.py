"""Application timeline/notes endpoints. Handlers stay thin: parse, call one service, shape."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import NoteServiceDep
from app.core.security import get_current_user_id
from app.schemas.note import NoteCreate, NoteRead, NoteUpdate

router = APIRouter(prefix="/applications/{application_id}/notes", tags=["notes"])

UserIdDep = Annotated[str, Depends(get_current_user_id)]


@router.get("", response_model=list[NoteRead])
async def list_notes(
    application_id: str,
    user_id: UserIdDep,
    service: NoteServiceDep,
) -> list[NoteRead]:
    notes = await service.list(user_id, application_id)
    return [NoteRead.from_entity(note) for note in notes]


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(
    application_id: str,
    payload: NoteCreate,
    user_id: UserIdDep,
    service: NoteServiceDep,
) -> NoteRead:
    note = await service.create(
        user_id=user_id,
        application_id=application_id,
        type=payload.type,
        content=payload.content,
    )
    return NoteRead.from_entity(note)


@router.patch("/{note_id}", response_model=NoteRead)
async def update_note(
    application_id: str,
    note_id: str,
    payload: NoteUpdate,
    user_id: UserIdDep,
    service: NoteServiceDep,
) -> NoteRead:
    note = await service.update(user_id, application_id, note_id, payload.content)
    return NoteRead.from_entity(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    application_id: str,
    note_id: str,
    user_id: UserIdDep,
    service: NoteServiceDep,
) -> None:
    await service.delete(user_id, application_id, note_id)
