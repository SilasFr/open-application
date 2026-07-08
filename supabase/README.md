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

## Applying migrations to production (CI)

Migrations are applied to the hosted Supabase project by the
[`Database Migrations`](../.github/workflows/db-migrations.yml) GitHub Actions
workflow — **never by hand**. On every push to `main` that touches
`supabase/migrations/**`, the workflow runs `supabase db push`, which applies
only migrations not yet recorded remotely. Merging a PR that adds a migration
ships it automatically.

### One-time setup

1. **Add two repo secrets** (Settings → Secrets and variables → Actions):
   - `SUPABASE_ACCESS_TOKEN` — a personal access token from
     <https://supabase.com/dashboard/account/tokens>.
   - `SUPABASE_DB_PASSWORD` — the project's database password
     (Project Settings → Database → Connection string / reset password).

   The project ref (`bezcaappcvbtreqdcpov`) is not secret and lives in the
   workflow `env`.

2. **Baseline the pre-existing migrations.** The first three migrations were
   applied by hand before this pipeline existed, and they are not idempotent, so
   `db push` would fail trying to re-run them. Run the workflow once in
   `repair-baseline` mode to record them as applied *without* executing their
   SQL:

   - Actions → **Database Migrations** → Run workflow → `mode: repair-baseline`,
   - or: `gh workflow run db-migrations.yml -f mode=repair-baseline`.

   After that, all normal pushes/`mode: push` runs apply only genuinely pending
   migrations. This baseline step is needed exactly once.
