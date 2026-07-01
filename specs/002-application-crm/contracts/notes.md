# Contract: Notes / Timeline

Base: `/api/v1/applications/{application_id}/notes`. All routes require
`Authorization: Bearer <supabase access token>`. The service verifies `application_id` is owned
by the caller; otherwise **404**.

Router: `backend/app/api/v1/routers/notes.py` (thin) → `NoteService`.

## GET `/api/v1/applications/{application_id}/notes`

List the application's timeline, newest first (notes + auto-generated activity events).

- **200** → `NoteRead[]`
- **401** missing/invalid token · **404** application not found/owned

## POST `/api/v1/applications/{application_id}/notes`

Create a user note.

- Body `NoteCreate`: `{ "type": "note", "content": "string (non-empty)" }`
  (`type` ∈ note|activity|email|call|interview; default `note`)
- **201** → `NoteRead`
- **422** empty content · **404** application not found/owned · **401**

## PATCH `/api/v1/applications/{application_id}/notes/{note_id}`

Edit a note's content (sets `updated_at`).

- Body `NoteUpdate`: `{ "content": "string (non-empty)" }`
- **200** → `NoteRead` (with `updated_at > created_at` ⇒ "edited")
- **404** note or application not found/owned · **422** empty content · **401**

## DELETE `/api/v1/applications/{application_id}/notes/{note_id}`

- **204** · **404** not found/owned · **401**

## Schemas

```
NoteRead {
  id: uuid, application_id: uuid, type: string,
  content: string, created_at: datetime, updated_at: datetime
}
```

Auto-events: a status change on the parent application inserts a `type:"activity"` note server-side
(not via this API) — it appears in GET results.
