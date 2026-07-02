# Implementation Plan: User Authentication

**Branch**: `003-auth` | **Date**: 2026-07-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-auth/spec.md`

## Summary

Enable users to create accounts, sign in via email/password or social login (Google, LinkedIn), reset forgotten passwords, and have protected routes enforced automatically. Supabase Auth is the identity provider; the backend's JWT verification infrastructure is already complete and requires no changes. This plan covers the **frontend-only** work: adding the OAuth flow, password reset flow, auth callback route handler, route protection middleware, and updating password strength validation.

## Technical Context

**Language/Version**: TypeScript — Next.js 16.2.9, React 19.2.4

**Primary Dependencies**: `@supabase/ssr`, `@supabase/supabase-js` (already installed)

**Storage**: Supabase Auth (managed Postgres `auth` schema); no new tables

**Testing**: Frontend: `npm run lint`, `npm run build`; Backend: `uv run ruff check .`, `uv run mypy app`, `uv run pytest` (no backend changes — existing tests unchanged)

**Target Platform**: Web (Next.js App Router, server + client components)

**Project Type**: Web application (fullstack — backend already complete for this feature)

**Performance Goals**: Auth flows complete in under 2 seconds on a standard connection

**Constraints**: No secrets in repo; OAuth redirect URLs must be configured in Supabase Dashboard; LinkedIn provider must use `linkedin_oidc` identifier

**Scale/Scope**: Single-user-at-a-time auth flows; no concurrent session limit concerns

## Constitution Check

### Gates (pre-design)

| Gate | Status | Notes |
|------|--------|-------|
| Spec-First: spec.md exists and is validated | PASS | `specs/003-auth/spec.md` complete |
| No business logic in route handlers | PASS | Auth flows delegate to Supabase SDK; no logic leaks into handlers |
| Domain layer stays pure | PASS | `AuthenticatedUser` and `TokenVerifier` already correct; no new domain changes |
| Services depend on abstractions | PASS | Backend unchanged; no new service dependencies |
| Full type hints + mypy clean | PASS | No backend changes; frontend uses TypeScript throughout |
| Unit tests use in-memory fakes | PASS | No new backend services; existing fakes unchanged |
| No secrets in repo | PASS | OAuth credentials are in Supabase Dashboard only; `.env.local` is gitignored |
| RLS enforces data ownership | PASS | Existing RLS policies already scope to `auth.uid()`; social login JWT carries same `sub` |

### Gates (post-design)

| Gate | Status | Notes |
|------|--------|-------|
| No new DB tables or RLS changes needed | PASS | Supabase Auth manages all auth entities |
| Backend layer boundaries respected | PASS | Backend requires zero changes |
| Middleware pattern aligns with Next.js 16 proxy convention | PASS | `proxy.ts` is the correct Next.js 16 middleware file (already used) |

## Project Structure

### Documentation (this feature)

```text
specs/003-auth/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── auth-flows.md   # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (frontend only — backend unchanged)

```text
frontend/src/
├── proxy.ts                          # MODIFY: add auth-guard redirects for protected paths
├── lib/
│   └── supabase/
│       └── proxy-session.ts          # MODIFY: expose session/claims from updateSession for redirect logic
├── app/
│   ├── login/
│   │   └── page.tsx                  # MODIFY: add social login buttons, forgot password, stronger password validation
│   ├── auth/
│   │   ├── callback/
│   │   │   └── route.ts              # NEW: OAuth code exchange + email/reset confirmation handler
│   │   └── reset-password/
│   │       └── page.tsx              # NEW: set new password form (accessed via password reset email link)
│   └── [tracker/, tailor/ unchanged] # Route protection enforced at middleware level
└── components/
    └── AuthStatus.tsx                # No changes required
```

**Structure Decision**: Web application (Option 2). Only frontend changes are required. Backend already implements the full auth verification chain with no gaps.

## Complexity Tracking

No constitution violations. No complexity justification required.
