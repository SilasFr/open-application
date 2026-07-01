# Feature Specification: MVP — Application Tracker & AI CV Tailoring

**Feature Branch**: `001-mvp-tracker-cv-tailoring`

**Created**: 2026-07-01

**Status**: Draft

**Input**: User description: "Application tracker with status lifecycle and AI CV tailoring from a job description"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Track a job application through its lifecycle (Priority: P1)

A job seeker records a position they are interested in and moves it through stages —
from saved, to applied, to interviewing, to a final outcome — so they always know where
each application stands.

**Why this priority**: The tracker is the core of the product and delivers value on its
own, even before any AI features exist. It is the smallest viable slice.

**Independent Test**: Sign in, create an application for a company/role, change its status
across the allowed lifecycle, and confirm the board reflects each change on reload.

**Acceptance Scenarios**:

1. **Given** a signed-in user, **When** they create an application with a company and role,
   **Then** it is saved with status "saved" and appears in their list.
2. **Given** an application with status "applied", **When** the user moves it to
   "interviewing", **Then** the status updates and is persisted.
3. **Given** an application with status "saved", **When** the user attempts to move it
   directly to "offer", **Then** the change is rejected as an invalid transition.
4. **Given** two different users, **When** each lists their applications, **Then** each sees
   only their own applications.

---

### User Story 2 - Tailor a CV to a specific job description (Priority: P2)

A job seeker pastes their existing CV and a target job description and receives a tailored
version of the CV that emphasizes the most relevant experience, without inventing anything.

**Why this priority**: This is the product's key differentiator, but it depends on the user
already having a CV and a job in mind. Valuable, but the tracker must exist first.

**Independent Test**: Provide CV text and a job description, request tailoring, and confirm a
tailored CV is returned that draws only on the supplied CV.

**Acceptance Scenarios**:

1. **Given** a CV and a job description, **When** the user requests tailoring, **Then** a
   tailored CV is returned in readable form.
2. **Given** an empty CV or empty job description, **When** the user requests tailoring,
   **Then** the request is rejected with a clear validation message.

---

### User Story 3 - Attach a job description to an application and tailor from it (Priority: P3)

A job seeker stores a job description on a tracked application and tailors their CV directly
from that stored description, connecting the two features.

**Why this priority**: A convenience that ties the tracker and the AI tool together; nice to
have once both P1 and P2 exist.

**Independent Test**: Create an application with a job description, trigger tailoring from it,
and confirm the tailored CV is produced from the stored description.

**Acceptance Scenarios**:

1. **Given** an application that has a stored job description, **When** the user tailors a CV
   from that application, **Then** the stored description is used as the tailoring input.

### Edge Cases

- What happens when the AI provider is slow or unavailable? The user sees an error and can
  retry; no partial/blank CV is stored.
- How does the system handle a very long CV or job description that exceeds the model's
  input budget? Input limits are enforced with a clear message.
- What happens when a user tries to read or modify an application that is not theirs? The
  system behaves as if it does not exist (owner-scoped).
- What happens on an illegal status transition (e.g. from a terminal state)? It is rejected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to create a job application with at least a company and role.
- **FR-002**: The system MUST assign a new application the initial status "saved".
- **FR-003**: Users MUST be able to view a list of their own applications.
- **FR-004**: Users MUST be able to change an application's status only along allowed
  lifecycle transitions; terminal states (accepted, rejected, withdrawn) MUST accept no
  further transitions.
- **FR-005**: Users MUST be able to delete their own applications.
- **FR-006**: The system MUST scope all application data to its owner; a user MUST never see
  or modify another user's applications.
- **FR-007**: Users MUST be able to submit a CV and a job description and receive a tailored
  CV in return.
- **FR-008**: The system MUST reject tailoring requests where the CV or job description is
  empty.
- **FR-009**: Tailored CVs MUST be grounded only in the supplied CV; the system MUST instruct
  the AI not to fabricate experience.
- **FR-010**: The system MUST authenticate users and associate all data with the
  authenticated user. *(NOTE: current skeleton uses an `X-User-Id` header stub; real Supabase
  JWT verification is required before launch.)*

### Key Entities *(include if feature involves data)*

- **Application**: A tracked job application. Attributes: company, role, status (lifecycle),
  optional job description, created/updated timestamps. Owned by one user.
- **CV**: A base CV the user provides. Attributes: filename, stored file reference, extracted
  text. Owned by one user.
- **TailoredCV**: An AI-generated CV tailored to a job description. Relationships: derived from
  an optional source CV and a job description. Owned by one user.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can create an application and see it in their list in under 10 seconds.
- **SC-002**: 100% of illegal status transitions are rejected; 0 cross-user data leaks.
- **SC-003**: A tailored CV is returned for valid input in under 30 seconds.
- **SC-004**: Tailored CVs introduce no experience, employers, or dates absent from the
  source CV (validated by review sampling).

## Assumptions

- Authentication and file storage are provided by Supabase; the tracker and AI features build
  on top of it.
- For the MVP, CV input may be provided as text; parsing uploaded PDF/DOCX files into text is
  a follow-up.
- Tailored CV output is returned as Markdown for the MVP; rendering to PDF/DOCX is a follow-up.
- The AI provider is Anthropic Claude, accessed only through the backend `AIClient` abstraction.
- A single default base CV per request is sufficient for the MVP; CV libraries/versioning are
  out of scope.
