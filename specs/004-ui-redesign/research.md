# Phase 0 Research: UI Redesign — Tracker & Tailor CV

All unknowns from the plan's Technical Context are resolved below. Each entry follows
Decision / Rationale / Alternatives considered.

## 1. Base-resume text extraction (PDF/DOCX → plain text)

- **Decision**: Use `pypdf` for PDF text extraction and `python-docx` for DOCX text
  extraction, both pure-Python with no system-level dependencies.
- **Rationale**: The extracted text only needs to feed an LLM prompt (Claude reads plain
  text, not layout), so exact visual fidelity is unnecessary. Both libraries are
  lightweight, MIT/BSD-licensed, and have no native/system dependencies — important for
  simple, portable deployment. `python-multipart` is already installed
  (`backend/pyproject.toml`), confirming file upload was anticipated but never wired up.
- **Alternatives considered**: `pdfplumber` (heavier, layout/table-focused — overkill
  here), `textract` (unmaintained, pulls in many system binaries), `unstructured`
  (large dependency footprint for a narrowly-scoped need).

## 2. Tailored-resume generation (download as PDF/DOCX)

- **Decision**: Generate DOCX with `python-docx` (same library as extraction, one fewer
  dependency to learn) and PDF with `reportlab`, rendering the structured `sections`
  list (heading + body) directly rather than converting from an intermediate HTML/DOCX
  form.
- **Rationale**: Both are pure-Python and require no system packages (no Pango/Cairo,
  no headless LibreOffice process), which matters for a simple containerized deploy.
  Rendering straight from structured sections (already required for the change-highlight
  UI, see #4) avoids a second "layout parsing" step.
- **Alternatives considered**: WeasyPrint (needs system Pango/Cairo — heavier
  operational footprint), headless LibreOffice conversion (introduces an external
  process dependency and failure mode not justified by this feature's scope).

## 3. "Current" base resume semantics

- **Decision**: Enforce "one active base resume per user" at the service layer
  (`CVTailoringService`/new base-resume logic): uploading a new resume deletes the
  previous row from `cvs` and its Storage object before inserting the new one. No schema
  change (e.g. an `is_active` flag) is introduced.
- **Rationale**: The spec (FR-012, User Story 6 AC6) describes replace/remove of a
  single resume, not multi-version history. Adding a flag or history table would be
  speculative complexity the spec doesn't ask for (Constitution: no premature
  abstraction).
- **Alternatives considered**: `is_active boolean` + keep old rows for history
  (rejected — no requirement calls for resume history; adds unused complexity).

## 4. Structured tailored-output representation

- **Decision**: Extend the AI prompt (new versioned template under
  `app/infrastructure/ai/prompt_templates/`) to require the model return JSON matching:
  `{ "sections": [{ "id": str, "heading": str, "body": str, "changed": bool,
  "explanation": str | null }] }`. Validate the model's response against a Pydantic
  model before persisting. Persist the structured `sections` in a new `jsonb` column on
  `tailored_cvs`, and keep the existing `content` column as the full rendered plain text
  (derived by joining section bodies) so copy/download don't need to reconstruct text
  from JSON at read time.
- **Rationale**: FR-017/FR-018 require per-section changed-flags and explanations, and
  cross-highlighting a section with its explanation — this is only possible if the model
  itself demarcates sections and explains them; it can't be reliably reconstructed by
  diffing plain text after the fact.
- **Alternatives considered**: Keep the single opaque `content` string and diff
  client-side against the original resume (rejected — no reliable section boundaries to
  diff against, and explanations require model-authored rationale that diffing cannot
  produce).

## 5. Linking a tailored resume to an Application ("save to application")

- **Decision**: Add a nullable `application_id uuid references applications(id) on
  delete set null` column to `tailored_cvs`. Attaching sets/replaces this single link
  (one tailored resume attaches to at most one application at a time); no join table.
- **Rationale**: FR-021 and User Story 7 AC3 describe attaching one tailored resume to
  one application, not a many-to-many relationship.
- **Alternatives considered**: A join table for many-to-many attachment (rejected — not
  required by the spec, adds unused complexity).

## 6. Refinement flow

- **Decision**: Model "refine" as another call into the same tailoring operation, adding
  optional `previous_tailored_cv_id` and `refinement_instructions` fields to the
  request. The prompt template incorporates the prior tailored content plus the new
  instructions. No separate "refine" service or endpoint.
- **Rationale**: Refinement is the same underlying capability (base resume + job
  description → tailored, structured output) with extra context; a parallel service
  would duplicate the structured-output/validation logic (Constitution Principle II
  favors one cohesive service over near-duplicates).
- **Alternatives considered**: A dedicated `RefineCVService` (rejected — unnecessary
  duplication of `CVTailoringService`'s generation and validation logic).

## 7. Frontend testing

- **Decision**: Introduce Vitest + React Testing Library, scoped to the redesign's
  non-trivial pure client logic: filter predicates (search/status/date), staleness
  calculation, and the client-side transition-legality mirror in `lib/board.ts`.
  Full Playwright/e2e coverage is out of scope for this feature; end-to-end validation
  is manual, guided by `quickstart.md`.
- **Rationale**: The frontend currently has zero test tooling, but this redesign
  duplicates business rules (transitions, staleness) on the client for instant UI
  feedback — that duplication is exactly the kind of logic that silently drifts from
  the backend's source of truth without a test pinning it down. The constitution's
  frontend gate (`npm run lint` + `npm run build`) doesn't mandate this, but it directly
  reduces risk introduced by this feature.
- **Alternatives considered**: No frontend tests (rejected — leaves client-duplicated
  business rules unverified); full Playwright e2e suite (rejected as scope creep beyond
  what this feature needs; constitution doesn't require it).

## 8. Design token integration

- **Decision**: Copy the custom-property values from
  `docs/design_handoff_tracker_tailor/{styles.css,tokens/*.css}` into
  `frontend/src/app/globals.css`, merged into the existing Tailwind v4 `@theme inline`
  block, rather than importing the `docs/` files at build time.
- **Rationale**: The handoff README explicitly treats `docs/design_handoff_tracker_tailor/`
  as reference material to recreate from, not ship as-is ("do not copy the prototype
  files in"). Copying token *values* into the app's own stylesheet keeps the production
  build decoupled from a docs/ path while preserving the design system's colors,
  spacing, radii, shadows, and typography scale.
- **Alternatives considered**: `@import`-ing the docs files directly at build time
  (rejected — couples the production bundle to a non-shipping documentation path).

## 9. Drag-and-drop keyboard accessibility (WCAG 2.1 AA)

- **Decision**: The detail panel's one-tap status-transition buttons (already required
  by User Story 3 AC4) serve as the WCAG-required non-drag equivalent for status
  changes. Additionally, enable `@dnd-kit`'s built-in `KeyboardSensor` on the board's
  `DndContext` so keyboard users who prefer to stay on the board can still reorder
  status via keyboard, since the dependency is already installed and unused for this.
- **Rationale**: Reuses an existing, tested library capability (`KeyboardSensor`) rather
  than building custom keyboard-driven drag logic, while the clarified requirement
  (FR-011a) is satisfied at minimum by the already-planned one-tap buttons.
- **Alternatives considered**: Building fully custom keyboard-operable drag-and-drop
  (rejected — reinvents what `@dnd-kit` already ships).
