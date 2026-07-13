Produce the **bullet sections** of a senior-tech resume tailored to the target
job description, as structured JSON. Every section's content is a list of bullet
strings. Do NOT produce Experience or Education here (those are separate).

Produce these sections, in this order, using only what the CV supports:
1. `summary` — heading "Career Summary". 3–5 bullets answering, within seconds:
   years of experience by domain, core tech stack, leadership/management scope,
   and company types. This front-loads the strongest, most JD-relevant signals.
2. `impact` — heading "Impact Summary". 4–6 bullets, each the single best
   metric-backed achievement from a major career era (name the company where it
   is impressive). Lead with numbers/scope.
3. `skills` — heading "Technology & Skills Snapshot". One bullet per category,
   each formatted "Category: comma, separated, items" (e.g. "Languages: Python,
   Go, TypeScript"). Mirror the job description's exact tech terms where the CV
   supports them. Include only skills genuinely present in the CV.
4. `languages` — heading "Languages". Include ONLY if the CV lists spoken
   languages; one bullet like "English (Fluent) | Portuguese (Native)". Omit the
   whole section otherwise.

Rules:
- Use ONLY information present in the CV. Never invent skills, metrics, or claims
  — including years of experience, team sizes, revenue, or performance numbers.
  If the CV states a figure (e.g. "5+ years"), copy it exactly; never round it up
  or embellish it. If no number supports a claim, state it qualitatively instead
  of inventing one (e.g. "Experience building..." instead of a fabricated "X
  years").
- Every bullet is specific and non-empty: action + scale + outcome, no waffle.
  Prefer the X-Y-Z form ("Accomplished [X] as measured by [Y] by doing [Z]") —
  but only when the CV actually supports X, Y, and Z.
- Mirror important keywords from the job description where they truthfully apply.
- Each section has a short lowercase `id` (exactly "summary", "impact", "skills",
  "languages"), a `heading`, and a non-empty `bullets` list.
- The JSON example below shows OUTPUT SHAPE ONLY. Its companies, numbers, and
  wording are illustrative placeholders — never copy them into your answer.
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
      "id": "summary",
      "heading": "Career Summary",
      "bullets": [
        "<years-from-CV> of experience in <domain from CV>.",
        "<leadership/management scope, only if the CV states it>."
      ]
    },
    {
      "id": "impact",
      "heading": "Impact Summary",
      "bullets": [
        "<best CV-supported achievement, with its actual metric if the CV has one>.",
        "<second-best CV-supported achievement>."
      ]
    },
    {
      "id": "skills",
      "heading": "Technology & Skills Snapshot",
      "bullets": [
        "<Category from CV>: <items from CV>",
        "<Another category from CV>: <items from CV>"
      ]
    },
    {
      "id": "languages",
      "heading": "Languages",
      "bullets": ["English (Fluent) | Portuguese (Native)"]
    }
  ]
}
