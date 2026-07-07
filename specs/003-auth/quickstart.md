# Quickstart Validation Guide: User Authentication

**Feature**: `003-auth` | **Date**: 2026-07-02

This guide describes how to validate that each auth flow works end-to-end after implementation. It is a run guide — not a code tutorial.

---

## Prerequisites

- Both services running locally:
  - Frontend: `npm run dev` in `frontend/` (default port 3000)
  - Backend: `uv run uvicorn app.main:app --reload` in `backend/` (default port 8000)
- `frontend/.env.local` contains `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Supabase project has Google and LinkedIn OIDC configured as auth providers (user confirmed)
- Email delivery is enabled in the Supabase project (required for password reset and email confirmation)

---

## Scenario 1: Email / Password Sign-Up

**Goal**: A new user creates an account and reaches the dashboard.

**Steps**:
1. Navigate to `http://localhost:3000/login`
2. Switch to "Create account" mode
3. Enter a valid email address not yet registered
4. Enter a password: `TestPass1` (meets 8 chars, 1 letter, 1 number requirement)
5. Submit

**Expected**:
- Email confirmation is disabled (see research.md Decision 7), so the account is
  active immediately and the browser redirects to `/tracker` — no "check your
  email" step.
- Prerequisite: Supabase Dashboard → Authentication → Sign In / Providers →
  Email → "Confirm email" is **off**.

---

## Scenario 2: Email / Password Sign-In

**Goal**: A registered user signs in and is redirected to the dashboard.

**Steps**:
1. Navigate to `http://localhost:3000/login`
2. Enter the email and password from Scenario 1
3. Submit

**Expected**: Redirect to `/tracker`; header shows the signed-in email address and "Sign out" button.

---

## Scenario 3: Invalid Credentials

**Goal**: Error is shown without revealing which field failed.

**Steps**:
1. On `/login`, enter a valid email with an incorrect password
2. Submit

**Expected**: "Invalid email or password" error message; user remains on `/login`; no indication of whether the email or password was wrong.

---

## Scenario 4: Duplicate Email on Sign-Up

**Goal**: Attempting to register an existing email shows a clear message.

**Steps**:
1. Switch to "Create account" mode on `/login`
2. Enter an email address already registered
3. Submit

**Expected**: Error message "This email is already registered. Try signing in." (or equivalent); user remains on sign-up form.

---

## Scenario 5: Google Social Login

**Goal**: A user signs in via Google.

**Steps**:
1. Navigate to `http://localhost:3000/login`
2. Click "Continue with Google"
3. Complete Google consent (use a test Google account)

**Expected**:
- Browser redirects through Google consent and back to `/auth/callback`
- Final redirect to `/tracker`
- Header shows the Google account's email

---

## Scenario 6: LinkedIn Social Login

**Goal**: A user signs in via LinkedIn.

**Steps**:
1. Navigate to `http://localhost:3000/login`
2. Click "Continue with LinkedIn"
3. Complete LinkedIn consent

**Expected**: Same as Google — redirect through LinkedIn and back, landing on `/tracker`.

---

## Scenario 7: Password Reset

**Goal**: A user who forgot their password sets a new one.

**Steps**:
1. On `/login`, click "Forgot password?"
2. Enter the registered email address and submit
3. Confirm the notice "If an account exists, you'll receive a reset email." is shown
4. Open the reset email and click the link
5. On `/auth/reset-password`, enter a new password (`NewPass1`) and submit

**Expected**:
- Redirect to `/tracker`
- Can sign in with the new password
- Old password no longer works

---

## Scenario 8: Sign-Out

**Goal**: Sign-out terminates the session and protects routes.

**Steps**:
1. While signed in, click "Sign out" in the header
2. Confirm redirect to `/login`
3. Manually navigate to `http://localhost:3000/tracker`

**Expected**: Step 2 lands on `/login`; Step 3 redirects to `/login`.

---

## Scenario 9: Route Protection

**Goal**: Unauthenticated users cannot access protected pages.

**Steps**:
1. Ensure no active session (sign out first, or use an incognito window)
2. Navigate directly to `http://localhost:3000/tracker`
3. Navigate directly to `http://localhost:3000/tailor`

**Expected**: Both routes redirect to `/login`.

---

## Scenario 10: Already-Authenticated Redirect

**Goal**: A signed-in user visiting `/login` is redirected to the dashboard.

**Steps**:
1. While signed in, navigate to `http://localhost:3000/login`

**Expected**: Immediate redirect to `/tracker`; login page never renders.

---

## Scenario 11: Password Strength Validation

**Goal**: Weak passwords are rejected with a helpful inline message.

**Steps**:
1. On `/login` in "Create account" mode, enter password `short` (< 8 chars) and submit
2. Enter password `alllowercase` (no number) and submit
3. Enter password `12345678` (no letter) and submit

**Expected**: Each attempt shows an inline error explaining the requirement; form is not submitted.

---

## Scenario 12: Persistent Session

**Goal**: Signed-in users remain authenticated across browser tab closures.

**Steps**:
1. Sign in
2. Close the browser tab
3. Open a new tab and navigate to `http://localhost:3000/tracker`

**Expected**: User is still authenticated (no redirect to login); dashboard loads with their applications.

---

## Backend Verification

After any successful sign-in (email or social), verify the backend correctly identifies the user:

```
curl -H "Authorization: Bearer <supabase_access_token>" http://localhost:8000/api/v1/applications
```

**Expected**: Returns the user's applications (200 OK with JSON array), not a 401.

The access token can be found in browser DevTools → Application → Local Storage → Supabase session.
