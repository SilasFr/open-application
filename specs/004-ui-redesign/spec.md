# Feature Specification: UI Redesign — Tracker & Tailor CV

**Feature Branch**: `004-ui-redesign`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: "UI Redesign"

## Clarifications

### Session 2026-07-06

- Q: What accessibility conformance target should the new interactive components (drag-and-drop board, add-application modal, detail slide-over) meet? → A: Meet WCAG 2.1 AA for all new interactive components; drag-and-drop status changes have a non-drag equivalent via one-tap transitions in the detail view, and modals/panels get proper focus trapping and keyboard dismissal.
- Q: What scale must the tracker board and its filters perform well at? → A: Up to ~100 applications per user (typical active job search); client-side filtering is sufficient, no server-side pagination/search needed for v1.
- Q: Should tailor/refine requests have any new usage limits introduced by this redesign? → A: No new usage limits in this spec — requests are unrestricted beyond whatever the existing AI integration already enforces.
- Q: Is dedicated mobile layout work in scope for this redesign? → A: No dedicated mobile redesign — usable on mobile only to a "doesn't break" bar (no layout breakage), not a full mobile-optimized layout for the tracker board or tailor wizard.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See application pipeline health at a glance (Priority: P1)

A job seeker opens the Tracker and, before reading any single card, sees a summary of
how their search is going overall — how many applications are active, how many are in
interviews, how many offers they have, their response rate, and how many need attention
because nothing has happened in a while.

**Why this priority**: This is the first thing users see on the page that matters most
to daily use. It turns the tracker from a static list into a motivating, actionable
overview, and surfaces neglect (stale applications) that otherwise goes unnoticed.

**Independent Test**: Can be fully tested by loading the tracker with a seeded set of
applications in various statuses and ages, and verifying the summary counts and
response rate match the underlying data without needing any other redesigned piece.

**Acceptance Scenarios**:

1. **Given** a set of applications across all statuses, **When** the tracker page loads,
   **Then** a summary strip shows counts for Active, Interviewing, Offers, a computed
   Response rate percentage, and a count of applications needing attention.
2. **Given** an application with no activity for 7 or more days while in an active
   status (saved, applied, interviewing, or offer), **When** the summary is computed,
   **Then** it is counted under "needing attention" and the corresponding card is
   visually flagged.
3. **Given** zero applications with a status other than "saved", **When** response rate
   is computed, **Then** it displays 0% rather than an error or undefined value.

---

### User Story 2 - Find and filter applications quickly (Priority: P1)

A user with dozens of tracked applications wants to narrow the board down to a specific
company/role or a recent time window without scrolling through every column.

**Why this priority**: Without search/filter, the tracker becomes unusable past a
handful of applications, which is a near-term reality for active job seekers. This is
required for the tracker to remain useful as data grows, and is independent of the
visual polish work.

**Independent Test**: Can be fully tested by seeding many applications and verifying
that typing a search term, choosing a status, or choosing a date range narrows the
visible cards to the expected subset, with no dependency on drag-and-drop or the detail
panel.

**Acceptance Scenarios**:

1. **Given** a board with applications from multiple companies, **When** the user types
   part of a company or role name into search, **Then** only matching cards remain
   visible (case-insensitive, partial match).
2. **Given** a status filter is set to a specific status, **When** applied, **Then**
   only cards with that status are visible.
3. **Given** a date filter of "last 7 days" or "last 30 days", **When** applied,
   **Then** only applications created within that window are visible.
4. **Given** multiple filters are set at once, **When** applied together, **Then** only
   cards matching all active filters are visible.

---

### User Story 3 - Move an application through its pipeline with guardrails (Priority: P1)

A user drags a card from one column to another, or uses one-tap status actions in the
detail view, to reflect real progress (e.g., moved from "applied" to "interviewing").
The system prevents moves that don't make sense (e.g., jumping from "saved" straight to
"offer") and gives clear feedback when a move is disallowed.

**Why this priority**: Status transitions are the core recurring action on this page.
Preserving the existing legal-transition rules while making them visible during
interaction (rather than only failing silently after the fact) is essential to trust
in the tool.

