# Handoff: Tracker & Tailor-CV Redesigns (Open Application)

**How to use with spec-driven development:** treat this bundle as the *design input* to your spec phase — not as tasks or code. Feed this README (and the `reference/` prototypes) to Claude Code when writing/updating the spec for each feature, then let your normal SDD flow generate requirements, plan, and tasks from it. One spec per feature is the natural split:

1. `tracker-redesign` — rework of `frontend/src/app/tracker/page.tsx` + related components
2. `tailor-cv-redesign` — rework of `frontend/src/app/tailor/page.tsx`

## About the design files

Files in `reference/` are **HTML/React design prototypes**, not production code. They mock data in memory and simulate uploads/AI generation. The task is to **recreate the designs inside the existing Next.js codebase** (`frontend/`, app router, Tailwind, `lib/api.ts`, dnd-kit already in use for the Kanban) following its established patterns. Do not copy the prototype files in.

`styles.css` + `tokens/` contain the design system's CSS custom properties. All colors/spacing/type below reference those variables; map them to your Tailwind config or import the token files.

## Fidelity

**High-fidelity.** Layout, spacing, color tokens, copy, and interaction behavior are final intent. Recreate faithfully using existing components where they match.

---

# Feature 1 — Application Tracker redesign

Reference: `reference/tracker_redesign.html` (+ `tracker-redesign-components.jsx`, `tracker-redesign-panel.jsx`)
Target: `frontend/src/app/tracker/page.tsx`, `KanbanBoard.tsx`, `ApplicationDetailPanel.tsx`, `ApplicationCard.tsx`, `SearchBar.tsx`

## Overview

Replaces the bare tracker with: summary stats strip, search + filters toolbar, add-application modal (replacing the permanent inline form), polished Kanban with legal-move affordances and stale indicators, and an upgraded slide-over detail panel.

## Page layout

- Max width `80rem`, centered, padding `32px 24px 48px`; page background `var(--gradient-page)` with fixed `var(--glow-accent)` overlay.
- Vertical order: header row (title + primary "＋ Add application" button, space-between, wrap) → stats strip (`margin-top 24px`) → toolbar (`margin-top 16px`) → board (`margin-top 20px`, horizontal scroll allowed).

## Stats strip

Single card (`--surface-card` bg, `--border-default` border, `--radius-lg`, `--shadow-sm`), 5 equal `flex:1` cells divided by 1px borders, each `padding 12px 20px`:
- **Active** — count of status ∈ {saved, applied, interviewing, offer}
- **Interviewing** — count of `interviewing`
- **Offers** — count of status ∈ {offer, accepted}
- **Response rate** — round(interviewing+offer+accepted ÷ everything except `saved` × 100)%, `0%` when denominator 0
- **Need attention** — count of stale active apps (see Staleness); value colored `var(--status-interviewing-text)` when > 0
Cell: value in `--font-display`, `--text-2xl`, bold, tight tracking; label `--text-xs` `--text-secondary`.

## Toolbar

Flex row, gap 8, wrapping: search input (`flex:1 1 240px`, min 200px, ⌕ glyph absolutely positioned left, `padding-left 32px`) + two selects (status: All statuses / each status; date added: any / last 7 / last 30 days). Inputs use `--surface-input` bg, `--border-input`, `--radius-md`, `--text-sm`, padding `8px 12px`. Filtering is client-side over company+role substring (case-insensitive), status equality, and `created_at` age.

## Board

5 columns — Saved, Applied, Interviewing, Offer, **Closed** (Closed aggregates accepted/rejected/withdrawn). Columns `flex:1 1 0`, `min-width 200px`, gap 12 (contained style) / 24 (open style).

Column (default "contained" style): `border 1px --border-default`, bg `rgb(148 163 184 / 0.04)`, `--radius-lg`, padding 12. Header row: uppercase `--text-xs` semibold label with 7px status-dot (`--status-<s>-dot`) + count pill (`--badge-count-bg`/`--badge-count-text`, `--radius-full`). Empty column shows "Nothing here yet." in `--text-xs` `--text-tertiary`.
"Open" layout variant (user-preferred in prototype tweaks): transparent columns, no border/bg, header separated by 1px bottom border, gap 24.

