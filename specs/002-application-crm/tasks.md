---
description: "Task list for Application CRM"
---

# Tasks: Application CRM

**Input**: Design documents from `/specs/002-application-crm/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/)

**Tests**: INCLUDED — the project [constitution](../../.specify/memory/constitution.md) requires
every service to have `pytest` unit tests against in-memory fakes, plus API tests. (Frontend has
no unit-test harness; it's validated by `lint` + `build` + the quickstart.)

**Organization**: Grouped by user story. US1 is a frontend-only MVP that reuses the existing
status endpoint; US2–US4 each add a backend vertical slice mirroring the Application slice.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- Paths: backend `backend/app/...`, `backend/tests/...`; frontend `frontend/src/...`

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 [P] Add `@dnd-kit/core` and `@dnd-kit/sortable` to `frontend/package.json` (`npm install`)
- [ ] T002 [P] Add `email-validator` (via `pydantic[email]`) to `backend/pyproject.toml` and `uv sync` (needed for `EmailStr`)

---

## Phase 2: Foundational (Blocking Prerequisites for US2–US4)

**Purpose**: The database groundwork the CRM data stories depend on. **US1 does not depend on this phase.**

- [ ] T003 Create migration `backend/../supabase/migrations/20260701T000000_application_crm.sql` — tables `application_notes`, `application_contacts`, `application_tasks` with RLS (`auth.uid() = user_id`), FKs `ON DELETE CASCADE` to `applications`/`auth.users`, indexes, and a `set_updated_at` trigger on `application_notes` (mirror `supabase/migrations/20260701170000_init.sql`)

**Checkpoint**: Schema defined. Apply it (T054) before manual testing of US2–US4.

---

## Phase 3: User Story 1 — Visual Kanban Pipeline Board (Priority: P1) 🎯 MVP

**Goal**: Replace the flat `/tracker` list with a Kanban board; dragging a card changes status
(validated), columns show counts, and a search box filters cards.

**Independent Test**: Sign in → `/tracker` shows columns Saved/Applied/Interviewing/Offer/Closed
with counts; drag Saved→Applied persists after reload; drag Saved→Offer reverts with an error.

**Note**: Frontend-only — reuses the existing `PATCH /api/v1/applications/{id}/status` and
`api.changeStatus` in `frontend/src/lib/api.ts`. No backend changes.

- [ ] T004 [P] [US1] Create `ApplicationCard` component in `frontend/src/components/ApplicationCard.tsx` (draggable via @dnd-kit; shows company/role/status)
- [ ] T005 [P] [US1] Add board↔status column mapping helper (Closed collapses accepted/rejected/withdrawn) in `frontend/src/lib/board.ts`
- [ ] T006 [US1] Create `KanbanBoard` component in `frontend/src/components/KanbanBoard.tsx` (5 columns via @dnd-kit `DndContext`, per-column counts) — depends on T004, T005
- [ ] T007 [US1] Handle drag-end in `KanbanBoard.tsx`: optimistic move → `api.changeStatus`; on 409 revert card and surface the validation error
- [ ] T008 [P] [US1] Create `SearchBar` component + client-side filter (company/role/contact) in `frontend/src/components/SearchBar.tsx`
- [ ] T009 [US1] Replace the flat list in `frontend/src/app/tracker/page.tsx` with `KanbanBoard` + `SearchBar`
- [ ] T010 [US1] Verify `cd frontend && npm run lint && npm run build` pass

**Checkpoint**: US1 is a fully functional MVP — demoable on its own.

---

## Phase 4: User Story 2 — Detail Panel & Activity Timeline (Priority: P2)

**Goal**: Click a card to open a slide-over panel with a reverse-chronological timeline of notes
and auto-generated activity events; add/edit/delete notes.

**Independent Test**: Open a card → status change from US1 shows as a "Moved to …" activity; add a
note (appears with timestamp), edit it ("edited" marker), reload → persists.

### Domain & test scaffolding

- [ ] T011 [P] [US2] Add `ApplicationNote` entity in `backend/app/domain/entities.py`
- [ ] T012 [P] [US2] Add `NoteType` enum (note/activity/email/call/interview) in `backend/app/domain/value_objects.py`
- [ ] T013 [US2] Add `NoteRepository` ABC in `backend/app/domain/repositories.py`
- [ ] T014 [US2] Add `InMemoryNoteRepository` fake in `backend/tests/fakes.py`

### Tests (write before implementation)

- [ ] T015 [P] [US2] Unit tests for `NoteService` (create/list newest-first/edit/delete + parent-ownership 404) in `backend/tests/unit/test_note_service.py`
- [ ] T016 [P] [US2] Unit test: `ApplicationService.change_status` appends an `activity` note in `backend/tests/unit/test_application_service.py`
- [ ] T017 [P] [US2] API tests for notes routes (201/200/204/401/404/422) in `backend/tests/integration/test_notes_api.py`

### Implementation

- [ ] T018 [US2] `SupabaseNoteRepository` in `backend/app/infrastructure/supabase/note_repository.py` (anyio.to_thread wrapper, per `application_repository.py`)
- [ ] T019 [US2] `NoteService` in `backend/app/services/note_service.py` (injects `NoteRepository` + `ApplicationRepository` for ownership)
- [ ] T020 [US2] Modify `ApplicationService.change_status` to append an activity note; add the `NoteRepository` constructor dependency in `backend/app/services/application_service.py`
- [ ] T021 [P] [US2] Note DTOs (`NoteCreate`/`NoteUpdate`/`NoteRead`) in `backend/app/schemas/note.py`
- [ ] T022 [US2] `notes` router in `backend/app/api/v1/routers/notes.py` and register it in `backend/app/main.py`
- [ ] T023 [US2] Wire `NoteRepository`/`NoteService` and the new `ApplicationService` dependency in `backend/app/core/dependencies.py`; update overrides in `backend/tests/integration/conftest.py`

### Frontend

- [ ] T024 [P] [US2] Add `ApplicationNote` type + note API methods (list/create/update/delete) in `frontend/src/lib/api.ts`
- [ ] T025 [US2] `ApplicationDetailPanel` slide-over shell in `frontend/src/components/ApplicationDetailPanel.tsx`
- [ ] T026 [US2] `NotesTimeline` component (reverse-chronological, add/edit/delete, "edited" marker) in `frontend/src/components/NotesTimeline.tsx`
- [ ] T027 [US2] Open the panel on card click (from `ApplicationCard`/`KanbanBoard`) and render `NotesTimeline`

**Checkpoint**: US1 + US2 both work independently.

---

## Phase 5: User Story 3 — Associated Contacts (Priority: P2)

**Goal**: Add/edit/delete contact profiles (name, role, email, phone, LinkedIn, notes) inside an
application's detail panel.

**Independent Test**: Open panel → add a contact (name/role/email) → lists with metadata; edit to
add LinkedIn → saves; delete → disappears; reload → persists.

- [ ] T028 [P] [US3] Add `ApplicationContact` entity in `backend/app/domain/entities.py`
- [ ] T029 [US3] Add `ContactRepository` ABC in `backend/app/domain/repositories.py`
- [ ] T030 [US3] Add `InMemoryContactRepository` fake in `backend/tests/fakes.py`
- [ ] T031 [P] [US3] Unit tests for `ContactService` (CRUD + parent-ownership 404) in `backend/tests/unit/test_contact_service.py`
- [ ] T032 [P] [US3] API tests for contacts routes (incl. 422 on bad email/url) in `backend/tests/integration/test_contacts_api.py`
- [ ] T033 [US3] `SupabaseContactRepository` in `backend/app/infrastructure/supabase/contact_repository.py`
- [ ] T034 [US3] `ContactService` in `backend/app/services/contact_service.py`
- [ ] T035 [P] [US3] Contact DTOs with `EmailStr`/URL validation in `backend/app/schemas/contact.py`
- [ ] T036 [US3] `contacts` router in `backend/app/api/v1/routers/contacts.py` and register in `backend/app/main.py`
- [ ] T037 [US3] Wire `ContactRepository`/`ContactService` in `backend/app/core/dependencies.py`; update `backend/tests/integration/conftest.py`
- [ ] T038 [P] [US3] Add contact type + API methods in `frontend/src/lib/api.ts`
- [ ] T039 [US3] `ContactsSection` component in `frontend/src/components/ContactsSection.tsx` and render it in `ApplicationDetailPanel`

**Checkpoint**: US1 + US2 + US3 all work independently.

---

## Phase 6: User Story 4 — Application Tasks & Checklist (Priority: P3)

**Goal**: Add checklist tasks to an application and toggle their completion.

**Independent Test**: Open panel → add task (unchecked) → toggle (completed) → reload → state
persists.

- [ ] T040 [P] [US4] Add `ApplicationTask` entity in `backend/app/domain/entities.py`
- [ ] T041 [US4] Add `TaskRepository` ABC in `backend/app/domain/repositories.py`
- [ ] T042 [US4] Add `InMemoryTaskRepository` fake in `backend/tests/fakes.py`
- [ ] T043 [P] [US4] Unit tests for `TaskService` (CRUD + toggle completion + parent-ownership 404) in `backend/tests/unit/test_task_service.py`
- [ ] T044 [P] [US4] API tests for tasks routes in `backend/tests/integration/test_tasks_api.py`
- [ ] T045 [US4] `SupabaseTaskRepository` in `backend/app/infrastructure/supabase/task_repository.py`
- [ ] T046 [US4] `TaskService` in `backend/app/services/task_service.py`
- [ ] T047 [P] [US4] Task DTOs (`TaskCreate`/`TaskUpdate`/`TaskRead`) in `backend/app/schemas/task.py`
- [ ] T048 [US4] `tasks` router (incl. `PATCH …/tasks/{id}` toggle) in `backend/app/api/v1/routers/tasks.py` and register in `backend/app/main.py`
- [ ] T049 [US4] Wire `TaskRepository`/`TaskService` in `backend/app/core/dependencies.py`; update `backend/tests/integration/conftest.py`
- [ ] T050 [P] [US4] Add task type + API methods in `frontend/src/lib/api.ts`
- [ ] T051 [US4] `TasksSection` component (add/toggle/delete) in `frontend/src/components/TasksSection.tsx` and render it in `ApplicationDetailPanel`

**Checkpoint**: All four user stories work independently.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T052 [P] Run backend gates: `cd backend && uv run ruff check . && uv run mypy app && uv run pytest` (all green)
- [ ] T053 [P] Run frontend gates: `cd frontend && npm run lint && npm run build`
- [ ] T054 Apply the migration to the database (`npx supabase db push`) and verify tables, RLS, and cascade delete
- [ ] T055 Make the board responsive on mobile (column horizontal-scroll/collapse) in `frontend/src/components/KanbanBoard.tsx`
- [ ] T056 Execute [quickstart.md](quickstart.md) end-to-end (US1–US4 + isolation + cascade checks)

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (P1)**: T001 (frontend) and T002 (backend) — independent, run in parallel.
- **Foundational (P2)**: T003 migration — blocks US2/US3/US4 testing (via T054), **not US1**.
- **US1 (P3)**: depends only on Setup T001. Ships as MVP.
- **US2/US3/US4**: each depends on Setup + the migration (T003). Independently testable via fakes
  without the DB applied.
- **Polish (P7)**: after the desired stories are done.

### Cross-story serialization points (shared files)

These files are edited by multiple stories, so those specific tasks can't run in parallel across
stories (append in story order): `backend/app/domain/entities.py` (T011, T028, T040),
`repositories.py` (T013, T029, T041), `backend/tests/fakes.py` (T014, T030, T042),
`core/dependencies.py` (T023, T037, T049), `backend/app/main.py` (T022, T036, T048),
`tests/integration/conftest.py` (T023, T037, T049), `frontend/src/lib/api.ts` (T024, T038, T050),
`ApplicationDetailPanel.tsx` (created T025, edited T039, T051).

### Within each story

Entity/enum → repository ABC → fake → tests → repository impl/service → schemas → router+DI →
frontend. Tests are expected to fail until the service/router exist.

---

## Parallel Example: User Story 2 kickoff

```bash
# Independent files, safe to start together:
Task: "T011 Add ApplicationNote entity in backend/app/domain/entities.py"
Task: "T012 Add NoteType enum in backend/app/domain/value_objects.py"
Task: "T021 Note DTOs in backend/app/schemas/note.py"
Task: "T024 Note type + API methods in frontend/src/lib/api.ts"
```

---

## Implementation Strategy

- **MVP first**: Setup (T001) → **US1** (T004–T010). Demo the Kanban board. This alone is a
  visible upgrade and depends on nothing else.
- **Incremental**: add US2 (timeline) → US3 (contacts) → US4 (tasks), each its own testable slice
  layered onto the detail panel.
- **Then**: Polish (gates, migration apply, responsiveness, quickstart), and open a PR into `main`.

## Notes

- `[P]` = different files, no incomplete-task dependency.
- Each US2–US4 slice mirrors the existing Application slice exactly — reuse
  `application_service.py`, `application_repository.py`, and `schemas/application.py` as templates.
- Commit after each task or logical group; stop at any checkpoint to validate a story.