**Independent Test**: Can be fully tested by attempting both legal and illegal moves
(via drag-and-drop and via the detail panel's one-tap transitions) against a known set
of applications and verifying accepted moves persist while rejected moves show an
explanatory error and leave the application unchanged.

**Acceptance Scenarios**:

1. **Given** an application in "applied" status, **When** the user drags its card to
   "interviewing", **Then** the move succeeds and the application's last-activity
   timestamp updates.
2. **Given** an application in "saved" status, **When** the user attempts to move it
   directly to "offer", **Then** the move is rejected and an inline message explains
   the move isn't allowed.
3. **Given** a drag is in progress, **When** the user hovers over a column that cannot
   legally receive the card, **Then** that column is visually de-emphasized, and a
   column that can legally receive it is visually highlighted.
4. **Given** an application in any status, **When** the user opens its detail view,
   **Then** only the statuses it can legally move to are offered as one-tap actions.
5. **Given** a card is dropped onto the "Closed" grouping, **When** the drop is
   processed, **Then** it is assigned the first legal closed status available for that
   application's current status (accepted, rejected, or withdrawn).

---

### User Story 4 - Manage an application's details without losing board context (Priority: P2)

A user clicks into an application to add notes, track contacts, manage follow-up tasks,
and change its status, then returns to the board without a jarring page transition.

**Why this priority**: Rich per-application tracking (notes, contacts, tasks) is a key
differentiator of the tool but is secondary to the pipeline-visibility and filtering
work; it can ship after P1 stories land.

**Independent Test**: Can be fully tested by opening an application's detail view,
adding a note/contact/task, and verifying each persists and displays correctly,
independent of the summary strip or filters.

**Acceptance Scenarios**:

1. **Given** an application is selected, **When** the detail view opens, **Then** it
   shows the role, company, time since added, current status, and legal one-tap status
   actions.
2. **Given** the detail view is open, **When** the user adds a note, **Then** it appears
   at the top of the timeline with a relative timestamp.
3. **Given** the detail view is open, **When** the user adds a task and later checks it
   complete, **Then** the open-task count updates and the task displays as completed.
4. **Given** an application has had no activity for 7+ days, **When** its detail view
   opens, **Then** a nudge suggests adding a note or task to keep it moving.
5. **Given** the detail view is open, **When** the user clicks outside it or presses
   Escape, **Then** it closes and returns focus to the board.

---

### User Story 5 - Add a new application without losing board focus (Priority: P2)

A user wants to log a new application they just submitted, without a permanently
present form taking up board space.

**Why this priority**: Reduces visual clutter versus the current permanent inline form,
improving how the board reads at a glance; secondary to viewing and moving existing
applications.

**Independent Test**: Can be fully tested by opening the add-application action,
submitting company/role/status, and verifying the new card appears in the correct
column with correct timestamps, independent of other redesigned pieces.

**Acceptance Scenarios**:

1. **Given** the tracker page, **When** the user triggers "Add application", **Then** a
   dialog opens prompting for company, role, and a starting status limited to "saved"
   or "applied".
2. **Given** the dialog is open with company and role both empty, **When** the user
   looks at the submit action, **Then** it is disabled until both fields are filled.
3. **Given** valid company and role are entered and submitted, **When** the dialog
   closes, **Then** the new application appears in the chosen column with its
   created-at and last-activity timestamps set to the current time.
4. **Given** the dialog is open, **When** the user clicks the overlay or cancels,
   **Then** the dialog closes without creating an application.

---

### User Story 6 - Tailor a resume to a job description with a guided flow (Priority: P1)

A user uploads their base resume once, pastes in a job description, and receives a
tailored version of their resume with visible explanations of what changed and why —
replacing the current two-textarea form with a guided, lower-friction flow.

**Why this priority**: This is the core value proposition of the "Tailor CV" feature;
the guided flow with a persisted base resume and explained changes is the primary
redesign goal and delivers value independently of the tracker work.

**Independent Test**: Can be fully tested end-to-end by uploading a resume, submitting
a job description, and verifying a tailored result renders with per-section change
explanations, without depending on any tracker redesign work.

**Acceptance Scenarios**:

1. **Given** a user has no previously saved base resume, **When** they visit the Tailor
   page, **Then** they are prompted to upload one (PDF or DOCX, up to 5 MB) before
   continuing.
2. **Given** a base resume has already been saved for the user, **When** they revisit
   the Tailor page (including in a new session or on a different device), **Then** they
   land directly on the job-description step without re-uploading.
3. **Given** a saved base resume and a submitted job description, **When** the user
   starts tailoring, **Then** a progress narrative communicates that generation is
   underway before the result appears.
4. **Given** a completed tailoring run, **When** the result renders, **Then** changed
   sections of the resume are visually distinguished and each has an associated
   explanation of what changed and why.
5. **Given** a result is displayed, **When** the user selects a changed section or its
   corresponding explanation, **Then** both are highlighted together; selecting again
   clears the highlight.
6. **Given** a user wants to replace their saved base resume, **When** they choose to
   replace or remove it, **Then** the stored resume is updated or cleared accordingly
   and future visits reflect the change.

---

### User Story 7 - Act on a tailored resume (Priority: P2)

After reviewing a tailored resume, a user downloads it, copies its text, attaches it to
a tracked application, or asks for a refinement — without starting over from scratch.

**Why this priority**: These actions convert a tailored result into real-world use
(applying, tracking) and refinement into a better result; secondary to producing the
first tailored result at all.

**Independent Test**: Can be fully tested by producing a tailored result and exercising
each action (download, copy, save to application, refine, start over) and verifying the
expected outcome, independent of how the result was generated.

**Acceptance Scenarios**:

1. **Given** a tailored result is shown, **When** the user chooses to download it,
   **Then** they can obtain it as a PDF or as a DOCX file.
2. **Given** a tailored result is shown, **When** the user chooses to copy it, **Then**
   the plain text of the tailored resume is copied and the action confirms success.
3. **Given** a tailored result is shown and the user has existing tracked applications,
   **When** they choose to save it to an application, **Then** they can pick one from a
   list and the tailored resume becomes attached to that application, with confirmation
   shown.
4. **Given** a tailored result is shown, **When** the user requests a refinement with
   additional instructions, **Then** a new tailored result is generated honoring those
   instructions.
5. **Given** a tailored result is shown, **When** the user chooses "start over", **Then**
   they return to the job-description step with their saved base resume retained and
   the previous job description cleared.

---

### Edge Cases

- What happens when a user has zero tracked applications? The summary strip and board
  should render with all-zero/empty states rather than errors, and columns should show
  an empty-state message.
- What happens when a drag-and-drop move fails (network/persistence error) after being
  visually accepted? The card must return to its original column and an error must be
  shown; the underlying status must not change.
- What happens when a user uploads a base resume or job description file that exceeds
  the size limit or is an unsupported type? The system must reject it with a clear
  message and not proceed.
- What happens when a job description is submitted with no saved base resume (e.g., a
  race between two tabs)? The user must be redirected back to the upload step.
- What happens when the "save to application" list is empty (no tracked applications
  exist yet)? The action must clearly communicate there is nothing to attach to yet.
- What happens when a refinement request is submitted with empty instructions? The
  system must require non-empty instructions before regenerating.
- How does the system behave when generation (tailoring or refinement) fails outright?
  The user must see an error and be able to retry without losing their job description
  or base resume.
- What happens when the tracker or tailor pages are viewed on a mobile-width viewport?
  Layout must not break (no overlapping/clipped content, no controls that are
  impossible to reach or activate), even though no dedicated mobile layout is provided.

## Requirements *(mandatory)*

### Functional Requirements

**Tracker**

- **FR-001**: The tracker MUST display a summary of Active, Interviewing, Offers,
  Response rate, and Need-attention counts, computed from the current set of tracked
  applications.
- **FR-002**: The tracker MUST let users filter visible applications by free-text
  search over company and role (case-insensitive, partial match), by status, and by
  date-added window (any / last 7 days / last 30 days), combinable together.
- **FR-003**: The tracker MUST organize applications into columns by status, with
  accepted/rejected/withdrawn applications grouped into a single "Closed" view.
- **FR-003a**: The tracker's board, summary, and filters MUST remain responsive (no
  perceptible lag) for a user with up to ~100 tracked applications; client-side
  filtering over the full set is an acceptable approach at this scale.