Card: `--surface-card` bg, `--border-default` border, `--radius-lg`, `--shadow-sm`, padding `var(--padding-card)`; role (`--text-sm` medium) over company (`--text-sm` `--text-secondary`), then meta line (`--text-xs`): "Updated {relative}" in `--text-tertiary`, or stale message (below). Hover: border `rgb(163 230 53 / 0.5)` + `--shadow-glow`, 150ms ease.

### Drag & drop (keep dnd-kit)

Allowed transitions (existing domain rules — enforce, don't relax):
- saved → applied, withdrawn
- applied → interviewing, rejected, withdrawn
- interviewing → offer, rejected, withdrawn
- offer → accepted, rejected, withdrawn
- accepted/rejected/withdrawn → none

While dragging: columns that can't legally receive the card dim to 45% opacity; a legal column under the pointer gets bg `rgb(132 204 22 / 0.10)` and border `rgb(163 230 53 / 0.5)`; the dragged card renders at 40% opacity. Dropping on Closed maps to the first legal closed status for the card. Illegal drop → inline error text (`--text-error`): "That move isn't allowed for this application's status." Any successful move updates `last_activity`.

### Staleness

An app is stale when status is active (saved/applied/interviewing/offer) and no activity for ≥ 7 days. Card shows an 8px `--status-interviewing-dot` dot top-right and meta line "No activity in {n}d" in `--status-interviewing-text`.

## Add application modal

Primary button opens a centered dialog (max-width `26rem`, `--gradient-panel` bg + 12px blur, `--radius-xl`, `--shadow-lg`, padding 24, `--surface-overlay` backdrop that closes on click). Fields: Company, Role, starting status select (Saved | Applied only). Footer right-aligned: ghost Cancel + primary "Add application" (disabled until both fields non-empty). Autofocus first field. Creates via existing `api` with `last_activity = created_at = now`.

## Detail panel (slide-over)

Right-anchored, max-width `30rem`, full height, `--gradient-panel` + blur, left border, scrollable; overlay click and Escape close it.

- **Sticky header**: role (`--text-lg` semibold) + "{company} · added {relative}"; Close text-button. Below: current-status badge (pill with dot, `--status-<s>-bg/border/text/dot`) + one pill button per legal transition, labeled "→ {Status}" — one-tap move (replaces the old dropdown). If stale, a nudge line: "No activity in {n} days. Add a note or task to keep it moving."
- **Timeline** section: inline add-note input + Add button; entries newest-first in bordered boxes with "{Type} · {relative}" meta.
- **Contacts** section: rows with 32px initials avatar (`--badge-count-bg`), name, "role · email", optional "LinkedIn →" link (`--text-link`).
- **Tasks** section: count pill shows *open* tasks; inline add input; checkbox rows (accent `#a3e635`), completed = line-through + `--text-tertiary`.

## State

Client state: apps list, selected app (panel), add-modal open, query, statusFilter ('all'|status), ageFilter ('any'|'7'|'30'), dragging app id. Notes/contacts/tasks keyed by application id (existing API shapes). Relative time: today / yesterday / "{n}d ago".

---

# Feature 2 — Tailor my CV redesign

Reference: `reference/tailor_redesign.html` (+ `tailor-components.jsx`, `tailor-result.jsx`)
Target: `frontend/src/app/tailor/page.tsx`

## Overview

Replaces the two-textarea form with a wizard: (1) upload a base resume **once, persisted**, (2) provide a job description, (3) progress narrative while generating, (4) result view — tailored resume with changed sections marked, side panel explaining each change, and actions (download, copy, save to a tracker application, refine).

## Flow / state machine

`phase: 'resume' | 'jd' | 'working' | 'result'`. If a saved base resume exists, land directly on `jd`. Step indicator (Base resume → Job description → Result) top-right: done = accent-filled check circle, current = `--badge-count-bg` circle, upcoming = bordered.

- **Step 1 — Base resume**: heading + "Upload it once — we keep it saved so you can tailor for any job in seconds." Dashed drop zone (1.5px dashed `--border-input`, `--radius-lg`, hover/dragover bg `rgb(132 204 22 / 0.10)` + accent border): "Drop your resume here, or click to browse" / "PDF or DOCX, up to 5 MB". After upload → compact chip: 36px "PDF" square, filename (ellipsized), "Saved to your account", Replace + Remove text-buttons. Continue (primary, disabled until present). **Persistence**: prototype uses localStorage; in the real app store server-side per user (the resume file + parsed text) so it survives sessions/devices.
- **Step 2 — JD**: 9-row textarea ("Paste the job description…") plus a secondary drop zone for a JD file; saved-resume chip shown above the form. Back (ghost) / "Tailor my resume" (primary, disabled while empty).
- **Working**: centered checklist (max-width 26rem) stepping ~900ms per line through: Reading job description… / Extracting key requirements… / Matching your experience… / Rewriting for relevance… / Finalizing your tailored resume… Done lines get accent check circles; current line pulses. In the real app, drive from actual request lifecycle (or keep as narrative if the API is single-shot).
- **Result** (page widens to `80rem`): action bar, then hint line "Highlighted sections were changed — click one (or a card) to see why.", then two panes gap 20.

## Result view

- **CV pane** (`flex:1`, card surface, padding `24px 28px`): resume rendered as sections; changed sections get a 2px left accent edge `rgb(163 230 53 / 0.4)`; section headings `--text-xs` semibold wide-tracked `--text-tertiary`; body `--text-sm`, relaxed leading, pre-wrap.
- **Reasoning pane** (`flex:0 0 20rem`, sticky top 24): "What changed & why" + count pill; one card per change (title `--text-sm` medium + detail `--text-xs` `--text-secondary`).
- **Cross-highlighting**: selecting a reasoning card (or clicking a changed section) highlights both with bg `rgb(132 204 22 / 0.10)` and accent border; click again to clear. The API response must therefore return **structured output**: sections with changed flags + change explanations referencing section ids — worth capturing as a requirement on the backend contract (extends current `api.tailorCV`).

## Actions

- **Download PDF** (primary), **Download DOCX** (ghost) — generated artifacts.
- **Copy text** — plain-text of tailored resume; button reads "Copied ✓" for 1.5s.
- **Save to application** — popover (240px, panel surface) listing the user's tracker applications; choosing one attaches the tailored resume to it and button becomes "Saved to {company} ✓". Ties into tracker data.
- **Refine…** — reveals inline input ("e.g. Keep it to one page, emphasize leadership more…") + Regenerate (primary); submits note + reruns generation (back to working phase).
- **Start over** — text-button; clears JD, returns to step 2 (resume stays saved).

---

# Design tokens (shared)

All from `styles.css` + `tokens/` (dark theme, `class="oa-dark"`). Key ones used here:

- Surfaces: `--gradient-page` (page bg) + `--glow-accent` overlay, `--surface-card`, `--surface-input`, `--surface-overlay`, `--gradient-panel` (modals/panels, with 12px backdrop blur)
- Borders: `--border-default`, `--border-input`; radii `--radius-md/lg/xl/full`
- Text: `--text-primary/secondary/tertiary/link/error`; fonts `--font-sans` body, `--font-display` headings/stat values; sizes `--text-xs` → `--text-3xl`
- Accent (lime): `--fill-primary` + `--fill-primary-text` + `--shadow-glow` for primary buttons; interaction accents use raw `rgb(132 204 22 / 0.10)` bg and `rgb(163 230 53 / 0.4–0.6)` borders; checkbox accent `#a3e635`
- Status: `--status-<saved|applied|interviewing|offer|accepted|rejected|withdrawn>-<bg|border|text|dot>`; count pills `--badge-count-bg/text`
- Shadows: `--shadow-sm` cards, `--shadow-lg` overlays, `--shadow-glow` primary/hover
- Motion: 150ms ease on hover/drag affordances; respect `prefers-reduced-motion` for the pulse animation

## Assets

None — no images or icon fonts. The ⌕, ✓, ●, →, ＋, × glyphs are plain text.

## Files

- `reference/tracker_redesign.html` — tracker page prototype (open in a browser; Tweaks values: boardStyle "open" was user-preferred)
- `reference/tracker-redesign-components.jsx` — stats strip, card, column, add modal, transition rules (`TR_ALLOWED`), staleness helpers
- `reference/tracker-redesign-panel.jsx` — detail slide-over
- `reference/tailor_redesign.html` — tailor wizard prototype
- `reference/tailor-components.jsx` — step dots, resume chip, drop zone, progress narrative, mock data
- `reference/tailor-result.jsx` — result view with reasoning panel + actions
- `styles.css`, `tokens/` — design-system tokens
