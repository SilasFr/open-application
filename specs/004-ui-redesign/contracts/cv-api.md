# Contract: CV API (`/api/v1/cv`)

Extends the existing `backend/app/api/v1/routers/cv.py`. All endpoints require
`Authorization: Bearer <supabase-jwt>` and resolve `user_id` via the existing
`get_current_user_id` dependency (`backend/app/core/security.py`), matching every other
router in this project. Tracker endpoints (`applications`, `notes`, `contacts`, `tasks`)
are unchanged by this feature — not repeated here.

## Base resume

### `POST /cv/base` — upload or replace the current base resume

- **Request**: `multipart/form-data`, field `file` (PDF or DOCX, ≤5MB).
- **Behavior**: Extracts plain text (research #1); deletes any existing `cvs` row +
  Storage object for this user first (research #3), then stores the new file in the
  `cvs` bucket and inserts the new row.
- **Response 201**: `{ id, filename, created_at }`
- **Errors**: `400` unsupported file type or >5MB (FR-013); `401` no/invalid token.

### `GET /cv/base` — fetch the current base resume

- **Response 200**: `{ id, filename, created_at }`
- **Response 404**: no base resume saved yet (drives FR-014's "skip to JD step" check on
  the frontend).

### `DELETE /cv/base` — remove the current base resume

- **Response 204**. Deletes the `cvs` row and its Storage object.

## Tailoring

### `POST /cv/tailor` — generate a tailored resume

- **Request**: `{ job_description: string, refinement_instructions?: string,
  previous_tailored_cv_id?: string }`
- **Preconditions**: a base resume must exist for the user (`404` "no base resume
  saved" otherwise — Edge Cases: JD submitted with no saved base resume, redirect to
  upload step); `job_description` non-empty (FR-015); if
  `refinement_instructions` is provided it must be non-empty (Edge Cases: empty
  refinement rejected).
- **Behavior**: Loads the current base resume's parsed `content` as `source_cv_id`
  context. If `previous_tailored_cv_id` is provided, loads that row's `content` +
  `sections` as additional prompt context (research #6). Calls the AI client with the
  structured-output prompt template (research #4), validates the JSON response against
  the `sections` schema, persists a new `tailored_cvs` row.
- **Response 201**: `TailoredCVRead` —
  `{ id, source_cv_id, job_description, content, sections: [{ id, heading, body, changed, explanation }], application_id, previous_tailored_cv_id, created_at }`
- **Errors**: `400` empty job description / empty refinement instructions; `404` no base
  resume; `422` AI response failed structured-output validation (retryable by the
  client, per Edge Cases: generation failure → user can retry without losing input);
  `401` no/invalid token.

### `GET /cv/tailored/{id}` — fetch a previously generated tailored resume

- **Response 200**: `TailoredCVRead` (same shape as above).
- **Response 404**: not found or not owned by the caller.

### `POST /cv/tailored/{id}/attach` — save a tailored resume to an application

- **Request**: `{ application_id: string }`
- **Preconditions**: both the tailored resume and the application must belong to the
  calling user (FR-021; Edge Cases: empty application list handled client-side by
  disabling this action, not a server error).
- **Response 200**: `TailoredCVRead` with `application_id` set.
- **Errors**: `404` tailored resume or application not found/not owned; `401`.

### `GET /cv/tailored/{id}/download?format=pdf|docx` — download a tailored resume

- **Response 200**: binary file, `Content-Type` `application/pdf` or
  `application/vnd.openxmlformats-officedocument.wordprocessingml.document`,
  `Content-Disposition: attachment` (FR-019). Rendered from `sections` (research #2).
- **Errors**: `400` invalid `format` value; `404` not found/not owned.

## Unchanged

- Copying tailored-resume text (FR-020) is a frontend-only action against the already
  fetched `content` field — no new endpoint.
- Tracker endpoints (`applications`, `notes`, `contacts`, `tasks`) are unchanged; see
  `backend/app/api/v1/routers/{applications,notes,contacts,tasks}.py`.
