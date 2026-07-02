"""Business logic for an application's associated contacts."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.domain.entities import ApplicationContact
from app.domain.exceptions import NotFoundError
from app.domain.repositories import ApplicationRepository, ContactRepository


class ContactService:
    """Use-cases for an application's contacts (recruiters, hiring managers, referrers).

    Depends only on the :class:`ContactRepository` and :class:`ApplicationRepository`
    interfaces — the latter is used solely to assert that the caller owns the
    parent application before touching its contacts.
    """

    def __init__(
        self,
        repository: ContactRepository,
        application_repository: ApplicationRepository,
    ) -> None:
        self._repository = repository
        self._application_repository = application_repository

    async def _assert_application_owned(self, user_id: str, application_id: str) -> None:
        application = await self._application_repository.get(user_id, application_id)
        if application is None:
            raise NotFoundError(f"Application {application_id} not found")

    async def list(
        self, user_id: str, application_id: str
    ) -> list[ApplicationContact]:
        await self._assert_application_owned(user_id, application_id)
        return await self._repository.list_for_application(user_id, application_id)

    async def create(
        self,
        *,
        user_id: str,
        application_id: str,
        name: str,
        role: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        linkedin_url: str | None = None,
        notes: str | None = None,
    ) -> ApplicationContact:
        await self._assert_application_owned(user_id, application_id)
        contact = ApplicationContact(
            id=str(uuid4()),
            application_id=application_id,
            user_id=user_id,
            name=name,
            role=role,
            email=email,
            phone=phone,
            linkedin_url=linkedin_url,
            notes=notes,
            created_at=datetime.now(UTC),
        )
        return await self._repository.add(contact)

    async def _get_owned(
        self, user_id: str, application_id: str, contact_id: str
    ) -> ApplicationContact:
        await self._assert_application_owned(user_id, application_id)
        contact = await self._repository.get(user_id, contact_id)
        if contact is None or contact.application_id != application_id:
            raise NotFoundError(f"Contact {contact_id} not found")
        return contact

    async def update(
        self,
        user_id: str,
        application_id: str,
        contact_id: str,
        *,
        name: str | None = None,
        role: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        linkedin_url: str | None = None,
        notes: str | None = None,
    ) -> ApplicationContact:
        contact = await self._get_owned(user_id, application_id, contact_id)
        if name is not None:
            contact.name = name
        if role is not None:
            contact.role = role
        if email is not None:
            contact.email = email
        if phone is not None:
            contact.phone = phone
        if linkedin_url is not None:
            contact.linkedin_url = linkedin_url
        if notes is not None:
            contact.notes = notes
        return await self._repository.update(contact)

    async def delete(self, user_id: str, application_id: str, contact_id: str) -> None:
        await self._get_owned(user_id, application_id, contact_id)
        await self._repository.delete(user_id, contact_id)
