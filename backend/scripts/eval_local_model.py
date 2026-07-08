"""Quality probe for the decomposed CV-tailoring pipeline against a local model.

Runs the three focused sub-calls (contact / prose / experience) through a live
OpenAI-compatible endpoint (local Ollama by default) using the *real* prompt
templates, system prompt, and per-shape validators from the tailoring service —
so a "pass" here means the model's raw output would survive the actual request
path. Reports per-call and overall (all-three-valid) success across N runs.

Usage (with Ollama running and the model pulled):

    uv run python -m scripts.eval_local_model
    EVAL_RUNS=20 AI_MODEL=qwen2.5:7b-instruct uv run python -m scripts.eval_local_model

Exit code is non-zero if any run fails, so it doubles as a smoke gate.
"""

from __future__ import annotations

import asyncio
import os
import time
from collections import Counter

from app.infrastructure.ai.openai_compatible_client import OpenAICompatibleClient
from app.infrastructure.ai.prompts import load_prompt

# Reuse the service's real system prompt, placeholders, and per-shape validators
# so this measures exactly what production validates.
from app.services.cv_tailoring_service import (
    _CV_PLACEHOLDER,
    _JD_PLACEHOLDER,
    _NONE_PLACEHOLDER_TEXT,
    _PREVIOUS_PLACEHOLDER,
    _REFINEMENT_PLACEHOLDER,
    _SYSTEM_PROMPT,
    CVTailoringService,
    _ContactResult,
    _EntrySectionsResult,
    _ProseSectionsResult,
)

_SAMPLE_CV = (
    "Jane Doe\nSenior Software Engineer\n"
    "jane@example.com | +1 555 0100 | linkedin.com/in/janedoe | github.com/janedoe\n"
    "Berlin, Germany (Remote)\n\n"
    "Summary: Backend engineer with 6 years building high-throughput services.\n\n"
    "Experience:\n"
    "- Senior Backend Engineer, Foo Inc (2020-2024): built Python/Go APIs, scaled to 1M req/day, "
    "owned reliability to 99.9% uptime.\n"
    "- Backend Engineer, Bar Corp (2018-2020): payments integrations in Python.\n\n"
    "Skills: Python, Go, TypeScript, PostgreSQL, AWS, Docker, Kubernetes\n\n"
    "Education: BSc Computer Science, State University (2014-2018)"
)
_SAMPLE_JD = (
    "We're hiring a Senior Backend Engineer strong in Python and distributed systems to own our "
    "API platform. PostgreSQL and AWS a plus. You will mentor engineers and drive reliability."
)


def _fill(template: str) -> str:
    return (
        template.replace(_CV_PLACEHOLDER, _SAMPLE_CV)
        .replace(_JD_PLACEHOLDER, _SAMPLE_JD)
        .replace(_PREVIOUS_PLACEHOLDER, _NONE_PLACEHOLDER_TEXT)
        .replace(_REFINEMENT_PLACEHOLDER, _NONE_PLACEHOLDER_TEXT)
    )


async def main() -> int:
    base_url = os.environ.get("AI_BASE_URL", "http://localhost:11434/v1")
    model = os.environ.get("AI_MODEL", "qwen2.5:7b-instruct")
    api_key = os.environ.get("AI_API_KEY", "")
    max_tokens = int(os.environ.get("AI_MAX_TOKENS", "4096"))
    runs = int(os.environ.get("EVAL_RUNS", "20"))

    client = OpenAICompatibleClient(
        base_url=base_url, api_key=api_key, model=model, max_tokens=max_tokens
    )

    tasks = [
        ("contact", _fill(load_prompt("cv_contact")), _ContactResult),
        ("prose", _fill(load_prompt("cv_prose_sections")), _ProseSectionsResult),
        ("experience", _fill(load_prompt("cv_experience")), _EntrySectionsResult),
    ]

    print(f"Endpoint: {base_url}  Model: {model}  Runs: {runs}\n")
    per_call_ok: Counter[str] = Counter()
    overall_ok = 0
    started = time.monotonic()

    for i in range(runs):
        run_all_ok = True
        for label, prompt, validator in tasks:
            raw = await client.generate(system=_SYSTEM_PROMPT, prompt=prompt)
            try:
                # Reuse the service's exact parse/validate path.
                CVTailoringService._parse_json(raw, validator)
                per_call_ok[label] += 1
            except Exception as exc:  # noqa: BLE001 - eval reports, doesn't raise
                run_all_ok = False
                first_line = str(exc).splitlines()[0]
                print(f"  run {i + 1}: [{label}] FAIL: {first_line}")
        if run_all_ok:
            overall_ok += 1

    elapsed = time.monotonic() - started
    print("\nPer-call valid-output rate:")
    for label, _, _ in tasks:
        print(f"  {label:11}: {per_call_ok[label]}/{runs}")
    print(f"\nOverall (all three valid): {overall_ok}/{runs}  ({elapsed:.0f}s total)")
    return 0 if overall_ok == runs else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
