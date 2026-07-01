# Data Model: Application CRM

Three new tables, all children of `applications`. Every table: owner-scoped RLS
(`auth.uid() = user_id`), `application_id` FK `ON DELETE CASCADE`, `user_id` FK to `auth.users`
`ON DELETE CASCADE`, and an index on `(application_id)` (and `(user_id)` where listed).

Domain entities live in [backend/app/domain/entities.py](../../backend/app/domain/entities.py);
the SQL lives in a new `supabase/migrations/20260701xxxxxx_application_crm.sql` following
[20260701170000_init.sql](../../supabase/migrations/20260701170000_init.sql).

## application_notes (the timeline)

Unified activity + notes feed. User-authored notes and system-generated activity events share
this table, distinguished by `type`.

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid PK | `default gen_random_uuid()` |
| `application_id` | uuid | FK → `applications(id)` ON DELETE CASCADE |
| `user_id` | uuid | FK → `auth.users(id)` ON DELETE CASCADE |
| `type` | text | CHECK in (`note`, `activity`, `email`, `call`, `interview`) |
| `content` | text | NOT NULL, non-empty |
| `created_at` | timestamptz | `default now()` |
| `updated_at` | timestamptz | `default now()`, maintained by `set_updated_at` trigger |

- Domain entity: `ApplicationNote`; `type` maps to a `NoteType` enum
  ([value_objects.py](../../backend/app/domain/value_objects.py)).
- "Edited" indicator = `updated_at > created_at`.
- Auto-events: `ApplicationService.change_status` inserts a `type='activity'` row.
- Index: `(application_id, created_at desc)`.

## application_contacts

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid PK | `gen_random_uuid()` |
| `application_id` | uuid | FK → `applications(id)` ON DELETE CASCADE |
| `user_id` | uuid | FK → `auth.users(id)` ON DELETE CASCADE |
| `name` | text | NOT NULL, non-empty |
| `role` | text | nullable (e.g. "Recruiter", "Hiring Manager") |
| `email` | text | nullable; basic format validation at the schema layer |
| `phone` | text | nullable |
| `linkedin_url` | text | nullable; basic URL validation at the schema layer |
| `notes` | text | nullable |
| `created_at` | timestamptz | `default now()` |

- Domain entity: `ApplicationContact`. Index: `(application_id)`.

## application_tasks

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid PK | `gen_random_uuid()` |
| `application_id` | uuid | FK → `applications(id)` ON DELETE CASCADE |
| `user_id` | uuid | FK → `auth.users(id)` ON DELETE CASCADE |
| `title` | text | NOT NULL, non-empty |
| `is_completed` | boolean | NOT NULL `default false` |
| `due_date` | timestamptz | nullable |
| `created_at` | timestamptz | `default now()` |

- Domain entity: `ApplicationTask`. Index: `(application_id)`.

## Relationships

```
auth.users 1───* applications 1───* application_notes
                              1───* application_contacts
                              1───* application_tasks
```

Deleting an `application` cascade-deletes its notes, contacts, and tasks (SC-CRM-003). Deleting a
user cascades to applications and onward.

## RLS

For each table (`for all using (auth.uid() = user_id) with check (auth.uid() = user_id)`), plus
`alter table … enable row level security`. Backend uses the service key and additionally enforces
parent-application ownership in the service layer (see research.md §6).

## Validation (schema layer, Pydantic)

- `content` / `name` / `title`: `min_length=1`.
- `type`: constrained to `NoteType`.
- `email`: `EmailStr` (optional); `linkedin_url`: URL-shaped string (optional).
- `is_completed`: boolean; toggled via `PATCH …/tasks/{id}`.
