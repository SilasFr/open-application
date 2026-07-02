"""Application checklist/tasks endpoints. Handlers stay thin: parse, call one service, shape."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import TaskServiceDep
from app.core.security import get_current_user_id
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/applications/{application_id}/tasks", tags=["tasks"])

UserIdDep = Annotated[str, Depends(get_current_user_id)]


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    application_id: str,
    user_id: UserIdDep,
    service: TaskServiceDep,
) -> list[TaskRead]:
    tasks = await service.list(user_id, application_id)
    return [TaskRead.from_entity(task) for task in tasks]


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    application_id: str,
    payload: TaskCreate,
    user_id: UserIdDep,
    service: TaskServiceDep,
) -> TaskRead:
    task = await service.create(
        user_id=user_id,
        application_id=application_id,
        title=payload.title,
        due_date=payload.due_date,
    )
    return TaskRead.from_entity(task)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    application_id: str,
    task_id: str,
    payload: TaskUpdate,
    user_id: UserIdDep,
    service: TaskServiceDep,
) -> TaskRead:
    task = await service.update(
        user_id,
        application_id,
        task_id,
        title=payload.title,
        is_completed=payload.is_completed,
        due_date=payload.due_date,
    )
    return TaskRead.from_entity(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    application_id: str,
    task_id: str,
    user_id: UserIdDep,
    service: TaskServiceDep,
) -> None:
    await service.delete(user_id, application_id, task_id)
