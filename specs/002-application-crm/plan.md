# Implementation Plan: Application CRM

**Branch**: `002-application-crm` | **Date**: 2026-07-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-application-crm/spec.md`

## Summary

Turn the flat `/tracker` list into a CRM workspace: a **Kanban board** where dragging a card
changes an application's status (validated), plus a per-application **detail panel** holding an
**activity timeline + notes**, **contacts**, and a **task checklist**. Adds three owner-scoped,
RLS-protected tables (`application_notes`, `application_contacts`, `application_tasks`) that
cascade-delete with their parent application. The backend mirrors the existing Application slice
at every layer (domain → services → thin nested REST routers, Supabase behind repository
interfaces); the frontend adds a @dnd-kit board and slide-over panel.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5 / React 19 (frontend)

**Primary Dependencies**: FastAPI, pydantic, supabase-py, anyio (backend); Next.js 16,
`@supabase/ssr`, **@dnd-kit** (frontend)

**Storage**: Supabase Postgres (new tables + RLS); no file storage in this feature

**Testing**: `pytest` (+ `pytest-asyncio`) against in-memory fakes and FastAPI `TestClient`;
frontend `eslint` + `next build`

**Target Platform**: Linux server (API) + browser SPA; responsive down to mobile

**Project Type**: Web application (`backend/` + `frontend/`)

**Performance Goals**: card move reflected < 1.5 s (SC-CRM-001); detail panel resources load
< 500 ms (SC-CRM-002)

**Constraints**: strict per-user isolation (SC-CRM-004, 0% leakage); cascade delete of child
records (SC-CRM-003); no page reload for note/contact/task mutations

**Scale/Scope**: individual job-seeker scale (tens–hundreds of applications, a handful of
child records each); 3 new tables, ~3 services, ~3 nested routers, 1 board + 1 detail panel

## Constitution Check

*GATE: passed before Phase 0, re-checked after Phase 1.*

- **Spec-first** ✅ — building against `spec.md`; this plan + artifacts precede code.
- **Layered OOP** ✅ — new logic lives in `NoteService` / `ContactService` / `TaskService`;
  routers stay thin (parse → one service → shape).
- **Dependency inversion** ✅ — services depend on new repository ABCs
  (`NoteRepository`, `ContactRepository`, `TaskRepository`); Supabase implementations live in
  `infrastructure/`, wired at the `core/dependencies.py` composition root.
- **Typed & tested** ✅ — full type hints; each service unit-tested against in-memory fakes;
  routers covered via `TestClient`.
- **AI abstraction** ✅ — not applicable; `AIClient` untouched.
- **Security/RLS** ✅ — every table RLS owner-scoped; services also assert parent-application
  ownership.

No violations → **Complexity Tracking left empty.**

## Project Structure

### Documentation (this feature)

```text
specs/002-application-crm/
├── plan.md              # This file
├── research.md          # Phase 0: decisions & rationale
├── data-model.md        # Phase 1: entities, tables, RLS, cascade
├── quickstart.md        # Phase 1: end-to-end validation steps
└── contracts/           # Phase 1: REST contracts
    ├── notes.md
    ├── contacts.md
    └── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── domain/
│   │   ├── entities.py            # + ApplicationNote, ApplicationContact, ApplicationTask
│   │   ├── value_objects.py       # + NoteType enum
│   │   └── repositories.py        # + NoteRepository, ContactRepository, TaskRepository (ABCs)
│   ├── services/
│   │   ├── application_service.py # change_status also records a timeline activity
│   │   ├── note_service.py        # new
│   │   ├── contact_service.py     # new
│   │   └── task_service.py        # new
│   ├── infrastructure/supabase/
│   │   ├── note_repository.py     # new (anyio.to_thread wrapper pattern)
│   │   ├── contact_repository.py  # new
│   │   └── task_repository.py     # new
│   ├── schemas/
│   │   ├── note.py  contact.py  task.py   # new Pydantic DTOs
│   ├── api/v1/routers/
│   │   ├── notes.py  contacts.py  tasks.py # new nested routers
│   └── core/dependencies.py       # wire new repos + services
├── supabase/migrations/
│   └── 20260701xxxxxx_application_crm.sql  # new tables + RLS + indexes + triggers
└── tests/{unit,integration}/       # new service + API tests, updated fakes

frontend/
├── src/app/tracker/page.tsx        # flat list -> KanbanBoard
├── src/components/
│   ├── KanbanBoard.tsx  ApplicationCard.tsx  ApplicationDetailPanel.tsx
│   ├── NotesTimeline.tsx  ContactsSection.tsx  TasksSection.tsx  SearchBar.tsx
└── src/lib/api.ts                  # + notes/contacts/tasks methods & types
```

**Structure Decision**: Web-application layout (Option 2). Every new capability is added by
duplicating the proven Application vertical slice across `domain → services → infrastructure →
schemas → api`, keeping the layering identical to what exists today.

## Phase 0 — Research

See [research.md](research.md). Resolves: drag-and-drop library (**@dnd-kit**), note edit-history
depth (**`updated_at` + "edited" marker**), search location (**client-side**), timeline
auto-event mechanism, cascade-delete strategy, and ownership enforcement. No open
`NEEDS CLARIFICATION`.

## Phase 1 — Design & Contracts

- [data-model.md](data-model.md): three entities/tables with fields, FKs (`ON DELETE CASCADE`),
  RLS policies, indexes, and the notes `updated_at` trigger.
- [contracts/](contracts/): REST contracts for notes, contacts, tasks (nested under
  `/api/v1/applications/{application_id}/…`), including auth and error codes.
- [quickstart.md](quickstart.md): runnable end-to-end validation of the board + panel.

**Cross-cutting design note.** To satisfy US2 acceptance scenario 3 (status change appends a
timeline event), `ApplicationService.change_status` takes a `NoteRepository` and writes an
`activity`-type note after a successful transition. This keeps the rule in the service layer;
unit tests use an in-memory fake note repository.

## Complexity Tracking

*No constitution violations — intentionally empty.*
