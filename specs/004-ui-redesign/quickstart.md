# Quickstart: Validating the UI Redesign

Manual end-to-end validation guide, one section per user story in `spec.md`. Run the
automated gates first, then walk the scenarios in a browser against a real Supabase
project (test/staging, not production data).

## Prerequisites

- Supabase project with migrations applied, including the new
  `<timestamp>_tailored_cv_structured_output.sql` from `data-model.md`
  (`supabase db push` or the project's usual migration command).
- A test user account with credentials for sign-in.
- Backend `.env` configured per `backend/.env.example` (Supabase URL/keys, Anthropic
  API key).

## Run the automated gates

```sh
# Backend
cd backend
uv run ruff check .
uv run mypy app
uv run pytest

# Frontend
cd ../frontend
npm run lint
npm run build
npx vitest run   # if introduced per research.md #7
```

All must pass before manual validation.

## Start the app

```sh
cd backend && uv run uvicorn app.main:app --reload
cd frontend && npm run dev
```

## Tracker: pipeline health (User Story 1)

1. Sign in as the test user with a mix of seeded applications across all statuses,
   including at least one active application with no activity for 7+ days.
2. Open `/tracker`. **Expect**: summary strip shows Active / Interviewing / Offers /
   Response rate / Need attention within ~3 seconds, and the stale application is
   visually flagged.
3. Seed a user with zero applications in a separate account. **Expect**: summary shows
   all-zero state, columns show "Nothing here yet."

## Tracker: filters (User Story 2)

1. With 10+ seeded applications across companies/dates, type a partial company name
   into search. **Expect**: only matching cards remain.
2. Set the status filter to a single status. **Expect**: only that status's cards
   remain.
3. Set the date filter to "last 7 days". **Expect**: only recently created applications
   remain. Combine all three filters and confirm the intersection is correct.

## Tracker: guarded transitions (User Story 3)

1. Drag an "applied" card onto "interviewing". **Expect**: move succeeds,
   `updated_at`/relative-time meta updates.
2. Attempt to drag a "saved" card onto "offer" (or the Closed group). **Expect**: move
   is rejected with an inline explanation; status unchanged after reload.
3. Start a drag and hover over an illegal column. **Expect**: illegal columns dim,
   legal columns highlight.
4. Open the detail panel for an application in each status. **Expect**: only legal
   one-tap transitions are offered.
5. Using only a keyboard (no mouse), confirm a status change is achievable via the
   detail panel's one-tap buttons and that modals/panels trap focus and close on
   Escape (FR-011a, WCAG check).

## Tracker: detail panel & add application (User Stories 4–5)

1. Open an application, add a note, add a task, mark it complete. **Expect**: timeline
   shows newest-first, open-task count updates.
2. Trigger "Add application" with empty fields. **Expect**: submit stays disabled until
   company + role are filled. Submit valid values. **Expect**: new card appears in the
   chosen column with current timestamps.

## Tailor CV: guided flow (User Story 6)

1. As a user with no base resume, visit `/tailor`. **Expect**: prompted to upload a
   PDF/DOCX resume; uploading a >5MB or unsupported file is rejected with a clear
   message (`POST /cv/base` from `contracts/cv-api.md`).
2. Upload a valid resume, then reload the page (simulating a new session).
   **Expect**: lands directly on the job-description step (`GET /cv/base` returns
   200).
3. Submit a job description. **Expect**: progress narrative shown, then a result with
   changed sections visually marked and each paired with an explanation
   (`POST /cv/tailor`).
4. Click a changed section, then its paired explanation card. **Expect**: both
   highlight together; clicking again clears it.
5. Replace the base resume from the result view. **Expect**: old file/row replaced
   (`POST /cv/base` again), not duplicated.

## Tailor CV: result actions (User Story 7)

1. Download as PDF, then as DOCX. **Expect**: both open correctly and reflect the
   tailored content (`GET /cv/tailored/{id}/download`).
2. Copy the result. **Expect**: clipboard contains plain text; button confirms for
   ~1.5s.
3. Save to an application from the picker. **Expect**: confirmation names the chosen
   application (`POST /cv/tailored/{id}/attach`); with zero applications seeded,
   **expect** the action clearly communicates there's nothing to attach to yet.
4. Submit a refinement with instructions. **Expect**: new result generated
   incorporating them; submitting empty instructions is blocked client-side.
5. Choose "start over". **Expect**: returns to the job-description step with the base
   resume retained and the previous job description cleared.

## Cross-cutting

- Resize the browser to a mobile width on both pages. **Expect**: no overlapping or
  clipped content, all controls remain reachable (clarified "doesn't break" bar — not a
  dedicated mobile layout).
- Force a network failure during a drag-and-drop move (e.g., devtools offline mode).
  **Expect**: the card reverts to its original column and an error is shown.
