# Implementation Plan: UI Redesign — Tracker & Tailor CV

**Branch**: `004-ui-redesign` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-ui-redesign/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Redesign the Application Tracker and Tailor-CV pages per the high-fidelity design handoff
(`docs/design_handoff_tracker_tailor/`): the tracker gains a pipeline summary strip,
combinable search/status/date filters, a modal add-application flow, and a richer detail
slide-over, while preserving the existing status-transition rules end to end. The tailor
flow becomes a guided wizard around a **persisted base resume** (new backend capability —
schema already exists but is unwired) and a **structured, section-level tailored result**
(new backend capability — requires extending the AI output contract and `tailored_cvs`
schema) with explained changes, download/copy/save-to-application/refine actions. Frontend
work is a Next.js/Tailwind component redesign wired to `lib/api.ts`; backend work adds a
`CVRepository`-backed base-resume flow and a `TailoredCV` structured-output flow, both
following the existing api → services → domain → infrastructure layering.

## Technical Context

**Language/Version**: Python 3.12 (backend, `backend/pyproject.toml:6`); TypeScript via
Next.js 16.2.9 + React 19.2.4 (frontend, `frontend/package.json`)

**Primary Dependencies**: Backend — FastAPI ≥0.115, Pydantic ≥2.10, `anthropic` SDK
(Claude), `supabase` Python client, `pyjwt[crypto]`, `python-multipart` (already present,
unused until now). Frontend — Tailwind CSS v4 (CSS-based config), `@dnd-kit/core` +
`@dnd-kit/sortable` + `@dnd-kit/utilities`, `@supabase/supabase-js` + `@supabase/ssr`. New
dependencies needed and resolved in `research.md`: a PDF/DOCX text-extraction library
(base-resume upload parsing) and a PDF/DOCX generation library (tailored-resume download).

**Storage**: Supabase Postgres. Existing tables `applications`, `application_notes`,
`application_contacts`, `application_tasks` are reused unchanged. Existing tables `cvs`
(base resume metadata) and `tailored_cvs` (AI output) already exist in
`supabase/migrations/20260701170000_init.sql` but are **unwired from any backend code
today** — this feature wires them up and extends `tailored_cvs` with structured
section/changed/explanation data and an application-attachment link (new migration,
detailed in `data-model.md`). A private `cvs` Storage bucket with per-user RLS policies
already exists for the resume file itself.

**Testing**: Backend — pytest + pytest-asyncio + httpx, with in-memory fakes per
repository interface (`backend/tests/fakes.py`) per Constitution Principle IV; new fakes
needed for the CV/base-resume repository. Frontend — **no test runner exists today** (no
vitest/jest/playwright config or test files); `research.md` decides whether to introduce
one for the redesign's non-trivial client logic (filters, staleness, transition rules).

**Target Platform**: Web (desktop/laptop browsers primary, per clarification; mobile must
not visually break but gets no dedicated layout).

**Project Type**: Web application — existing `backend/` (FastAPI) + `frontend/` (Next.js)
monorepo with `supabase/migrations/` for schema.

**Performance Goals**: Tracker summary computed and visible within 3s of page load
(SC-001); search/filter narrows a 50+ item board within 10s (SC-002); board/filters stay
responsive with no perceptible lag up to ~100 applications per user (clarified scale,
FR-003a) using client-side filtering (no server-side pagination/search needed for v1).

**Constraints**: New interactive components (drag-and-drop board, add-application modal,
detail slide-over) MUST meet WCAG 2.1 AA, with the one-tap detail-panel transitions
serving as the required non-drag equivalent for status changes (FR-011a, clarified).
Base resume uploads limited to PDF/DOCX ≤5MB (FR-013). Existing status-transition rules
are enforced unchanged, both client- and server-side (FR-004). No new AI usage
limits/quotas are introduced (clarified). No dedicated mobile layout is in scope; mobile
must only clear a "doesn't visually break" bar (clarified).

