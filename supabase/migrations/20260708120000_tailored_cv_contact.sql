-- Adds a structured contact/header block to tailored_cvs (name, email, phone,
-- location, labelled links) so the downloadable resume can render a proper
-- header. See specs/007-rich-resume-rendering.
--
-- Additive and nullable, so existing rows remain valid without a backfill. The
-- richer per-section "entries" (structured experience/education items) live
-- inside the existing `sections` jsonb, so no column change is needed for them.
-- RLS is inherited from the existing "own tailored_cvs" policy (auth.uid() =
-- user_id); this column doesn't widen access.

alter table public.tailored_cvs
    add column if not exists contact jsonb;
