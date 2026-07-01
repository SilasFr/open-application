# Research: Application CRM

Phase 0 decisions. Each is stated as Decision / Rationale / Alternatives considered.

## 1. Drag-and-drop library

- **Decision**: Use **@dnd-kit** (`@dnd-kit/core`, `@dnd-kit/sortable`) for the Kanban board.
- **Rationale**: Lightweight, actively maintained, built-in keyboard and touch sensors (mobile +
  accessibility come "for free"), and a hook-based API that fits React 19 / Next.js client
  components. Handles the "revert on invalid drop" flow cleanly via drag-end callbacks.
- **Alternatives considered**:
  - *Native HTML5 DnD* — zero dependencies but poor mobile support and weak accessibility; we'd
    hand-roll touch handling and focus management.
  - *react-dnd* — capable but older, heavier, and a more verbose backend/monitor API than needed.

## 2. Note edit history depth (FR-CRM-005)

- **Decision**: Track `created_at` + `updated_at`; surface an **"edited" indicator** with the
  last-edited time. No separate version table in this feature.
- **Rationale**: Covers the realistic need ("this note was changed") at near-zero cost, reusing
  the existing `set_updated_at` trigger pattern. Full version history is a self-contained future
  feature if demand appears.
- **Alternatives considered**: A `application_note_versions` table capturing every prior body —
  richer but adds a table, endpoints, and UI for marginal early value.

## 3. Search location (FR-CRM-010)

- **Decision**: **Client-side** filter over the already-loaded board data (company, role, and any
  loaded contact names). No new backend search endpoint.
- **Rationale**: At individual-user scale the whole board is already in memory; filtering in the
  browser is instant and needs no API work. Matches the spec assumption.
- **Alternatives considered**: A backend `?q=` search endpoint (Postgres `ilike`/full-text) —
  warranted only at much larger scale; deferred.

## 4. Timeline auto-events on status change (US2 scenario 3)

- **Decision**: `ApplicationService.change_status` records an `activity`-type note (e.g.
  "Moved to Interviewing") after a successful, valid transition, via an injected `NoteRepository`.
- **Rationale**: Keeps the business rule in the service layer (constitution), reuses the notes
  table as the unified timeline, and is trivially testable with an in-memory fake note repo.
- **Alternatives considered**: A DB trigger on `applications.status` — hides logic in SQL, harder
  to unit-test and to phrase human-readable messages. A domain-event bus — overkill at this scope.

## 5. Cascade delete of child records (SC-CRM-003)

- **Decision**: Each child table's `application_id` is a FK to `applications(id)` with
  `ON DELETE CASCADE` (and `user_id → auth.users(id) ON DELETE CASCADE`).
- **Rationale**: Guarantees zero orphaned notes/contacts/tasks at the database level regardless of
  how the application is deleted; no application-code cleanup needed.
- **Alternatives considered**: Service-layer cascade — more code and a race/oversight risk versus
  a referential-integrity guarantee.

## 6. Ownership enforcement (SC-CRM-004)

- **Decision**: Two layers. (a) RLS `auth.uid() = user_id` on every table. (b) Each child service
  first calls `ApplicationRepository.get(user_id, application_id)`; a miss raises `NotFoundError`
  → HTTP 404, so a user cannot address child resources under an application they don't own.
- **Rationale**: RLS is the hard guarantee; the service check gives correct 404 semantics and
  keeps the API honest even though the backend uses the service key.
- **Alternatives considered**: Relying on RLS alone — but the backend client uses the service key
  (bypasses RLS), so the explicit ownership check is required, with RLS as defense-in-depth.

## 7. Board ↔ status mapping

- **Decision**: The DB keeps all seven concrete statuses. The board renders five columns; the
  "Closed" column collapses `accepted` / `rejected` / `withdrawn`. Drags map to a target status
  and go through the existing `PATCH /applications/{id}/status`, which enforces `can_transition`.
- **Rationale**: No schema change, no new transition rules; the UI is a presentation over existing
  validated state.
- **Alternatives considered**: A stored "column" field — redundant with status and a second source
  of truth to keep in sync.
