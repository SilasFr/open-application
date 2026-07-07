# Auth Flow Contracts

**Feature**: `003-auth` | **Date**: 2026-07-02

This document defines the URL contracts and flow contracts for the authentication feature. All flows are frontend-only (Next.js). The backend is not modified.

---

## URL Contracts

| Route                   | Type               | Visibility  | Description                                        |
|-------------------------|--------------------|-------------|----------------------------------------------------|
| `GET /login`            | Next.js Page       | Public      | Sign-in / sign-up form (email+password + social)  |
| `GET /auth/callback`    | Next.js Route Handler | Public   | OAuth code exchange + email confirmation handler   |
| `GET /auth/reset-password` | Next.js Page    | Public      | Set new password after clicking reset email link   |
| `GET /tracker`          | Next.js Page       | Protected   | Redirects to `/login` if unauthenticated           |
| `GET /tailor`           | Next.js Page       | Protected   | Redirects to `/login` if unauthenticated           |

---

## Flow 1: Email / Password Sign-In

```
User → POST credentials → supabase.auth.signInWithPassword()
   ↓ success
Session cookies set by @supabase/ssr → redirect to /tracker
   ↓ failure
Error message displayed; user remains on /login
```

**Inputs**: `email` (valid format), `password` (min 8 chars, ≥1 letter, ≥1 number)
**Error cases**: invalid credentials → generic "Invalid email or password" message (no hint which field failed)

---

## Flow 2: Email / Password Sign-Up

```
User → POST credentials → supabase.auth.signUp()
   ↓ email confirmation disabled (Supabase dashboard setting; research.md #7)
Session returned directly → redirect to /tracker
   ↓ (defensive) no session returned
supabase.auth.signInWithPassword() → redirect to /tracker
```

**Inputs**: same as sign-in
**Prerequisite**: "Confirm email" is disabled in the Supabase dashboard.
**Error cases**: duplicate email → "This email is already registered. Try signing in."

---

## Flow 3: Google OAuth

```
User → clicks "Continue with Google"
   → supabase.auth.signInWithOAuth({ provider: 'google', redirectTo: '<origin>/auth/callback' })
   → browser redirects to Google consent screen
   → Google redirects to /auth/callback?code=<code>
   → supabase.auth.exchangeCodeForSession(code)
   → redirect to /tracker
```

**Provider identifier**: `'google'`
**Scopes requested**: default (email, profile) — configured in Supabase Dashboard
**Error cases**: user cancels Google consent → redirect to `/login?error=access_denied`

---

## Flow 4: LinkedIn OAuth

```
User → clicks "Continue with LinkedIn"
   → supabase.auth.signInWithOAuth({ provider: 'linkedin_oidc', redirectTo: '<origin>/auth/callback' })
   → browser redirects to LinkedIn consent screen
   → LinkedIn redirects to /auth/callback?code=<code>
   → supabase.auth.exchangeCodeForSession(code)
   → redirect to /tracker
```

**Provider identifier**: `'linkedin_oidc'` (OIDC variant — required for Supabase v2+ projects)
**Error cases**: same as Google

---

## Flow 5: Password Reset

```
User → clicks "Forgot password?" on /login
   → enters email → supabase.auth.resetPasswordForEmail(email, { redirectTo: '<origin>/auth/callback?next=/auth/reset-password' })
   → notice: "If an account exists, you'll receive a reset email."
   
User clicks link in email:
   → GET /auth/callback?code=<token>&type=recovery
   → supabase.auth.exchangeCodeForSession(code)
   → redirect to /auth/reset-password (session now active with recovery scope)

User sets new password on /auth/reset-password:
   → supabase.auth.updateUser({ password: newPassword })
   → redirect to /tracker
```

**Security note**: The "account exists" message is always shown regardless of whether the email is registered, preventing account enumeration.

---

## Flow 6: Sign-Out

```
User → clicks "Sign out" in header AuthStatus component
   → supabase.auth.signOut()
   → session cookies cleared
   → redirect to /
```

---

## Flow 7: Route Protection (Middleware)

```
Request to /tracker or /tailor:
   → proxy.ts (Next.js middleware) runs updateSession()
   → getClaims() returns null (no valid session)
   → redirect to /login

Request to /login (already authenticated):
   → getClaims() returns valid claims
   → redirect to /tracker
```

**Protected paths**: `/tracker`, `/tailor` (and any sub-paths)
**Login bypass**: `/login` redirects to `/tracker` when already authenticated

---

## Auth Callback Route Handler Contract

**Path**: `GET /auth/callback`

**Query parameters**:

| Parameter | Required | Description                                      |
|-----------|----------|--------------------------------------------------|
| `code`    | Yes      | Authorization code from Supabase/OAuth provider  |
| `type`    | No       | `signup`, `recovery`, or absent (OAuth)          |
| `error`   | No       | OAuth error code (e.g., `access_denied`)         |
| `next`    | No       | Path to redirect to after success (default: `/tracker`) |

**Response**: HTTP 302 redirect to `next` (success) or `/login?error=<message>` (failure)
