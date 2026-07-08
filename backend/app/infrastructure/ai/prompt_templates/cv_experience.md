Tailor the candidate's **Experience and Education** to the target job description
and return them as structured JSON. Produce ONLY these structured sections here —
each section is a list of `entries`. Do NOT produce a Summary or Skills section,
and do NOT use free-form prose; every item is a structured entry.

Rules:
- Use ONLY information present in the original CV. Do not invent roles, employers,
  degrees, dates, or metrics.
- Reorder and reword to surface the experience most relevant to the job; mirror
  important keywords from the job description where they truthfully apply.
- Produce an `experience` section and, if the CV lists education, an `education`
  section. Each section has a short, stable, lowercase `id`, a human `heading`,
  and a non-empty `entries` list (at least one entry).
- Each entry is `{ "title", "organization", "date_range", "context", "bullets" }`:
  - `title` (required) — the role or degree.
  - `organization` — company or school, or null.
  - `date_range` — a human string like "Feb 2026 – May 2026", or null.
  - `context` — an optional one-line note, or null.
  - `bullets` — a list of accomplishment strings (may be empty for education).
- Set `"changed": true` if you altered the section from the original CV (reordered
  roles, reworded bullets, re-emphasized), or `"changed": false` if carried over
  unchanged. `changed` must be `true` or `false`, never null.
- Every section with `"changed": true` MUST include a non-empty, human-readable
  `"explanation"` of what changed and why (referencing the job description where
  relevant). Sections with `"changed": false` MUST have `"explanation": null`.

## Original CV

{{CV}}

## Target job description

{{JOB_DESCRIPTION}}

## Prior tailored version (present only when refining a previous result; otherwise "(none)")

{{PREVIOUS_TAILORED_CV}}

## Refinement instructions (present only when refining a previous result; otherwise "(none)")

{{REFINEMENT_INSTRUCTIONS}}

If refinement instructions are present, treat the prior tailored version as your
starting point and apply the instructions on top of it, still honoring the rules
above and the original CV as ground truth.

## Output format

Return ONLY a single JSON object shaped exactly like this — no markdown code
fences, no preamble, no commentary, no trailing text:

{
  "sections": [
    {
      "id": "experience",
      "heading": "Professional Experience",
      "changed": true,
      "entries": [
        {
          "title": "Senior Backend Engineer",
          "organization": "Foo Inc",
          "date_range": "2020 – 2024",
          "context": "High-scale fintech APIs",
          "bullets": [
            "Built Python/Go services scaling to 1M requests/day.",
            "Owned service reliability, reaching 99.9% uptime."
          ]
        }
      ],
      "explanation": "Led with the most relevant role and emphasized scale metrics the job calls out."
    },
    {
      "id": "education",
      "heading": "Education",
      "changed": false,
      "entries": [
        {
          "title": "BSc Computer Science",
          "organization": "State University",
          "date_range": "2014 – 2018",
          "context": null,
          "bullets": []
        }
      ],
      "explanation": null
    }
  ]
}
