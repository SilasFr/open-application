# Feature Specification: Application CRM

**Feature Branch**: `002-application-crm`

**Created**: 2026-07-01

**Status**: Draft

**Input**: User description: "Manage applications in a CRM-like interface"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visual Kanban Pipeline Board (Priority: P1)

A job seeker views all of their tracked applications organized in columns by lifecycle stage (Saved, Applied, Interviewing, Offer, and Closed). They can easily drag and drop applications to move them between stages, instantly update their status, and see a visual count of applications at each stage of their search funnel.

**Why this priority**: Translating a static list into a dynamic Kanban pipeline is the visual foundation of a CRM interface. It provides immediate value by letting users visualize their funnel.

**Independent Test**:
1. Sign in and navigate to the application tracker board.
2. Verify that columns exist for each key status (Saved, Applied, Interviewing, Offer, Closed).
3. Drag (or trigger action to move) a card from "Saved" to "Applied".
4. Reload the page and verify the application remains in the "Applied" column.

**Acceptance Scenarios**:

1. **Given** a signed-in user, **When** they view the tracker board, **Then** they see columns representing the application lifecycle, with each application placed in its respective column.
2. **Given** a visual column, **When** it contains applications, **Then** the header displays the total count of applications in that column.
3. **Given** an application card in the "Applied" column, **When** the user drags it to "Interviewing", **Then** the status updates in the backend and the card persists in the "Interviewing" column.
4. **Given** an application card, **When** the user drags it to an illegal status transition (e.g. directly from "Saved" to "Offer"), **Then** the UI rejects the transition, returns the card to its original column, and shows a clear validation error.

---

### User Story 2 - Application Details Detail Panel & Activity Timeline (Priority: P2)

A job seeker clicks on an application card to open a slide-over panel or modal displaying the detailed history of that application. They can view a chronological timeline of activities (status changes, emails sent, calls made) and write custom, time-stamped text notes to keep track of conversations, follow-up items, or self-reflections.

**Why this priority**: Job hunting involves dozens of micro-interactions. A central timeline for notes and events is the core "Relationship Management" engine that prevents details from falling through the cracks.

**Independent Test**:
1. Click on a job application card to open its detail panel.
2. Type a note (e.g., " recruiter reached out for availability next week") and click "Save Note".
3. Verify the note is appended to the timeline with a timestamp.
4. Reload the page, open the card again, and verify the note remains visible.

**Acceptance Scenarios**:

1. **Given** a visible application detail panel, **When** the user enters a note and saves it, **Then** it is successfully added to the timeline database and rendered immediately in reverse-chronological order.
2. **Given** a note created by the user, **When** the user edits or deletes the note, **Then** the timeline is updated instantly and the change is persisted.
3. **Given** an application status change, **When** the status is updated, **Then** the system automatically appends an event to the timeline (e.g., "Moved to Interviewing on [Date]") to track lifecycle history.

---

### User Story 3 - Associated Contacts Management (Priority: P2)

A job seeker records names, roles, emails, phone numbers, and LinkedIn URLs of key stakeholders (recruiters, hiring managers, referrers) directly inside the application's details panel, keeping all communication lines in one organized place.

**Why this priority**: Recruiters and hiring managers change frequently during long interview loops. Associating specific contact profiles directly with the job application is essential for professional tracking.

**Independent Test**:
1. Open the details panel for an application.
2. Click "Add Contact" and enter a name, role ("Recruiter"), and email.
3. Save the contact and verify it appears in the "Contacts" section of the panel.
4. Click the contact to edit its email or add a LinkedIn URL, and verify the edits save.

**Acceptance Scenarios**:

1. **Given** an application details view, **When** a user creates a contact, **Then** the contact is saved and displays with its metadata (Name, Role, Email, Phone, LinkedIn).
2. **Given** an existing contact, **When** the user clicks "Delete", **Then** the contact is removed and the UI updates.
3. **Given** multiple contacts, **When** viewed on the application, **Then** they are all listed clearly under the contacts section.

---

### User Story 4 - Application Tasks & Checklist (Priority: P3)

A job seeker creates checklist items (e.g., "Tailor CV", "Review presentation slides", "Send thank-you email") for a specific job application, checks them off as they are completed, and tracks their completion status.

**Why this priority**: Action items keep the momentum going. While a checklist is very helpful, it builds on top of the visual board and the timeline features.

**Independent Test**:
1. Open the details panel for an application.
2. In the "Tasks" section, add a task "Send thank-you letter".
3. Verify the task appears as unchecked.
4. Click the checkbox to complete the task and verify the UI updates (e.g. strikethrough/gray-out) and the completion status is persisted.

