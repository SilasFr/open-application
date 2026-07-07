Tailor the candidate's CV below to the target job description and return the
result as **structured JSON** describing each section of the tailored CV.

Rules:
- Use ONLY information present in the original CV. Do not invent roles, skills, dates, or metrics.
- Reorder and reword to surface the experience most relevant to the job.
- Mirror important keywords from the job description where they truthfully apply.
- Break the tailored CV into logical sections (e.g. Summary, Experience, Skills, Education).
- Give each section a short, stable, lowercase `id` (e.g. "summary", "experience", "skills").
- On every section, `id`, `heading`, and `body` MUST be non-empty strings and
  `changed` MUST be `true` or `false` — never null or omitted, even for a
  carried-over/unchanged section. `explanation` is the ONLY field that may be null.
- For each section, set `"changed": true` if you altered it from the original CV
  (reworded, reordered, trimmed, or re-emphasized), or `"changed": false` if it is
  carried over unchanged.
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
      "body": "Full text of this section, as it should appear in the tailored CV.",
      "changed": true,
      "explanation": "Reworded to foreground backend experience the job description asks for."
    }
  ]
}
