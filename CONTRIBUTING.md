# Contributing to Open Application

Thanks for helping build Open Application! This project follows **Spec-Driven Development
(SDD)** — code is a consequence of a spec, never the starting point.

## The golden rule

**No feature code is merged without a spec.** Every change that adds or alters behavior must
have a corresponding `specs/<feature>/spec.md` (and usually `plan.md` + `tasks.md`) committed
first or in the same PR.

## The workflow (GitHub Spec Kit)

We use [Spec Kit](https://github.com/github/spec-kit). From Claude Code:

1. **`/speckit.constitution`** — the project's non-negotiable principles. Read
   [`.specify/memory/constitution.md`](.specify/memory/constitution.md) before you start; it
   governs every plan and implementation.
2. **`/speckit.specify`** — describe *what* and *why* (not *how*). Produces `specs/<n>/spec.md`.
3. **`/speckit.plan`** — the technical approach for that spec.
4. **`/speckit.tasks`** — an ordered, reviewable task list.
5. **`/speckit.implement`** — build it, honoring the constitution.

## Architecture rules (enforced by the constitution)

- **Layered / OOP backend.** Route handlers stay thin. Business logic lives in **service
  classes**. Persistence sits behind **repository interfaces** (`app/domain/repositories.py`);
  concrete Supabase implementations live in `app/infrastructure/`.
- **Depend on interfaces, not vendors.** Services receive repositories and the `AIClient` by
  dependency injection so they can be unit-tested against fakes with no network.
- **Typed and tested.** Full type hints (`mypy` clean). Every service has `pytest` unit tests
  against in-memory fakes.
- **AI is abstracted.** All Claude calls go through the single `AIClient` interface. Prompts
  are versioned files under `app/infrastructure/ai/prompts/`, and model IDs are configuration.

## Before you open a PR

```bash
# backend
cd backend && uv run ruff check . && uv run mypy app && uv run pytest
# frontend
cd frontend && npm run lint && npm run build
```

- No secrets in the repo. Keep `.env.example` files up to date when you add config.
- Keep the spec and the code in sync — if the implementation diverges, update the spec.
