# Contributing to Open Application

Thanks for helping build Open Application! This project follows **Spec-Driven Development
(SDD)** — code is a consequence of a spec, never the starting point.

## The golden rule

**No feature code is merged without a spec.** Every change that adds or alters behavior must
have a corresponding `specs/<feature>/spec.md` (and usually `plan.md` + `tasks.md`) committed
first or in the same PR.

## Branch-per-feature

`main` stays releasable. **Every feature is built on its own branch, and the branch name
matches its Spec Kit feature id** — a zero-padded number plus a slug, e.g.
`001-mvp-tracker-cv-tailoring`. That one name is shared by three things:

- the git branch,
- the spec folder `specs/001-mvp-tracker-cv-tailoring/`,
- the feature id Spec Kit tracks in `.specify/feature.json`.

Start a feature with the helper, which creates the spec folder **and** the matching branch in
one step (keeping the names in sync automatically):

```bash
scripts/new-feature.sh "Import a resume from a PDF"
# or force a slug:
scripts/new-feature.sh --short-name "resume-import" "Import a resume from a PDF"
```

Work the feature to completion on that branch, then open a **pull request into `main`**. The
spec, plan, tasks, and implementation all land together in that PR.

## The workflow (GitHub Spec Kit)

We use [Spec Kit](https://github.com/github/spec-kit). Read
[`.specify/memory/constitution.md`](.specify/memory/constitution.md) first — it governs every
plan and implementation. Then, from Claude Code (on your feature branch):

1. **`scripts/new-feature.sh "<description>"`** — creates `specs/<id>/spec.md` and the `<id>`
   branch. (Equivalent to `/speckit-specify` plus cutting the branch.)
2. **`/speckit-plan`** — the technical approach for that spec.
3. **`/speckit-tasks`** — an ordered, reviewable task list.
4. **`/speckit-implement`** — build it, honoring the constitution.
5. Open a PR into `main`.

To change the project's guiding principles, run **`/speckit-constitution`** (updates
`.specify/memory/constitution.md`) on its own branch.

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
