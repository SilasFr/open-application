# 007 — Rich resume rendering

## Why

The downloadable tailored CV was rendered from a flat list of `{heading, body}`
sections into a plain, unstyled PDF/DOCX. Users want a polished, well-formatted
resume (contact header, dated experience entries, styled section rules) worth
sending to employers — comparable to a hand-built HTML/CSS resume.

## Decisions

- **Engine: reportlab (pure-Python).** Keeps the backend free of native system
  dependencies, so the Render deploy needs no Docker/apt change. Produces a
  single-column A4 layout with a centred name header, indigo section headings +
  underline rules, bold role titles with right-aligned date ranges, italic
  context lines, and justified bullet lists. (WeasyPrint would give exact
  HTML/CSS fidelity but requires Pango/cairo native libs — rejected for the
  deployment cost.)
- **Enriched structured output.** The AI now returns a `contact` block plus
  sections that carry EITHER prose `body` (Summary, Skills) OR a list of
  structured `entries` (Experience, Education), each with
  `title / organization / date_range / context / bullets`. This is what lets the
  PDF look like a real resume rather than heading+paragraph blocks. The
  `changed` / `explanation` mechanism is unchanged.

## Data model

- `TailoredCV.contact`: `{ name, email?, phone?, location?, links[] {label,url} }`
  (nullable; new `contact jsonb` column on `tailored_cvs`).
- `TailoredCVSection`: `{ id, heading, changed, body?, entries[], explanation? }`
  — at least one of `body`/`entries` is populated (enforced in validation).
- `TailoredCVEntry`: `{ title, organization?, date_range?, context?, bullets[] }`
  (stored inside the existing `sections` jsonb — no new column).

Backward-compatible: old rows (body-only sections, no contact) still deserialize.

## Verification

- Unit: validation (body-or-entries rule, changed-needs-explanation), rendering
  (contact + entries → valid PDF/DOCX bytes), repo round-trip.
- Visual: sample render matches the target layout.
- Live: tailor against a model → download PDF → inspect styling (requires the
  `contact` column migration applied to the project).