**Acceptance Scenarios**:

1. **Given** an application, **When** a user adds a task, **Then** the task is listed under the checklist.
2. **Given** a task, **When** the user toggles the checkbox, **Then** the status is updated in the database.
3. **Given** completed and uncompleted tasks, **When** the user reloads the application, **Then** the correct checked/unchecked states are loaded.

---

### Edge Cases

- **Unauthorized Details Access**: What happens if a user tries to access notes, contacts, or tasks for an application they don't own by manipulating the API? The backend MUST enforce ownership at the query level (using Supabase RLS and FastAPI dependencies) and return a `404 Not Found` or `403 Forbidden`.
- **Application Deletion**: When an application is deleted, all related timeline notes, contacts, and tasks MUST be cascade-deleted from the database to avoid orphaned records.
- **Empty or Invalid Input**: Notes, contacts, and tasks must be validated. An empty note, empty contact name, or blank task title cannot be saved. Email and URL inputs should have basic format validation.
- **Terminal Status Handling**: Moving applications into closed states (Accepted, Rejected, Withdrawn) should visually place them in a consolidated "Closed" column. Dragging them out of closed states requires user action, with normal status transition validation rules still strictly enforced.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-CRM-001**: The system MUST support a Kanban board page displaying applications in columns based on status: Saved, Applied, Interviewing, Offer, and Closed (collapsing Accepted, Rejected, Withdrawn).
- **FR-CRM-002**: Users MUST be able to change application status by dragging cards between columns or using controls within the application card.
- **FR-CRM-003**: The backend MUST validate that status updates follow allowed status lifecycle transitions.
- **FR-CRM-004**: The system MUST support adding, editing, and deleting notes/activities (type: note, email, call, meeting) linked to a specific application.
- **FR-CRM-005**: Note entries MUST show the date/time they were logged and show a history of edits.
- **FR-CRM-006**: The system MUST support adding, editing, and deleting contact profiles linked to a specific application (including Name, Role, Email, Phone, LinkedIn, Notes).
- **FR-CRM-007**: The system MUST support adding, editing, and deleting checklist tasks linked to a specific application.
- **FR-CRM-008**: The system MUST support toggling a task's completion status.
- **FR-CRM-009**: The system MUST enforce strict user isolation: a user can only view, create, edit, or delete notes, contacts, and tasks for applications they own.
- **FR-CRM-010**: The dashboard MUST include a search input to filter the board's cards by company, role, or contact name.

### Key Entities

- **ApplicationNote** (Activity): A chronological timeline event. Attributes: `id` (UUID), `application_id` (UUID), `user_id` (UUID), `type` (text: note, activity, email, call, interview), `content` (text), `created_at` (timestamptz), `updated_at` (timestamptz).
- **ApplicationContact**: A professional contact related to the application. Attributes: `id` (UUID), `application_id` (UUID), `user_id` (UUID), `name` (text), `role` (text), `email` (text, optional), `phone` (text, optional), `linkedin_url` (text, optional), `notes` (text, optional), `created_at` (timestamptz).
- **ApplicationTask**: A single checklist item. Attributes: `id` (UUID), `application_id` (UUID), `user_id` (UUID), `title` (text), `is_completed` (boolean), `due_date` (timestamptz, optional), `created_at` (timestamptz).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-CRM-001**: A card dragged to a new valid column updates status and updates the UI state in less than 1.5 seconds.
- **SC-CRM-002**: Notes, contacts, and tasks for an application detail panel load and display in less than 500 milliseconds on click.
- **SC-CRM-003**: 100% of associated child records (notes, contacts, tasks) are automatically deleted from the database when their parent application is deleted.
- **SC-CRM-004**: Zero (0%) information leakage: unauthorized requests to read or modify notes/contacts/tasks of another user's application are rejected by RLS.

## Assumptions

- We will utilize Supabase Postgres for data storage, and write SQL migrations to add the `application_notes`, `application_contacts`, and `application_tasks` tables.
- Each table will enable Row Level Security (RLS) with policies checking `auth.uid() = user_id`.
- The user interface will replace the simple flat list on `/tracker` with a visual Kanban board, maintaining responsiveness on mobile (mobile can collapse columns or show a list view).
- HTML5 Drag and Drop APIs or React-dnd will be utilized for desktop card movement without relying on heavy external styling dependencies.
- Submitting notes, contacts, or tasks does not require page reload; the frontend will update state optimistically or re-fetch only the application's related resources.
