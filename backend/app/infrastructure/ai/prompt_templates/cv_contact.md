Extract the candidate's contact header from the CV below and return it as
structured JSON. This is pure extraction — do NOT tailor, reword, or invent
anything. Copy details verbatim from the CV.

Rules:
- `name` is required (the candidate's full name).
- `email`, `phone`, and `location` are strings copied from the CV, or null if the
  CV does not contain them. Never invent contact details.
- `links` is a possibly-empty list of labelled URLs found in the CV (e.g.
  LinkedIn, GitHub, portfolio), each `{ "label", "url" }`. Only include a link
  when its actual URL appears in the CV text; if you can see a label but no URL,
  omit that link entirely rather than guessing or emitting a null URL.

## Original CV

{{CV}}

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
  }
}
