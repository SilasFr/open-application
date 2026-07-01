# Open Application — Backend

FastAPI service organized in a layered / OOP (clean) architecture. See the project
[constitution](../.specify/memory/constitution.md) for the rules this code follows.

## Layers

```
app/
├── domain/          # Pure OOP: entities, value objects, repository & AIClient interfaces
├── services/        # Business logic as classes (depend only on domain interfaces)
├── infrastructure/  # Concrete adapters: Supabase repositories, Anthropic AIClient, prompts
├── api/             # Thin FastAPI routers (parse → call one service → shape response)
├── schemas/         # Pydantic request/response DTOs
└── core/            # Settings, security, dependency-injection composition root
```

Dependencies point inward: `api → services → domain`. Nothing in `domain` imports a web
framework, an SDK, or a database driver. `infrastructure` implements interfaces that `domain`
declares.

## Develop

```bash
uv sync
cp .env.example .env      # fill Supabase + Anthropic values
uv run uvicorn app.main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Quality gates

```bash
uv run ruff check .
uv run mypy app
uv run pytest            # unit tests use in-memory fakes — no network required
```