- **FR-004**: The tracker MUST enforce the existing status-transition rules
  (saved→applied/withdrawn; applied→interviewing/rejected/withdrawn;
  interviewing→offer/rejected/withdrawn; offer→accepted/rejected/withdrawn; closed
  statuses are terminal) for every move, whether initiated by drag-and-drop or by a
  one-tap action in the detail view.
- **FR-005**: The tracker MUST visually indicate, during a drag interaction, which
  destination columns are legal and which are not for the card being dragged.
- **FR-006**: The tracker MUST reject illegal moves with a clear inline explanation and
  leave the application's status unchanged.
- **FR-007**: The tracker MUST update an application's last-activity timestamp on every
  successful status change.
- **FR-008**: The tracker MUST flag an application as needing attention when it is in
  an active status (saved, applied, interviewing, or offer) and has had no activity for
  7 or more days, both in the summary count and on the individual card.
- **FR-009**: The tracker MUST provide an add-application action that collects company,
  role, and a starting status limited to "saved" or "applied", and only allows
  submission once company and role are both provided.
- **FR-010**: The tracker MUST provide a detail view per application showing its
  status with available one-tap legal transitions, a note timeline (newest first, with
  the ability to add a note), a contacts list, and a task list with the ability to add
  a task and toggle completion.
- **FR-011**: The tracker's detail view MUST be dismissible via an explicit close
  action, clicking outside it, or pressing Escape.
- **FR-011a**: All new interactive components (board drag-and-drop, add-application
  modal, detail slide-over) MUST meet WCAG 2.1 AA: every status change reachable by
  drag-and-drop MUST also be reachable via a non-drag control (the detail view's
  one-tap transitions satisfy this), and modals/panels MUST trap focus while open and
  be dismissible via keyboard.

