Tailor the candidate's CV below to the target job description and return the
result as **structured JSON**: a contact header plus a list of sections.

Rules:
- Use ONLY information present in the original CV. Do not invent roles, skills, dates, metrics, or contact details.
- Reorder and reword to surface the experience most relevant to the job.
- Mirror important keywords from the job description where they truthfully apply.
- Extract the candidate's contact details into `contact` (name, email, phone, location, and labelled links such as LinkedIn/GitHub). `name` is required; set any detail absent from the CV to null. `links` is a possibly-empty list of `{ "label", "url" }`.
- Break the tailored CV into logical sections (e.g. Summary, Experience, Skills, Education).
- Give each section a short, stable, lowercase `id` (e.g. "summary", "experience", "skills").
- Each section carries its content in EITHER `body` OR `entries`:
  - Prose sections (Summary, Skills) use `body`: a single string. For Skills, put one "Category: comma, separated, items" per line. Leave `entries` as `[]`.
  - Structured sections (Experience, Education) use `entries`: a list of items, and set `body` to null. Each entry is `{ "title", "organization", "date_range", "context", "bullets" }` where `title` is required (role or degree), `organization` is the company/school (or null), `date_range` is a human string like "Feb 2026 – May 2026" (or null), `context` is an optional one-line note (or null), and `bullets` is a list of accomplishment strings.
- Every section MUST have a non-empty `heading`, a lowercase non-empty `id`, and `changed` set to `true` or `false` (never null). A section MUST have a non-empty `body` OR at least one entry — never both empty.
- Set `"changed": true` on a section you altered from the original CV (reworded, reordered, trimmed, or re-emphasized), or `"changed": false` if it is carried over unchanged.
- Every section with `"changed": true` MUST include a non-empty, human-readable `"explanation"` of what changed and why (referencing the job description where relevant). Sections with `"changed": false` MUST have `"explanation": null`.

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
  "contact": {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+1 555 0100",
    "location": "Berlin, Germany (Remote)",
    "links": [
      { "label": "LinkedIn", "url": "https://linkedin.com/in/janedoe" },
      { "label": "GitHub", "url": "https://github.com/janedoe" }
    ]
  },
  "sections": [
    {
      "id": "summary",
      "heading": "Summary",
      "changed": true,
      "body": "Senior backend engineer with 6 years building high-throughput Python and Go services...",
      "entries": [],
      "explanation": "Reworded to foreground the backend and distributed-systems experience the job description asks for."
    },
    {
      "id": "experience",
      "heading": "Professional Experience",
      "changed": true,
      "body": null,
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
    }
  ]
}
