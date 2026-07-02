# Data Model: User Authentication

**Feature**: `003-auth` | **Date**: 2026-07-02

## Overview

All authentication entities are managed entirely by **Supabase Auth**. No new database tables are created by this feature. The application domain exposes a single read-only value type derived from a verified access token.

---

## Domain Entity: AuthenticatedUser

**Location**: `backend/app/domain/auth.py` (already exists)

Represents the identity extracted from a verified Supabase JWT. Used throughout the backend to scope all data access.

| Field  | Type         | Source                  | Notes                           |
|--------|--------------|-------------------------|---------------------------------|
| `id`   | `str` (UUID) | JWT `sub` claim         | Stable Supabase user UUID       |
| `email`| `str \| None`| JWT `email` claim       | Present for all auth providers  |

This entity is **immutable** (frozen dataclass). It is populated once per request by `SupabaseTokenVerifier.verify()` and injected into route handlers via `get_current_user`.

---

## Supabase-Managed Entities

These entities live in the `auth` schema in Supabase's managed Postgres instance. The application **never writes directly** to these tables.

### User

Managed by Supabase Auth. Created on sign-up (email/password or OAuth).

| Field              | Notes                                                        |
|--------------------|--------------------------------------------------------------|
| `id` (UUID)        | Primary key; matches `AuthenticatedUser.id`                  |
| `email`            | Unique; present for email/password and most OAuth providers  |
| `encrypted_password` | Bcrypt hash; null for OAuth-only accounts                  |
| `email_confirmed_at` | Null until email is confirmed                              |
| `last_sign_in_at`  | Updated on every successful sign-in                          |
| `raw_app_meta_data` | Contains `provider` (e.g., `email`, `google`, `linkedin_oidc`) |
| `created_at`       | Account creation timestamp                                   |

### Session

Managed by Supabase Auth. Represents an active authenticated context. Stored server-side; the client holds only the access + refresh tokens.

| Field        | Notes                                                         |
|--------------|---------------------------------------------------------------|
| `id` (UUID)  | Primary key                                                   |
| `user_id`    | FK to User                                                    |
| `created_at` | When the session was established                              |
| `not_after`  | Session hard expiry (Supabase default: 1 week)                |

Sessions are terminated on sign-out (`supabase.auth.signOut()`) or expiry.

### Password Reset Token

One-time use token embedded in the reset link email. Managed entirely by Supabase Auth.

| Attribute    | Notes                                                         |
|--------------|---------------------------------------------------------------|
| Lifetime     | Default 24 hours (configurable in Supabase Dashboard)         |
| Single-use   | Invalidated immediately after use                             |
| Delivery     | Sent to the user's registered email address                   |

---

## Row Level Security

All application data tables (applications, notes, contacts, tasks) already enforce RLS policies scoped to `auth.uid()`. No changes are required to existing RLS policies — the JWT issued after social login carries the same `sub` claim as an email/password JWT.

---

## State Transitions

```
[No Account]
     │
     │ sign-up (email/password)
     ▼
[Unconfirmed] ──── email confirmation link ────► [Active]
                                                     │
[No Account]                                         │ sign-out
     │                                               ▼
     │ sign-in via OAuth (Google / LinkedIn)    [No Session]
     ▼                                               │
[Active] ◄───────────────────────────────────── sign-in again
     │
     │ forgot password → reset email
     ▼
[Active, new password set]
```
