-- Extends tailored_cvs with structured section output, an optional application
-- attachment, and refinement linkage. See specs/004-ui-redesign/data-model.md.
--
-- All new columns are additive and nullable (or have a safe default), so existing
-- rows remain valid without a backfill. RLS is inherited from the existing
-- "own tailored_cvs" policy (auth.uid() = user_id) — these columns don't widen
-- access, since the service layer only lets a user set application_id to an
-- application they already own.

alter table public.tailored_cvs
    add column if not exists sections jsonb not null default '[]'::jsonb,
    add column if not exists application_id uuid references public.applications(id) on delete set null,
    add column if not exists refinement_instructions text,
    add column if not exists previous_tailored_cv_id uuid references public.tailored_cvs(id) on delete set null;

create index if not exists tailored_cvs_application_id_idx
    on public.tailored_cvs (application_id);

create index if not exists tailored_cvs_previous_tailored_cv_id_idx
    on public.tailored_cvs (previous_tailored_cv_id);