**Scale/Scope**: Two redesigned pages (Tracker, Tailor CV), 7 prioritized user stories, 23
functional requirements, single-tenant-per-user data (each user only ever sees their own
applications/resumes — no collaborative/shared-data concurrency concerns).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
|---|---|---|
| I. Spec-First | `specs/004-ui-redesign/spec.md` exists and precedes this plan; clarifications already resolved. | PASS |
| II. Layered OOP Architecture | New base-resume/tailoring work adds a `CVRepository` domain interface + Supabase implementation in `infrastructure/`; routers in `api/v1/routers/cv.py` stay thin (parse/validate/call service); business logic (upsert-current-resume, structured tailoring, refinement, attach-to-application) lives in `services/`. | PASS (planned in Phase 1) |
| III. Dependency Inversion | New CV persistence sits behind a repository interface in `domain/repositories.py`, implemented only in `infrastructure/supabase/`; AI structured-output generation still flows through the single `AIClient` interface (extended prompt template, not a new vendor coupling). | PASS (planned in Phase 1) |
| IV. Typed and Tested | Backend: mypy strict stays clean; new service/repository logic gets pytest unit tests against in-memory fakes (extend `tests/fakes.py`) plus API tests via `TestClient`/httpx. Frontend: constitution only mandates `npm run lint` + `npm run build` for frontend — no violation from the current lack of a frontend test runner, though `research.md` recommends adding one for redesign-specific logic. | PASS |
| V. AI is Abstracted and Configurable | Structured section-output tailoring and refinement stay behind `AIClient`; the new prompt is a new versioned file under `app/infrastructure/ai/prompt_templates/`, not an inline string. Model config remains in `Settings`. | PASS (planned in Phase 1) |

No constitution violations identified. Complexity Tracking table is not needed.

**Post-Phase 1 re-check**: `research.md`, `data-model.md`, and `contracts/cv-api.md`
confirm the design stays within a repository-interface + service-layer + thin-router
shape (no direct Supabase/AI SDK calls outside `infrastructure/`), and introduces no new
top-level projects or vendor couplings. Gates above remain PASS after design.

## Project Structure

### Documentation (this feature)

```text
specs/004-ui-redesign/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── cv-api.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

Existing web-application monorepo layout (`backend/` + `frontend/` + `supabase/`);
redesign work extends it in place, no new top-level projects.

```text
backend/
├── app/
│   ├── api/v1/routers/
│   │   └── cv.py                       # extended: base-resume upload/get/replace/remove,
│   │                                    # structured tailor, refine, attach, download
│   ├── services/
│   │   └── cv_tailoring_service.py     # extended: structured output, refinement, base-resume upsert
│   ├── domain/
│   │   ├── repositories.py             # + CVRepository interface (base resume + tailored CV)
│   │   ├── entities.py                 # CV / TailoredCV entities extended (sections, application_id)
│   │   └── ai.py                       # AIClient contract (structured generate, if needed)
│   ├── infrastructure/
│   │   ├── supabase/
│   │   │   └── cv_repository.py        # new: Supabase-backed CVRepository (table + storage bucket)
│   │   └── ai/prompt_templates/        # + new versioned structured-tailoring prompt
│   └── schemas/cv.py                   # extended request/response models
└── tests/
    ├── fakes.py                        # + InMemoryCVRepository
    ├── unit/test_cv_tailoring_service.py   # extended
    └── integration/test_cv_api.py          # new

frontend/
├── src/app/
│   ├── tracker/page.tsx                # redesigned: stats strip, filters, modal, layout
│   ├── tailor/page.tsx                 # redesigned: wizard (resume → jd → working → result)
│   └── globals.css                     # + design tokens mapped into @theme
├── src/components/
│   ├── KanbanBoard.tsx                 # updated: legal/illegal column affordances, "open" layout
│   ├── ApplicationCard.tsx             # updated: stale indicator, drag-state styling
│   ├── ApplicationDetailPanel.tsx      # updated: one-tap transitions, nudge, WCAG focus handling
│   ├── SearchBar.tsx                   # updated or superseded by a Toolbar component
│   ├── StatsStrip.tsx                  # new
│   ├── FilterToolbar.tsx               # new (search + status + date filters)
│   ├── AddApplicationModal.tsx         # new
│   └── tailor/                        # new: ResumeUploadStep, JobDescriptionStep,
│                                        # ProgressNarrative, TailorResult, ReasoningPanel
└── src/lib/
    ├── api.ts                          # extended: base-resume CRUD, structured tailor/refine/attach
    └── board.ts                        # reused as-is (column/transition mirror)

supabase/migrations/
└── <new>_tailored_cv_structured_output.sql   # extends tailored_cvs (sections jsonb,
                                                # application_id, refinement linkage)
```

**Structure Decision**: Extend the existing `backend/` (FastAPI, layered per Constitution
Principle II) and `frontend/` (Next.js App Router) projects in place — no new services or
projects are introduced. The only new persistent-storage change is one additive Supabase
migration; the `cvs` table, `tailored_cvs` table, and `cvs` Storage bucket already exist
and are reused rather than replaced.

## Complexity Tracking

*No constitution violations identified — this section is not applicable.*
