Tailor the candidate's **prose sections** (Summary and Skills) to the target job
description and return them as structured JSON. Produce ONLY prose sections here —
each section's content is a single `body` string. Do NOT produce Experience or
Education here.

Rules:
- Use ONLY information present in the original CV. Do not invent skills, metrics,
  or claims.
- Reorder and reword to surface what is most relevant to the job; mirror
  important keywords from the job description where they truthfully apply.
- Produce a `summary` section and, if the CV lists skills, a `skills` section.
- Each section has a short, stable, lowercase `id` (e.g. "summary", "skills"), a
  human `heading`, and a non-empty `body` string.
  - For `summary`, `body` is a short paragraph.
  - For `skills`, put one "Category: comma, separated, items" per line in `body`.
- Set `"changed": true` if you altered the section from the original CV (reworded,
  reordered, trimmed, re-emphasized), or `"changed": false` if carried over
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
      "id": "summary",
      "heading": "Summary",
      "changed": true,
      "body": "Senior backend engineer with 6 years building high-throughput Python and Go services...",
      "explanation": "Reworded to foreground the backend and distributed-systems experience the job description asks for."
    },
    {
      "id": "skills",
      "heading": "Skills",
      "changed": true,
      "body": "Languages: Python, Go, TypeScript\nInfrastructure: AWS, PostgreSQL, Docker",
      "explanation": "Led with the languages and infrastructure the role emphasizes."
    }
  ]
}
