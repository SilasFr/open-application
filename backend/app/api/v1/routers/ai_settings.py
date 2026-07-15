"""BYOK AI provider settings endpoints. Handlers stay thin: parse, call one
service, shape the response."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import AISettingsServiceDep
from app.core.security import get_current_user_id
from app.schemas.ai_settings import AISettingsRead, SaveAISettingsRequest

router = APIRouter(prefix="/settings/ai", tags=["ai-settings"])

UserIdDep = Annotated[str, Depends(get_current_user_id)]


@router.get("", response_model=AISettingsRead | None)
async def get_ai_settings(
    user_id: UserIdDep, service: AISettingsServiceDep
) -> AISettingsRead | None:
    key = await service.get(user_id)
    return AISettingsRead.from_entity(key) if key is not None else None


@router.put("", response_model=AISettingsRead)
async def save_ai_settings(
    payload: SaveAISettingsRequest,
    user_id: UserIdDep,
    service: AISettingsServiceDep,
) -> AISettingsRead:
    key = await service.save(
        user_id=user_id,
        provider=payload.provider,
        api_key=payload.api_key,
        model=payload.model,
        base_url=payload.base_url,
    )
    return AISettingsRead.from_entity(key)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_settings(user_id: UserIdDep, service: AISettingsServiceDep) -> None:
    await service.delete(user_id)
