# Open Application Constitution

The non-negotiable principles governing every spec, plan, and implementation in this
project. When a plan or change conflicts with this document, this document wins.

## Core Principles

### I. Spec-First (NON-NEGOTIABLE)
No feature code is written or merged without a spec. Every behavior-changing contribution
has a `specs/<feature>/spec.md` describing *what* and *why* before any *how*. Plans and
tasks derive from the spec; if the implementation diverges, the spec is updated in the same
change. Code is a consequence of a spec, never the starting point.

### II. Layered OOP Architecture
The backend is organized in inward-pointing layers: `api → services → domain`, with
`infrastructure` implementing domain-owned interfaces.
- **Route handlers stay thin** — they parse/validate input, call one service, and shape the
  response. No business logic in handlers.
- **Business logic lives in service classes** under `app/services/`.
- **The domain layer is pure** — entities, value objects, and repository interfaces in
  `app/domain/` import no web framework, no SDK, no database driver.

### III. Dependency Inversion (depend on interfaces, not vendors)
Services depend on abstractions, never on concrete vendors. Persistence sits behind
repository interfaces (ABCs / `Protocol`) declared in `app/domain/repositories.py`;
Supabase-specific code lives only in `app/infrastructure/`. All AI calls go through a single
`AIClient` interface — no service imports any LLM vendor SDK (`anthropic`, `google-genai`, …)
directly. Dependencies are injected (composition root in `app/core/dependencies.py`) so any
implementation is swappable.

### IV. Typed and Tested
Full type hints on all Python code; `mypy` must be clean. Every service/use-case has `pytest`
unit tests exercised against **in-memory fakes** of the repository and `AIClient` interfaces —
unit tests run with no network and no live Supabase or AI-provider calls. Route contracts are
covered by API tests via FastAPI's `TestClient`.

### V. AI is Abstracted and Configurable
Every LLM interaction flows through the `AIClient` abstraction. Prompts are versioned files
under `app/infrastructure/ai/prompts/`, never inline string literals scattered in logic. The
AI provider, model IDs, temperatures, and limits are configuration (`Settings`), not hardcoded —
selectable per environment (`AI_PROVIDER`), with concrete `AIClient` implementations wired only
at the composition root.

## Additional Constraints

- **Stack.** Backend: Python + FastAPI managed by `uv`. Frontend: Next.js + React (TypeScript).
  Data/auth/storage: Supabase. AI: pluggable behind the `AIClient` interface — Google Gemini
  (via `google-genai`) is the default free-tier provider; Anthropic Claude (via `anthropic`) and
  any OpenAI-compatible endpoint (self-hosted Ollama/llama.cpp or a hosted open-model API, via
  `openai_compatible`) are also supported. Selected with `AI_PROVIDER`.
- **Security & privacy.** No secrets in the repo; every config surface has an `.env.example`.
  User data (CVs, applications) is owner-scoped and protected by Supabase Row Level Security.
  CVs and job descriptions are personal data — never log their contents.
- **Open-source hygiene.** MIT licensed. Public-facing changes keep README/CONTRIBUTING current.

## Development Workflow & Quality Gates

Features follow the Spec Kit flow: `/speckit.constitution` → `/speckit.specify` →
`/speckit.plan` → `/speckit.tasks` → `/speckit.implement`.

Before any backend change is considered done, all gates pass locally:
`uv run ruff check .`, `uv run mypy app`, and `uv run pytest`. Frontend: `npm run lint` and
`npm run build`. A change that fails a gate is not done.

## Governance

This constitution supersedes other practices. Amendments are made by editing this file with a
clear rationale and a version bump. Every plan and PR review must verify compliance with these
principles; added complexity must be justified against Principle II and III or removed.

**Version**: 1.1.0 | **Ratified**: 2026-07-01 | **Last Amended**: 2026-07-07
