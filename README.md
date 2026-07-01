# Open Application

An open-source platform that helps people apply to open positions.

- **Application tracker** — track the progress and status of every job application in one place.
- **AI CV tailoring** — paste a job description and get your CV tailored to it, powered by Claude.

Built the **Spec-Driven Development (SDD)** way: every feature starts as a written spec, not code.

## Tech stack

| Layer      | Choice                                                              |
| ---------- | ------------------------------------------------------------------ |
| Specs      | [GitHub Spec Kit](https://github.com/github/spec-kit) (`specify`)  |
| Backend    | Python + FastAPI, layered/OOP (clean) architecture                 |
| Frontend   | Next.js + React (TypeScript, App Router)                           |
| Data/Auth  | Supabase (Postgres + Auth + Storage)                               |
| AI         | Anthropic Claude via the `anthropic` Python SDK                    |
| Tooling    | `uv`, `ruff`, `mypy`, `pytest`                                     |

## Repository layout

```
.specify/     Spec Kit memory (constitution) + templates
specs/        Per-feature spec / plan / tasks
backend/      FastAPI service (domain → services → api, infra behind interfaces)
frontend/     Next.js web app
supabase/     Database migrations & config
```

## Getting started

Prerequisites: `git`, `node` 20+, `docker`, and [`uv`](https://docs.astral.sh/uv/).

### Backend

```bash
cd backend
uv sync                       # create venv + install deps
cp .env.example .env          # fill in Supabase + Anthropic keys
uv run uvicorn app.main:app --reload
# API docs at http://localhost:8000/docs
```

Quality gates:

```bash
uv run pytest        # unit tests run against fakes — no network needed
uv run ruff check .
uv run mypy app
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev           # http://localhost:3000
```

### Supabase (local)

```bash
npx supabase start    # local Postgres + Auth + Storage
npx supabase db reset # apply migrations in supabase/migrations
```

## How we build features (SDD)

We use GitHub Spec Kit. In Claude Code:

1. `/speckit.constitution` — the project's non-negotiable principles (already seeded).
2. `/speckit.specify` — write the spec for a feature.
3. `/speckit.plan` — technical plan for that spec.
4. `/speckit.tasks` — break the plan into tasks.
5. `/speckit.implement` — implement against the tasks.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## License

[MIT](LICENSE)
