# Phase 1 Data Model: UI Redesign — Tracker & Tailor CV

Source of truth for shape: `backend/app/domain/entities.py`, `backend/app/domain/value_objects.py`,
and `supabase/migrations/`. Entries marked **(existing, unchanged)** require no schema or
entity changes; entries marked **(extended)** need a new additive migration.

## Application (existing, unchanged)

Table `public.applications`. Entity `backend/app/domain/entities.py:11-22`.

| Field | Type | Notes |
|---|---|---|
| id | uuid | primary key |
| user_id | uuid | FK `auth.users`, RLS-scoped |
| company | text | required |
| role | text | required |
| status | `ApplicationStatus` enum | saved / applied / interviewing / offer / accepted / rejected / withdrawn |
| job_description | text? | optional |
| created_at | timestamptz | used for date-filter (FR-002) and add-application timestamp (FR-009) |
| updated_at | timestamptz | serves as "last activity" — used for staleness (FR-008) and updated on every status change (FR-007) |

**State transitions** — `_ALLOWED_TRANSITIONS` in `value_objects.py:22-51`, enforced by
`ApplicationService.change_status` (`application_service.py:58-71`), unchanged by this
feature (FR-004):

```
saved        → applied, withdrawn
applied      → interviewing, rejected, withdrawn
interviewing → offer, rejected, withdrawn
offer        → accepted, rejected, withdrawn
accepted / rejected / withdrawn → (terminal)
```

**Derived (not stored)**:
- *Stale* = status ∈ {saved, applied, interviewing, offer} AND `now() - updated_at ≥ 7 days` (FR-008).
- *Response rate* = round((interviewing + offer + accepted) / (total − saved) × 100), or
  0% when the denominator is 0 (User Story 1 AC3).
- *Closed column* (frontend grouping only) = accepted ∪ rejected ∪ withdrawn (FR-003).

## ApplicationNote / ApplicationContact / ApplicationTask (existing, unchanged)

Tables `application_notes`, `application_contacts`, `application_tasks`
(`supabase/migrations/20260701180000_application_crm.sql`). Entities
`backend/app/domain/entities.py:26-64`. No changes — reused as-is for the detail panel
(FR-010).

## CV — Base Resume (existing table, new application-layer invariant)

Table `public.cvs` (`supabase/migrations/20260701170000_init.sql:44-52`). Entity
`backend/app/domain/entities.py:67-75`.

| Field | Type | Notes |
|---|---|---|
| id | uuid | primary key |
| user_id | uuid | FK `auth.users`, RLS-scoped |
| filename | text | original upload filename |
| storage_path | text | path in the `cvs` Storage bucket, `<user_id>/<filename>` |
| content | text? | extracted plain text (via `pypdf`/`python-docx`, research #1) |
| created_at | timestamptz | |

**New invariant (application layer, not schema)**: at most one `cvs` row exists per
`user_id` at a time. Replacing deletes the previous row + Storage object before
inserting the new one (research #3). No migration needed for this table.

**Validation**: file type ∈ {`application/pdf`, DOCX mimetype}, size ≤ 5MB (FR-013).

## TailoredCV (existing table, extended)

Table `public.tailored_cvs` (`supabase/migrations/20260701170000_init.sql:57-65`).
Entity `backend/app/domain/entities.py:78-87`.

**New migration** `supabase/migrations/<timestamp>_tailored_cv_structured_output.sql`
adds:

| New field | Type | Notes |
|---|---|---|
| sections | jsonb | `[{ id, heading, body, changed: bool, explanation: str \| null }]` (research #4) |
| application_id | uuid, nullable | FK `applications(id) on delete set null`; set via "save to application" (FR-021, research #5) |
| refinement_instructions | text, nullable | present only on refinement-generated rows |
| previous_tailored_cv_id | uuid, nullable | FK `tailored_cvs(id) on delete set null`; links a refinement to what it refined (research #6) |

Existing columns unchanged: `id`, `user_id`, `source_cv_id` (→ `cvs.id`),
`job_description`, `content` (full rendered plain text, kept for copy/download —
research #4), `created_at`.

**Validation**:
- `sections` MUST be a non-empty list; every section with `changed: true` MUST have a
  non-null `explanation` (FR-017).
- `refinement_instructions`, when a refinement request is submitted, MUST be non-empty
  (Edge Cases: empty refinement instructions rejected).

**RLS**: inherits the existing `own tailored_cvs` policy
(`auth.uid() = user_id`) — no policy change needed since `user_id` is unchanged and
still the scoping column; the new `application_id` FK does not widen access (a user can
only set it to an application they already own, enforced by the service layer resolving
both rows under the same `user_id`).

## Relationships

```
Application (1) ── (0..1) TailoredCV.application_id   [a tailored CV may be attached to one application]
CV (1) ── (0..n) TailoredCV.source_cv_id               [a base resume may back many tailoring runs]
TailoredCV (1) ── (0..n) TailoredCV.previous_tailored_cv_id  [a refinement chain]
Application (1) ── (0..n) ApplicationNote / ApplicationContact / ApplicationTask  [existing]
```

## Out of scope for this data model

- No versioning/history table for base resumes (research #3).
- No many-to-many join table between `TailoredCV` and `Application` (research #5).
- No new table for "tailoring session" state — the wizard's `phase` (resume / jd /
  working / result) is frontend-only UI state, not persisted domain data.
