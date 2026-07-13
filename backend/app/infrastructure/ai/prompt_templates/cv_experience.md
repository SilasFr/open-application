Produce the **Experience and Education** sections of a senior-tech resume
tailored to the target job description, as structured JSON. Each section is a
list of `entries`. Do NOT produce a Career Summary, Impact, Skills, or Languages
section here, and do NOT use free-form prose — every item is a structured entry.

Sections (use only what the CV supports):
- `experience` — heading "Professional Experience". One entry per role, most
  recent first. 4–6 bullets for recent/relevant roles, 2–3 for older ones.
- `education` — heading "Education & Certifications". One entry per degree or
  certification. Bullets may be empty. Include only if the CV has education.

Rules:
- Use ONLY information present in the CV. Never invent roles, employers, degrees,
  dates, or metrics — including team sizes, revenue, percentages, or scale
  figures the CV does not state. Copy any number from the CV exactly, never
  round or embellish it.
- Each entry is `{ "title", "organization", "date_range", "context", "bullets" }`:
  - `title` (required) — the role or degree.
  - `organization` — company or school, or null.
  - `date_range` — a human string like "Feb 2026 – May 2026", or null.
  - `context` — a one-line company descriptor (stage, size, domain) when the
    employer may be unfamiliar to a recruiter and the CV supports it, else null.
  - `bullets` — accomplishment strings grounded in the CV. Lead each with a
    strong verb (Architected, Led, Scaled, Drove, Built 0->1). Include a metric
    or concrete scope ONLY when the CV states one; otherwise describe the
    action and outcome without inventing a number. No waffle ("responsible
    for", "worked on", "helped with").
- Each section has a lowercase `id` (exactly "experience" or "education"), a
  `heading`, and a non-empty `entries` list.
- The JSON example below shows OUTPUT SHAPE ONLY. Its company, dates, and
  numbers are illustrative placeholders — never copy them into your answer.
  Every fact in your output must trace back to the CV above.

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
      "entries": [
        {
          "title": "<title from CV>",
          "organization": "<organization from CV, or null>",
          "date_range": "<date range from CV, or null>",
          "context": "<one-line descriptor, only if CV supports it, else null>",
          "bullets": [
            "<CV-grounded accomplishment, with its real metric if the CV has one>",
            "<second CV-grounded accomplishment>"
          ]
        }
      ]
    },
    {
      "id": "education",
      "heading": "Education & Certifications",
      "entries": [
        {
          "title": "<degree/certification from CV>",
          "organization": "<school from CV, or null>",
          "date_range": "<date range from CV, or null>",
          "context": null,
          "bullets": []
        }
      ]
    }
  ]
}
