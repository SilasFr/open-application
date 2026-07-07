"""Quality probe for a local/open CV-tailoring model.

Runs a few CV + job-description pairs through a live OpenAI-compatible endpoint
(local Ollama by default) using the *real* system prompt, template, and
structured-output validation from the tailoring service — so a "pass" here means
the model's raw output would survive the actual request path.

Usage (with Ollama running and the model pulled):

    uv run python -m scripts.eval_local_model
    AI_BASE_URL=http://localhost:11434/v1 AI_MODEL=qwen2.5:7b-instruct \\
        uv run python -m scripts.eval_local_model

Exit code is non-zero if any case fails validation, so it doubles as a smoke gate.
"""

from __future__ import annotations

import asyncio
import json
import os
import time

from pydantic import ValidationError

from app.infrastructure.ai.openai_compatible_client import OpenAICompatibleClient
from app.infrastructure.ai.prompts import load_prompt
from app.services.cv_tailoring_service import (
    _CV_PLACEHOLDER,
    _JD_PLACEHOLDER,
    _NONE_PLACEHOLDER_TEXT,
    _PREVIOUS_PLACEHOLDER,
    _REFINEMENT_PLACEHOLDER,
    _SYSTEM_PROMPT,
    _StructuredOutputModel,
)

# A couple of small, realistic CV/JD pairs. Enough to catch JSON-shape and
# instruction-following regressions without a full benchmark.
_CASES: list[tuple[str, str, str]] = [
    (
        "backend engineer",
        "Jane Doe\nSoftware Engineer\n\nExperience:\n"
        "- Backend Engineer, Foo Inc (2020-2024): built Python/Go APIs, scaled to 1M req/day.\n"
        "- Frontend Engineer, Bar Corp (2018-2020): React dashboards.\n\n"
        "Skills: Python, Go, React, TypeScript, AWS, PostgreSQL",
        "We're hiring a Senior Backend Engineer strong in Python and distributed "
        "systems to own our API platform. PostgreSQL and AWS a plus.",
    ),
    (
        "data analyst",
        "John Smith\nAnalyst\n\nExperience:\n"
        "- Data Analyst, Acme (2021-2024): SQL reporting, Tableau dashboards, A/B tests.\n\n"
        "Skills: SQL, Python, Tableau, statistics",
        "Seeking a Data Analyst comfortable with SQL and experimentation to drive "
        "product decisions. Dashboarding experience required.",
    ),
]


def _build_prompt(template: str, cv_text: str, job_description: str) -> str:
    """Mirror CVTailoringService._build_prompt for the no-refinement case."""
    return (
        template.replace(_CV_PLACEHOLDER, cv_text)
        .replace(_JD_PLACEHOLDER, job_description)
        .replace(_PREVIOUS_PLACEHOLDER, _NONE_PLACEHOLDER_TEXT)
        .replace(_REFINEMENT_PLACEHOLDER, _NONE_PLACEHOLDER_TEXT)
    )


async def main() -> int:
    base_url = os.environ.get("AI_BASE_URL", "http://localhost:11434/v1")
    model = os.environ.get("AI_MODEL", "qwen2.5:7b-instruct")
    api_key = os.environ.get("AI_API_KEY", "")
    max_tokens = int(os.environ.get("AI_MAX_TOKENS", "4096"))

    client = OpenAICompatibleClient(
        base_url=base_url, api_key=api_key, model=model, max_tokens=max_tokens
    )
    template = load_prompt("cv_tailoring_structured")

    print(f"Endpoint: {base_url}  Model: {model}\n")
    failures = 0
    for label, cv_text, jd in _CASES:
        prompt = _build_prompt(template, cv_text, jd)
        started = time.monotonic()
        try:
            raw = await client.generate(system=_SYSTEM_PROMPT, prompt=prompt)
        except Exception as exc:  # noqa: BLE001 - eval script reports, doesn't raise
            failures += 1
            print(f"[FAIL] {label}: request error: {exc}")
            continue
        elapsed = time.monotonic() - started

        try:
            parsed = _StructuredOutputModel.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValidationError) as exc:
            failures += 1
            print(f"[FAIL] {label}: invalid structured output ({elapsed:.1f}s): {exc}")
            print(f"       raw (first 200 chars): {raw[:200]!r}")
            continue

        changed = sum(1 for s in parsed.sections if s.changed)
        print(
            f"[PASS] {label}: {len(parsed.sections)} sections "
            f"({changed} changed) in {elapsed:.1f}s"
        )

    print(f"\n{len(_CASES) - failures}/{len(_CASES)} passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
