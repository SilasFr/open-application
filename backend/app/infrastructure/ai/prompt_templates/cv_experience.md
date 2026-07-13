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
  dates, or metrics.
- Each entry is `{ "title", "organization", "date_range", "context", "bullets" }`:
  - `title` (required) — the role or degree.
  - `organization` — company or school, or null.
  - `date_range` — a human string like "Feb 2026 – May 2026", or null.
  - `context` — a one-line company descriptor (stage, size, domain) when the
    employer may be unfamiliar to a recruiter, else null.
  - `bullets` — accomplishment strings. Lead each with a strong verb
    (Architected, Led, Scaled, Drove, Built 0->1); most bullets carry a metric
    or concrete scope (team size, users, %, revenue, scale). Prefer the X-Y-Z
    form. Mirror the job description's exact terminology where it truthfully
    applies. No waffle ("responsible for", "worked on", "helped with").
- Each section has a lowercase `id` (exactly "experience" or "education"), a
  `heading`, and a non-empty `entries` list.

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
          "title": "Senior Backend Engineer",
          "organization": "Foo Inc",
          "date_range": "2020 – 2024",
          "context": "Series B fintech, 150-person engineering org",
          "bullets": [
            "Architected the payments platform to 1M requests/day, cutting p99 latency 40%.",
            "Led a team of 6 engineers, reaching 99.9% uptime under Prime Day peaks."
          ]
        }
      ]
    },
    {
      "id": "education",
      "heading": "Education & Certifications",
      "entries": [
        {
          "title": "BSc Computer Science",
          "organization": "State University",
          "date_range": "2014 – 2018",
          "context": null,
          "bullets": []
        }
      ]
    }
  ]
}
