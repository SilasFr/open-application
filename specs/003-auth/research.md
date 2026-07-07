# Research: User Authentication

**Feature**: `003-auth` | **Date**: 2026-07-02

## Decisions

---

### Decision 1: OAuth provider integration approach

**Decision**: Use Supabase JS SDK (`signInWithOAuth`) for OAuth flows entirely client-side; handle the callback via a Next.js Route Handler at `/auth/callback`.

**Rationale**: Supabase's `@supabase/ssr` package manages the token exchange and cookie writes automatically when `exchangeCodeForSession(code)` is called in the Route Handler. This pattern is the standard Supabase PKCE flow and is already compatible with the project's existing `updateSession` middleware.

**Alternatives considered**:
- Backend-proxied OAuth redirect: rejected — would bypass Supabase Auth's cookie management, require backend session storage, and add unnecessary complexity since the backend only needs to verify tokens (already working).

---

### Decision 2: LinkedIn provider name in Supabase

**Decision**: Use `linkedin_oidc` (not `linkedin`) as the provider identifier when calling `signInWithOAuth`.

**Rationale**: Supabase deprecated the legacy `linkedin` provider in favour of `linkedin_oidc` (OpenID Connect). New projects (including this one, which has the providers configured in the Supabase dashboard) use the OIDC variant. The user confirmed providers are already configured in the Supabase project.

**Alternatives considered**:
- `linkedin` legacy provider: rejected — Supabase no longer creates new apps with this provider; would fail silently or error.

---

### Decision 3: Route protection location

**Decision**: Enforce auth-guarding in the Next.js proxy (`proxy.ts` / middleware), redirecting unauthenticated requests to `/login` for protected paths (`/tracker`, `/tailor`). Also redirect already-authenticated users away from `/login` to `/tracker`.

**Rationale**: Middleware runs before any page renders and is the correct Next.js location for session-based redirects. The `updateSession` function already has the Supabase client and calls `getClaims()` — it can inspect the resulting session and redirect immediately without a round-trip to the page component. This keeps route-protection logic in one place rather than duplicated across page components.

**Alternatives considered**:
- Per-page redirect in Server Components: rejected — duplication across every protected page; slower (page partially renders before redirect).
- Client-side redirect with `useEffect`: rejected — exposes a flash of unauthenticated content; poor UX.

---

### Decision 4: Password reset flow

**Decision**: Use Supabase's built-in password reset email (`resetPasswordForEmail`) with a redirect to `/auth/callback?next=/auth/reset-password` — not directly to `/auth/reset-password`, which is not in Supabase's redirect allowlist and would be silently downgraded to the bare site URL — then `updateUser({ password })` on that page once the callback route exchanges the code and forwards there.

**Rationale**: Supabase handles the secure token generation, delivery, and expiry for the reset link. The app only needs to (a) trigger the email and (b) provide the UI to set a new password once the user lands from the link. The auth callback route (`/auth/callback`) handles the code exchange for the reset token automatically (same route as OAuth).

**Alternatives considered**:
- Custom email with backend-generated reset token: rejected — unnecessary complexity; Supabase Auth already provides this with proper expiry and single-use guarantees.

---

### Decision 5: Backend scope

**Decision**: No backend changes required for this feature.

**Rationale**: The backend already implements the full auth verification chain:
- `TokenVerifier` domain interface in `app/domain/auth.py`
- `SupabaseTokenVerifier` in `app/infrastructure/auth/supabase_verifier.py` (supports RS256/ES256/HS256)
- `get_current_user` / `get_current_user_id` FastAPI dependencies in `app/core/security.py`
- All existing routes already use these dependencies for user scoping

Social login via Google/LinkedIn issues the same Supabase JWT format — the verifier already handles it.

---

### Decision 6: Password strength validation

**Decision**: Update frontend validation to enforce minimum 8 characters, at least one letter, and at least one number. Validation is on the client before submit, with a clear inline error message.

**Rationale**: The current login page uses `minLength={6}`, which is below the spec's requirement of 8+ chars with letter + number. Client-side validation provides immediate feedback. Supabase also enforces server-side minimum length when configured in the Dashboard (set to 8).

**Alternatives considered**:
- Server-side only validation via Supabase error messages: rejected — Supabase error messages are not always user-friendly; inline validation is better UX.

---

### Decision 7: Email confirmation flow

**Decision**: Email confirmation is **disabled** (Supabase Dashboard → Authentication → Sign In / Providers → Email → "Confirm email" off). A new email/password sign-up returns an active session immediately and the user is redirected straight to `/tracker` — no "check your email" step. The login page defensively signs the user in explicitly if `signUp` ever returns no session (e.g. confirmation re-enabled).

**Rationale**: Reliable transactional email requires custom SMTP (e.g. Resend), which is deferred until the project needs it. Blocking every new sign-up on an email that may not deliver is a worse trade-off at this stage than allowing unconfirmed accounts. Revisit (re-enable confirmation) once SMTP is configured and scale warrants it.

**Alternatives considered**:
- Keep confirmation on with Supabase's built-in email: rejected — the default sender is rate-limited (2/hour) and unsuitable for real sign-ups; deliverability is unreliable without custom SMTP.
