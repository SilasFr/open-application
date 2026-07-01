# Supabase

Local database, auth, and storage for Open Application. Requires Docker running.

## Commands

```bash
npx supabase start        # boot the local stack (Postgres + Auth + Storage + Studio)
npx supabase db reset     # drop & recreate the DB, applying everything in migrations/
npx supabase stop         # shut the stack down
```

After `supabase start`, the CLI prints local URLs and keys. Put the API URL and the
**service_role** key into `backend/.env` (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`) and the
URL + **anon** key into `frontend/.env.local`.

## Schema

See [`migrations/`](migrations). The initial migration creates:

- `applications` — the tracker (status lifecycle enforced by a CHECK constraint).
- `cvs` — metadata for uploaded base CVs (file bytes live in the `cvs` storage bucket).
- `tailored_cvs` — AI-generated tailored CVs.

Every table has **Row Level Security** enabled with owner-scoped policies (`auth.uid() =
user_id`), and the private `cvs` storage bucket restricts each user to their own
`<user_id>/…` folder.

## Adding a migration

```bash
npx supabase migration new <name>   # creates a timestamped file in migrations/
# edit the SQL, then:
npx supabase db reset               # re-apply from scratch to verify
```
