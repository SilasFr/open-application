# Quickstart: Application CRM

End-to-end validation once the feature is implemented (via `/speckit-tasks` → `/speckit-implement`).
Proves the board, timeline, contacts, and tasks work against a real Supabase project.

## Prerequisites

- `backend/.env` and `frontend/.env.local` populated (as in the current setup).
- The new migration applied to the database:
  `npx supabase db push` (or apply `supabase/migrations/20260701xxxxxx_application_crm.sql`).
- Backend: `cd backend && uv run uvicorn app.main:app --port 8000`
- Frontend: `cd frontend && npm install && npm run dev` (installs `@dnd-kit`)

## Automated checks (run first)

```bash
cd backend && uv run ruff check . && uv run mypy app && uv run pytest
cd frontend && npm run lint && npm run build
```

Expected: all green. New unit tests cover `NoteService` / `ContactService` / `TaskService`
(including parent-ownership 404 and the status-change → activity event) against in-memory fakes;
new API tests cover the nested routes and 401/404/422 paths.

## Manual end-to-end (browser at http://localhost:3000)

1. **Board (US1).** Sign in → `/tracker` shows a Kanban board with columns Saved, Applied,
   Interviewing, Offer, Closed, each with a count. Create an application → it appears in Saved.
2. **Valid drag.** Drag the card Saved → Applied. It stays after reload (status persisted).
   → validates SC-CRM-001.
3. **Invalid drag.** Drag Saved → Offer. The card snaps back and a validation error shows
   (backend returns 409 from `PATCH …/status`).
4. **Timeline (US2).** Open the card's detail panel. The status change from step 2 appears as an
   auto "Moved to Applied" activity. Add a note → it appears at the top with a timestamp; edit it
   → an "edited" marker appears; reload → note persists.
5. **Contacts (US3).** In the panel, add a contact (name + role + email) → it lists with its
   metadata; edit to add a LinkedIn URL → saves; delete → disappears.
6. **Tasks (US4).** Add a task → shows unchecked; toggle → shows completed; reload → state
   persists.
7. **Search (FR-CRM-010).** Type in the board search box → cards filter by company/role/contact.
8. **Isolation (SC-CRM-004).** With a second account, call
   `GET /api/v1/applications/{other_users_app_id}/notes` with your token → **404**.
9. **Cascade (SC-CRM-003).** Delete an application that has notes/contacts/tasks → querying its
   children returns none (DB `ON DELETE CASCADE`).

## References

- Endpoints: [contracts/](contracts/) · Schema: [data-model.md](data-model.md) ·
  Decisions: [research.md](research.md)
