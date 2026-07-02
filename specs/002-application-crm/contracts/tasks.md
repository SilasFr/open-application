# Contract: Tasks / Checklist

Base: `/api/v1/applications/{application_id}/tasks`. Requires
`Authorization: Bearer <token>`. Parent-application ownership enforced → **404** otherwise.

Router: `backend/app/api/v1/routers/tasks.py` (thin) → `TaskService`.

## GET `/api/v1/applications/{application_id}/tasks`

- **200** → `TaskRead[]` (creation order) · **401** · **404** application not found/owned

## POST `/api/v1/applications/{application_id}/tasks`

- Body `TaskCreate`: `{ "title": "string (non-empty)", "due_date"?: datetime }`
- **201** → `TaskRead` (starts `is_completed: false`)
- **422** empty title · **404** application not found/owned · **401**

## PATCH `/api/v1/applications/{application_id}/tasks/{task_id}`

Toggle completion and/or edit title/due date.

- Body `TaskUpdate`: `{ "is_completed"?: boolean, "title"?: string(non-empty), "due_date"?: datetime }`
- **200** → `TaskRead` · **404** not found/owned · **422** validation · **401**

## DELETE `/api/v1/applications/{application_id}/tasks/{task_id}`

- **204** · **404** not found/owned · **401**

## Schemas

```
TaskRead {
  id: uuid, application_id: uuid, title: string,
  is_completed: boolean, due_date: datetime|null, created_at: datetime
}
```
