# Tasks: User Authentication

**Input**: Design documents from `specs/003-auth/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/auth-flows.md

**Organization**: Tasks grouped by user story for independent implementation and testing. This is a frontend-only feature — the backend auth chain (`TokenVerifier`, `get_current_user`, `SupabaseTokenVerifier`) is already complete and requires no changes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths included in every task description

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure that ALL user stories depend on. Must be complete before any auth flow can function end-to-end.

**⚠️ CRITICAL**: No user story implementation can be validated end-to-end until this phase is complete.

- [x] T001 [P] Create auth callback route handler at `frontend/src/app/auth/callback/route.ts` — Route Handler (`GET`) that reads `code`, `type` (`signup` | `recovery` | absent), `error`, and optional `next` query params; calls `supabase.auth.exchangeCodeForSession(code)` on success; redirects to `next` (default `/tracker`) on success or to `/login?error=<message>` on failure
- [x] T002 [P] Add auth-guard logic to `frontend/src/lib/supabase/proxy-session.ts` and `frontend/src/proxy.ts` — after the existing `getClaims()` call, redirect unauthenticated requests for `/tracker` and `/tailor` paths to `/login`; redirect authenticated requests for `/login` to `/tracker`

**Checkpoint**: Foundation complete — both OAuth flows and route protection are now active. User story implementation can begin.

---

## Phase 2: US1 + US2 — Email Sign-Up & Sign-In (Priority: P1) 🎯 MVP

**Goal**: Users can create an account and sign in using email/password, including via Google and LinkedIn social login.

**Independent Test**: Navigate to `/login`, create a new account with email + a strong password, verify redirect to `/tracker`. Sign out, return to `/login`, sign in with the same credentials, verify redirect to `/tracker` again. Try Google/LinkedIn buttons and verify redirect to `/tracker` after OAuth consent.

- [x] T003 [US1] Update password validation in `frontend/src/app/login/page.tsx` — replace `minLength={6}` with a client-side regex check requiring ≥ 8 characters, at least one letter, and at least one number; display an inline error message below the password field explaining the requirement when violated; block form submission until the password passes
- [x] T004 [US1] Update sign-in error handling in `frontend/src/app/login/page.tsx` — change the error message for failed sign-in to a generic "Invalid email or password" that does not reveal which field was wrong; update the sign-up duplicate-email error message to "This email is already registered. Try signing in."
- [x] T005 [US1] Add social login section to `frontend/src/app/login/page.tsx` — add a visual divider ("or continue with") and two buttons: "Continue with Google" and "Continue with LinkedIn"; each button calls `supabase.auth.signInWithOAuth({ provider: 'google' | 'linkedin_oidc', options: { redirectTo: \`\${window.location.origin}/auth/callback\` } })`; show loading state during the redirect; display an error if `searchParams.error` is present in the URL (e.g., user cancelled OAuth consent)

**Checkpoint**: US1 + US2 complete — email/password sign-up, sign-in, and social login are all functional and independently testable.

---

## Phase 3: US3 — Password Reset (Priority: P2)

**Goal**: A user who has forgotten their password can receive a reset email and set a new password.

**Independent Test**: Click "Forgot password?" on `/login`, enter a registered email, confirm notice is shown, open the reset email, click the link, set a new password on `/auth/reset-password`, verify redirect to `/tracker`, verify old password no longer works.

- [x] T006 [US3] Add "Forgot password?" mode to `frontend/src/app/login/page.tsx` — add a third `Mode` value (`"forgot-password"`); render an email-only input and a submit button in this mode; on submit call `supabase.auth.resetPasswordForEmail(email, { redirectTo: \`\${window.location.origin}/auth/reset-password\` })`; always show the notice "If an account exists, you'll receive a reset email." regardless of whether the email is registered; add a back link to return to sign-in mode
- [x] T007 [P] [US3] Create reset-password page at `frontend/src/app/auth/reset-password/page.tsx` — "set new password" client component with two password fields (new password + confirm); validate both fields: ≥ 8 characters, at least one letter, one number, and fields must match; on submit call `supabase.auth.updateUser({ password: newPassword })`; on success redirect to `/tracker`; on error (e.g., expired link, session mismatch) show a clear message with a link back to `/login`

**Checkpoint**: US3 complete — full password reset flow works independently of other stories.

---

## Phase 4: US4 — Sign Out (Priority: P2)

**Goal**: Authenticated users can explicitly terminate their session and are redirected to the sign-in page.

**Independent Test**: While signed in, click "Sign out" in the header; confirm redirect to `/login`; confirm that navigating directly to `/tracker` then redirects back to `/login`.

- [x] T008 [US4] Update sign-out redirect in `frontend/src/components/AuthStatus.tsx` — change `router.push("/")` to `router.push("/login")` so users are sent to the sign-in page (not the home page) after signing out

**Checkpoint**: US4 complete — sign-out terminates session and lands the user at `/login`.

---

## Phase 5: US5 — Persistent Session (Priority: P2)

**Goal**: Authenticated users remain signed in across browser tab closures within the session validity window.

**Status**: Already implemented — `@supabase/ssr` cookie-based session management and the `updateSession()` call in `frontend/src/lib/supabase/proxy-session.ts` handle token refresh on every request. No code changes required. Validate using Quickstart Scenario 12.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and end-to-end validation.

- [x] T009 [P] Create `frontend/.env.example` — document the two required environment variables (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`) with placeholder values; add a comment noting that Google and LinkedIn OAuth providers must be enabled in the Supabase Dashboard and that `<site-url>/auth/callback` must be in the allowed redirect URLs list
- [x] T010 Run all 12 validation scenarios from `specs/003-auth/quickstart.md` against the running app and fix any failures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — start immediately, T001 and T002 are parallel
- **US1+US2 (Phase 2)**: Depends on Phase 1 complete (needs T001 for OAuth callback, T002 for redirect after sign-in)
- **US3 (Phase 3)**: Depends on Phase 1 complete (needs T001 for reset callback); T006 also depends on T003–T005 completing (same file)
- **US4 (Phase 4)**: No dependency on Phase 2 or 3 — can start after Phase 1
- **US5 (Phase 5)**: Already implemented — validate at any point after Phase 1
- **Polish (Final Phase)**: Depends on all desired stories being complete

### User Story Dependencies

- **US1+US2 (P1)**: Requires Phase 1 → T003 → T004 → T005 (sequential, same file)
- **US3 (P2)**: Requires Phase 1, T003 done → T006 (same file); T007 is a new file, runs in parallel with T006
- **US4 (P2)**: Requires Phase 1 only; T008 is independent of T003–T007
- **US5 (P2)**: No tasks — already implemented

### Parallel Opportunities

- T001 and T002 can run in parallel (different files)
- T007 (new file) can run in parallel with T006 (login page modification)
- T008 can run in parallel with T006 and T007 (touches AuthStatus.tsx, a different file)
- T009 can run in parallel with T010 (different activities)

---

## Parallel Execution Example: Phase 1

```
Parallel start:
  Agent A → T001: Create frontend/src/app/auth/callback/route.ts
  Agent B → T002: Update frontend/src/lib/supabase/proxy-session.ts + frontend/src/proxy.ts
Both complete → proceed to user stories
```

## Parallel Execution Example: Phase 3 (US3)

```
After T003–T005 complete:
  Agent A → T006: Add forgot-password mode to frontend/src/app/login/page.tsx
  Agent B → T007: Create frontend/src/app/auth/reset-password/page.tsx  (new file — no conflict)
  Agent C → T008: Update sign-out redirect in frontend/src/components/AuthStatus.tsx (different file)
```

---

## Implementation Strategy

### MVP (Phase 1 + Phase 2 only)

1. Complete Phase 1: Foundational (T001, T002)
2. Complete Phase 2: US1+US2 email + social login (T003, T004, T005)
3. **STOP and VALIDATE**: Sign up, sign in, sign out, try Google/LinkedIn, verify protected routes redirect to `/login`
4. This is a shippable increment — users can authenticate

### Full Feature (All Phases)

1. Complete Phase 1 → Foundation active
2. Complete Phase 2 → Email + social login working (**MVP demo point**)
3. Complete Phase 3 → Password reset working
4. Complete Phase 4 → Sign-out lands on `/login` (**now fully polished**)
5. Verify Phase 5 → Session persistence validated (no code changes)
6. Complete Final Phase → Documentation + full validation

---

## Notes

- [P] tasks = different files, no write conflicts, safe to parallelize
- LinkedIn provider identifier is `linkedin_oidc` (not `linkedin`) — critical detail from research.md
- The backend requires **zero changes** — `SupabaseTokenVerifier` already handles JWTs from all providers (email, Google, LinkedIn)
- All 12 quickstart scenarios in `specs/003-auth/quickstart.md` serve as acceptance tests
- Commit after each task or logical group to keep changes reviewable