**Tailor CV**

- **FR-012**: The tailor flow MUST persist a user's uploaded base resume server-side so
  it is available across sessions and devices, and let the user replace or remove it.
- **FR-013**: The tailor flow MUST accept a base resume as PDF or DOCX up to 5 MB, and
  reject files that don't meet those constraints with a clear message.
- **FR-014**: The tailor flow MUST skip directly to the job-description step when a
  base resume is already saved for the user.
- **FR-015**: The tailor flow MUST require a job description (pasted text or uploaded
  file) before generation can start.
- **FR-016**: The tailor flow MUST show progress feedback to the user while a tailored
  resume is being generated.
- **FR-017**: The tailor flow MUST return a tailored resume broken into sections, each
  flagged as changed or unchanged, with a human-readable explanation for every changed
  section.
- **FR-018**: The tailor flow MUST let a user select a changed section or its
  explanation and see both highlighted together, and clear the highlight on a second
  selection.
- **FR-019**: The tailor flow MUST let a user download the tailored resume as PDF and
  as DOCX.
- **FR-020**: The tailor flow MUST let a user copy the tailored resume as plain text,
  with visible confirmation the copy succeeded.
- **FR-021**: The tailor flow MUST let a user attach the tailored resume to one of
  their existing tracked applications, with visible confirmation of which application
  it was attached to.
- **FR-022**: The tailor flow MUST let a user submit refinement instructions to
  regenerate the tailored resume, requiring non-empty instructions before regenerating.
- **FR-023**: The tailor flow MUST let a user start over into a new job description
  while retaining their saved base resume.

### Key Entities

- **Application**: A tracked job application. Attributes include company, role,
  current status (saved, applied, interviewing, offer, accepted, rejected, withdrawn),
  created-at, last-activity timestamps, and associations to notes, contacts, tasks, and
  optionally an attached tailored resume.
- **Note**: A free-text timeline entry attached to an application, with a type and a
  created timestamp.
- **Contact**: A person associated with an application (name, role, email, optional
  professional-profile link).
- **Task**: A follow-up item attached to an application with a completion state.
- **Base Resume**: A user's persisted source resume (file plus parsed content), one
  active version per user, replaceable/removable.
- **Tailored Resume**: The generated output of tailoring a base resume against a job
  description — sections with changed/unchanged flags and per-section explanations,
  optionally attached to an Application.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can assess their overall pipeline status (active/interviewing/
  offers/response rate/needs-attention) within 3 seconds of the tracker page loading,
  without opening any individual application.
- **SC-002**: Users can narrow a board of 50+ applications down to a relevant subset
  using search and/or filters in under 10 seconds.
- **SC-003**: 100% of illegal status-transition attempts are rejected with a visible
  explanation, and 0% of them alter stored application data.
- **SC-004**: Users complete adding a new application in under 20 seconds from opening
  the add action to seeing the new card on the board.
- **SC-005**: Returning users with a previously saved base resume can start a new
  tailoring request without re-uploading their resume, 100% of the time.
- **SC-006**: Users can go from having a job description ready to seeing a tailored
  result, understanding what changed and why, without needing outside help or
  documentation.
- **SC-007**: Users can download, copy, or attach a tailored resume to an application
  in one action each (single click/tap) from the result view.
- **SC-008**: Applications that have gone stale (7+ days without activity) are
  surfaced to the user without them having to open every card individually.

## Assumptions

- This redesign covers the two pages described in the existing design handoff
  (`docs/design_handoff_tracker_tailor/`): the Application Tracker and the Tailor-CV
  flow. It is a visual and interaction redesign of existing functionality, not the
  introduction of new domains beyond what's described above.
- Existing status-transition rules, note/contact/task data, and the current AI-backed
  resume-tailoring capability are reused as-is; this redesign changes how they are
  presented and interacted with, not the underlying business rules.
- "Base resume" persistence is a new capability implied by the redesign (today's flow
  does not save a resume between sessions); it is treated as in-scope per the design
  handoff's explicit instruction to store it server-side per user.
- Structured, section-level tailoring output (changed flags + explanations) is a new
  requirement on the tailoring capability, needed to support the redesigned result view;
  it extends rather than replaces today's tailoring behavior.
- Visual styling specifics (exact colors, spacing, tokens) are treated as design detail
  owned by the linked design handoff and its token files, not restated as functional
  requirements here.
- Dedicated mobile layouts are out of scope for this redesign; the tracker board and
  tailor wizard must not visually break on mobile viewports (no overlapping content,
  no unusable controls), but no mobile-optimized layout work is required.
- No new usage limits or quotas are introduced for tailor/refine requests by this
  redesign; any throttling remains governed by whatever the existing AI integration
  already enforces.
