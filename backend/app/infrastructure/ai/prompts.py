"""Loader for versioned prompt templates stored as files.

Prompts live as ``.md`` files next to this module so they can be reviewed and
versioned like any other source, rather than buried as string literals in logic.
"""

from __future__ import annotations

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompt_templates"


def load_prompt(name: str) -> str:
    """Return the text of the prompt template ``<name>.md``."""

    return (_PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")
