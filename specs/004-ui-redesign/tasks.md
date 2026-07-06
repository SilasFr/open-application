---

description: "Task list template for feature implementation"
---

# Tasks: UI Redesign — Tracker & Tailor CV

**Input**: Design documents from `/specs/004-ui-redesign/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cv-api.md, quickstart.md (all present)

**Tests**: Not explicitly requested in the spec, but Constitution Principle IV mandates
pytest unit tests against in-memory fakes for every backend service/use-case, and
`research.md` (#7) decided to introduce Vitest for redesign-specific frontend logic that
duplicates backend business rules. Test tasks below reflect those two sources, not a
general TDD request — they are not required to be written before implementation.

**Organization**: Tasks are grouped by user story (US1–US7, matching `spec.md` priorities)
to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US7)

## Path Conventions

Existing web-application monorepo: `backend/app/`, `backend/tests/`, `frontend/src/`,
`supabase/migrations/`. See `plan.md` Project Structure for the full tree.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new dependencies and scaffolding needed before foundational/story work

- [X] T001 [P] Add `pypdf`, `python-docx`, and `reportlab` to `backend/pyproject.toml` dependencies and run `uv lock`
- [X] T002 [P] Add Vitest + `@testing-library/react` devDependencies and a `frontend/vitest.config.ts` (research.md #7)
- [X] T003 [P] Create empty migration file `supabase/migrations/20260706120000_tailored_cv_structured_output.sql` (filled in during US6)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Wire design tokens from `docs/design_handoff_tracker_tailor/{styles.css,tokens/*.css}` into `frontend/src/app/design-tokens.css` (imported by `globals.css`) as plain `:root` custom properties — every redesigned component in every user story depends on these tokens existing. Radius tokens are namespaced `--radius-token-*` (Tailwind v4 already defines `--radius-{sm,md,lg,...}` globally with different values — confirmed via `node_modules/tailwindcss/theme.css` — so reusing the bare names would silently reskin unrelated pages like `/login` and `/`). `--text-*` sizes are value-identical to Tailwind's own scale so reusing them is a no-op; `--font-sans`/`--font-mono` are deliberately left to the app's existing Geist mapping.

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - See application pipeline health at a glance (Priority: P1) 🎯 MVP

**Goal**: Tracker page shows a summary strip (Active / Interviewing / Offers / Response
rate / Need attention) computed from the current applications, and stale applications
are flagged on their cards.

**Independent Test**: Seed applications across all statuses and ages (including one
stale for 7+ days), load the tracker, and verify the summary counts, response rate
(including the 0%-denominator case), and stale flagging match the underlying data.

- [X] T005 [P] [US1] Create summary helper functions (active/interviewing/offers counts, response-rate calc incl. 0% when denominator is 0, staleness predicate) in `frontend/src/lib/stats.ts`
- [X] T006 [P] [US1] Unit test summary helpers, including the 0%-response-rate edge case, in `frontend/src/lib/stats.test.ts`
- [X] T007 [US1] Create `StatsStrip` component (5-cell summary card) in `frontend/src/components/StatsStrip.tsx` (depends on T005)
- [X] T008 [US1] Add stale indicator dot and "No activity in {n}d" meta line to `frontend/src/components/ApplicationCard.tsx` (depends on T005)
- [X] T009 [US1] Integrate `StatsStrip` into `frontend/src/app/tracker/page.tsx` above the toolbar (depends on T007)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Find and filter applications quickly (Priority: P1)

**Goal**: Search (company/role substring) plus status and date-added filters, combinable,
narrow the visible board client-side.

**Independent Test**: Seed many applications across companies/statuses/dates and verify
each filter individually, and all combined, narrow the visible set to the expected
subset.

- [X] T010 [P] [US2] Create filter-predicate helpers (case-insensitive company/role search, status equality, date-window check) in `frontend/src/lib/filters.ts`
- [X] T011 [P] [US2] Unit test filter predicates individually and combined in `frontend/src/lib/filters.test.ts`
- [X] T012 [US2] Create `FilterToolbar` component (search input + status select + date-added select), replacing `frontend/src/components/SearchBar.tsx`, in `frontend/src/components/FilterToolbar.tsx` (depends on T010)
- [X] T013 [US2] Wire `FilterToolbar` state and the filtered application list into `frontend/src/app/tracker/page.tsx` (depends on T012, T009)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Move an application through its pipeline with guardrails (Priority: P1)

**Goal**: Drag-and-drop and one-tap detail-panel transitions both enforce the existing
legal-transition rules, with visual affordances during drag and a keyboard-accessible
alternative.

**Independent Test**: Attempt legal and illegal moves via both drag-and-drop and the
detail panel's one-tap actions; verify accepted moves persist and update last-activity,
rejected moves show an inline explanation and leave status unchanged, and illegal
columns are visually de-emphasized during drag.

- [X] T014 [P] [US3] Add a unit test asserting `frontend/src/lib/board.ts`'s transition rules stay in parity with `backend/app/domain/value_objects.py`'s `_ALLOWED_TRANSITIONS`, in `frontend/src/lib/board.test.ts`
- [X] T015 [US3] Add legal/illegal column highlighting during drag (dim illegal columns, highlight the legal drop target, 40% opacity on the dragged card) to `frontend/src/components/KanbanBoard.tsx`
- [X] T016 [US3] Add inline rejection messaging and revert-on-failure UX (network/persistence error reverts the card to its original column) to `frontend/src/components/KanbanBoard.tsx` (depends on T015)
- [X] T017 [US3] Enable `@dnd-kit`'s `KeyboardSensor` on the board's `DndContext` for keyboard-operable drag in `frontend/src/components/KanbanBoard.tsx` (research.md #9, FR-011a)
- [X] T018 [US3] Replace the status `<select>` fallback in `frontend/src/components/ApplicationCard.tsx` with one-tap legal-transition pill buttons in `frontend/src/components/ApplicationDetailPanel.tsx` (the required non-drag equivalent, FR-011a)
- [X] T019 [US3] Add Closed-group drop mapping (assign the first legal closed status for the card's current status) to `frontend/src/lib/board.ts`

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently — the P1 core of the tracker redesign is complete

---

## Phase 6: User Story 4 - Manage an application's details without losing board context (Priority: P2)

**Goal**: Redesigned detail slide-over: sticky header with status + one-tap transitions,
stale nudge, notes/contacts/tasks sections, dismissible via close/overlay/Escape with
proper focus handling.

**Independent Test**: Open an application's detail view, add a note/contact/task, toggle
a task, and verify each persists and displays correctly; verify Escape/overlay-click
closes it and focus returns to the board.

- [X] T020 [US4] Redesign `frontend/src/components/ApplicationDetailPanel.tsx` layout (sticky header, current-status badge with dot, stale nudge line) (depends on T018)
- [X] T021 [US4] Add focus-trap, Escape-to-close, and overlay-click-to-close behavior to `frontend/src/components/ApplicationDetailPanel.tsx` (FR-011, FR-011a)
- [X] T022 [P] [US4] Restyle `frontend/src/components/NotesTimeline.tsx` per design tokens (newest-first entries, relative timestamps)
- [X] T023 [P] [US4] Restyle `frontend/src/components/ContactsSection.tsx` per design tokens (initials avatar, optional LinkedIn link)
- [X] T024 [P] [US4] Restyle `frontend/src/components/TasksSection.tsx` per design tokens (open-task count pill, accent checkbox, completed strike-through)

**Checkpoint**: User Stories 1–4 all work independently

---

## Phase 7: User Story 5 - Add a new application without losing board focus (Priority: P2)

**Goal**: A modal dialog (company, role, starting status limited to saved/applied)
replaces the permanent inline form.

**Independent Test**: Open the add-application dialog, verify submit stays disabled
until both fields are filled, submit valid values, and verify the new card appears in
the chosen column with current timestamps; verify overlay-click/cancel closes without
creating anything.

- [X] T025 [US5] Create `AddApplicationModal` component (company/role fields, starting-status select limited to saved/applied, autofocus, disabled-until-valid submit, overlay-click/cancel to close) in `frontend/src/components/AddApplicationModal.tsx`
- [X] T026 [US5] Replace the inline create-form in `frontend/src/app/tracker/page.tsx` with a primary "+ Add application" button that opens `AddApplicationModal` (depends on T025, T013)

**Checkpoint**: User Stories 1–5 all work independently — the Tracker redesign is complete

---

## Phase 8: User Story 6 - Tailor a resume to a job description with a guided flow (Priority: P1)

**Goal**: A persisted, replaceable base resume plus a guided wizard (resume → job
description → progress → result) that returns a structured, section-level tailored
resume with per-section change explanations and cross-highlighting.

**Independent Test**: Upload a base resume, reload the page in a new session and
confirm it lands directly on the job-description step, submit a job description, and
verify a structured result renders with changed sections and matching explanations that
cross-highlight together.

### Backend

- [X] T027 [P] [US6] Add base-resume CRUD methods (`get_current`, `replace`, `delete`) to a new `CVRepository` interface in `backend/app/domain/repositories.py`
- [X] T028 [US6] Implement a Supabase-backed `CVRepository` (Storage upload/delete in the `cvs` bucket; delete-then-insert to keep exactly one current row per user, per research.md #3) in `backend/app/infrastructure/supabase/cv_repository.py` (depends on T027)
- [X] T029 [P] [US6] Implement PDF/DOCX text-extraction helper (`pypdf`/`python-docx`) in `backend/app/infrastructure/cv_text_extraction.py` (research.md #1)
- [X] T030 [US6] Wire `CVRepository` and the extraction helper into `backend/app/core/dependencies.py` (depends on T028, T029)
- [X] T031 [P] [US6] Add `InMemoryCVRepository` fake in `backend/tests/fakes.py`
- [X] T032 [US6] Add `POST /cv/base`, `GET /cv/base`, `DELETE /cv/base` endpoints and request/response schemas in `backend/app/api/v1/routers/cv.py` and `backend/app/schemas/cv.py` (depends on T030)
- [X] T033 [P] [US6] Unit tests for base-resume upload/replace/remove and file-type/size validation in `backend/tests/unit/test_cv_base_resume.py` (depends on T031)
- [X] T034 [P] [US6] Integration tests for `/cv/base` endpoints via `TestClient` in `backend/tests/integration/test_cv_api.py` (depends on T032)
- [X] T035 [US6] Fill in the `tailored_cvs` schema migration (`sections jsonb`, `application_id`, `refinement_instructions`, `previous_tailored_cv_id`) in `supabase/migrations/20260706120000_tailored_cv_structured_output.sql`
- [X] T036 [US6] Add a new versioned structured-output prompt template in `backend/app/infrastructure/ai/prompt_templates/` (research.md #4)
- [X] T037 [US6] Extend the `TailoredCV` entity with `sections` and `application_id` fields in `backend/app/domain/entities.py` (depends on T035)
- [X] T038 [US6] Extend `CVTailoringService.tailor()` to require a saved base resume and call the structured-output prompt, validating the model's JSON against the sections schema, in `backend/app/services/cv_tailoring_service.py` (depends on T036, T037)
- [X] T039 [US6] Extend `POST /cv/tailor` request/response schemas (`sections`, `application_id`) and persist via `CVRepository` in `backend/app/schemas/cv.py` and `backend/app/api/v1/routers/cv.py` (depends on T038, T028)
- [X] T040 [P] [US6] Unit tests for structured tailoring failure paths (missing base resume → 404, malformed AI JSON → 422) in `backend/tests/unit/test_cv_tailoring_service.py` (depends on T038)
- [X] T041 [P] [US6] Integration test for `POST /cv/tailor` in `backend/tests/integration/test_cv_api.py` (depends on T039)

### Frontend

- [X] T042 [P] [US6] Extend `frontend/src/lib/api.ts` with `uploadBaseResume`, `getBaseResume`, `deleteBaseResume`, and an extended `tailorCV`/`TailoredCV` type with `sections` (depends on T032, T039)
- [X] T043 [US6] Create `ResumeUploadStep` component (dashed drop zone, saved-resume chip, replace/remove) in `frontend/src/components/tailor/ResumeUploadStep.tsx` (depends on T042)
- [X] T044 [US6] Create `JobDescriptionStep` component (textarea + JD file drop zone + saved-resume chip) in `frontend/src/components/tailor/JobDescriptionStep.tsx`
- [X] T045 [US6] Create `ProgressNarrative` component (stepping checklist, ~900ms per line, respects `prefers-reduced-motion`) in `frontend/src/components/tailor/ProgressNarrative.tsx`
- [X] T046 [US6] Create `TailorResult` component (CV pane with changed-section accent edges, reasoning pane with change cards, click-to-cross-highlight) in `frontend/src/components/tailor/TailorResult.tsx` (depends on T042)
- [X] T047 [US6] Rebuild `frontend/src/app/tailor/page.tsx` as the phase state machine (`resume` → `jd` → `working` → `result`), landing directly on `jd` when a base resume already exists (depends on T043, T044, T045, T046)

**Checkpoint**: User Story 6 works independently — the core Tailor-CV redesign is functional (actions on the result come in US7)

---

## Phase 9: User Story 7 - Act on a tailored resume (Priority: P2)

**Goal**: Download (PDF/DOCX), copy, save-to-application, refine, and start-over actions
on a tailored result.

**Independent Test**: Produce a tailored result and exercise each action, verifying the
expected outcome (file downloads correctly, clipboard has plain text, application gets
attached with confirmation, refinement honors instructions, start-over resets the JD but
keeps the base resume).

### Backend

- [X] T048 [P] [US7] Implement PDF generation (`reportlab`) and DOCX generation (`python-docx`) from a `sections` list in `backend/app/infrastructure/cv_document_rendering.py` (research.md #2)
- [X] T049 [US7] Add `GET /cv/tailored/{id}/download?format=pdf|docx` endpoint in `backend/app/api/v1/routers/cv.py` (depends on T048, T039)
- [X] T050 [US7] Add `POST /cv/tailored/{id}/attach` endpoint with ownership checks on both the tailored resume and the application, in `backend/app/api/v1/routers/cv.py` (depends on T039)
- [X] T051 [US7] Extend `POST /cv/tailor` to accept `refinement_instructions` and `previous_tailored_cv_id`, incorporating prior content into the prompt, in `backend/app/services/cv_tailoring_service.py` (depends on T038)
- [X] T052 [P] [US7] Unit and integration tests for download/attach/refine in `backend/tests/unit/test_cv_tailoring_service.py` and `backend/tests/integration/test_cv_api.py` (depends on T049, T050, T051)

### Frontend

- [X] T053 [P] [US7] Extend `frontend/src/lib/api.ts` with `downloadTailoredCV`, `attachTailoredCV`, and refinement parameters on the tailor function (depends on T049, T050, T051)
- [X] T054 [US7] Add the result action bar (Download PDF, Download DOCX, Copy text with 1.5s confirmation, Save-to-application popover, inline Refine input) to `frontend/src/components/tailor/TailorResult.tsx` (depends on T046, T053)
- [X] T055 [US7] Wire "Start over" and "Refine" transitions back into the phase state machine in `frontend/src/app/tailor/page.tsx` (depends on T047, T054)

**Checkpoint**: All 7 user stories work independently — the full UI redesign is complete

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final gates and validation across both redesigned pages

- [X] T056 [P] Run and fix `uv run ruff check .` and `uv run mypy app` in `backend/` — clean (49 source files), 109 tests passing
- [X] T057 [P] Run and fix `npm run lint` and `npm run build` in `frontend/` — found and fixed 3 `react-hooks/set-state-in-effect` lint errors introduced by the two parallel implementation tracks (`ProgressNarrative.tsx`, `TailorResult.tsx`) and a CSS `@import`-ordering build warning (Google Fonts import hoisted from `design-tokens.css` to the top of `globals.css`); all clean now
- [~] T058 Run the full `quickstart.md` validation walkthrough end-to-end against a staging Supabase project — PARTIAL: migration applied to the real project (`bezcaappcvbtreqdcpov`, confirmed via `\d public.tailored_cvs` before/after), backend boots against it cleanly, `/health` returns 200, and unauthenticated requests to `/api/v1/applications` and the new `/api/v1/cv/base` both correctly return 401. The logged-in, browser-driven scenarios in quickstart.md (User Stories 1-7 step-by-step) are NOT done — that needs a real user session, and creating an account or entering login credentials is something I won't do myself; see completion report
- [X] T059 [P] Update `backend/.env.example` if any new configuration was introduced during implementation — no new config was introduced; no changes needed
- [X] T060 Keyboard-only accessibility pass across the tracker and tailor pages per FR-011a — verified `KanbanBoard`'s `KeyboardSensor`, `ApplicationDetailPanel`'s and `AddApplicationModal`'s focus-trap/Escape/return-focus (added the missing focus trap to `AddApplicationModal`, which only had Escape+autofocus), and the save-popover's Escape/outside-click handling

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3–9)**: All depend on Foundational phase completion
  - US1, US2, US3, US6 have no dependencies on each other and can proceed in parallel
  - US4 depends on US3 (T018, the one-tap transition buttons it redesigns further)
  - US5 depends on US2 (T013, the toolbar/list state it hooks the modal into)
  - US7 depends on US6 (it extends the same tailoring service, schemas, and result component)
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories
- **User Story 2 (P1)**: No dependencies on other stories
- **User Story 3 (P1)**: No dependencies on other stories
- **User Story 4 (P2)**: Builds on US3's detail-panel transition buttons (T018)
- **User Story 5 (P2)**: Builds on US2's toolbar/filtered-list state (T013)
- **User Story 6 (P1)**: No dependencies on other stories
- **User Story 7 (P2)**: Builds on US6's tailoring service, schemas, and result component

### Within Each User Story

- Helpers/repositories before components/services that consume them
- Services before endpoints; endpoints before frontend API-client wiring
- Core implementation before integration into the page shell
- Story complete before moving to the next priority (if working sequentially)

### Parallel Opportunities

- All Setup tasks (T001–T003) can run in parallel
- US1, US2, US3, and US6 can all start in parallel immediately after Foundational (Phase 2)
- Within US6/US7's backend work, T027/T029/T031 (interface, extraction helper, fake) can run in parallel; likewise T033/T034 and T040/T041/T052 test tasks
- Within US4, T022/T023/T024 (three separate component restyles) can run in parallel

---

## Parallel Example: User Story 6 (backend foundation)

```bash
# Launch independent backend scaffolding for User Story 6 together:
Task: "Add base-resume CRUD methods to a new CVRepository interface in backend/app/domain/repositories.py"
Task: "Implement PDF/DOCX text-extraction helper in backend/app/infrastructure/cv_text_extraction.py"
Task: "Add InMemoryCVRepository fake in backend/tests/fakes.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (design tokens wired in)
3. Complete Phase 3: User Story 1 (pipeline summary strip)
4. **STOP and VALIDATE**: Confirm the summary strip against seeded data independently
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Test independently → Demo (MVP)
3. US2, US3 → Test independently → Demo (tracker becomes genuinely usable at scale, with guardrails)
4. US4, US5 → Test independently → Demo (Tracker redesign complete)
5. US6 → Test independently → Demo (Tailor-CV core flow live)
6. US7 → Test independently → Demo (full redesign complete)

### Parallel Team Strategy

With multiple developers, once Foundational is done:

- Developer A: US1 → US4 → US5 (Tracker track)
- Developer B: US2 → US3 (Tracker track)
- Developer C: US6 → US7 (Tailor-CV track, mostly backend-heavy)

Tracks integrate independently since the Tracker and Tailor-CV pages don't share
components.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US4 and US5 are not fully independent of US2/US3 (see User Story Dependencies) —
  this is an intentional, minimal coupling since they redesign the same page shell;
  each is still independently *testable* once its one dependency task lands
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
