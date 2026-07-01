-- Open Application — initial schema.
-- Tracker (applications), CV storage metadata (cvs), and AI outputs (tailored_cvs).
-- Every table is owner-scoped and protected by Row Level Security.

-- ---------------------------------------------------------------------------
-- Helper: keep updated_at fresh on UPDATE.
-- ---------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- applications
-- ---------------------------------------------------------------------------
create table public.applications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    company text not null,
    role text not null,
    status text not null default 'saved'
        check (status in (
            'saved', 'applied', 'interviewing', 'offer',
            'accepted', 'rejected', 'withdrawn'
        )),
    job_description text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index applications_user_id_created_at_idx
    on public.applications (user_id, created_at desc);

create trigger applications_set_updated_at
    before update on public.applications
    for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- cvs — metadata for a base CV; the file itself lives in the `cvs` storage bucket.
-- ---------------------------------------------------------------------------
create table public.cvs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    filename text not null,
    storage_path text not null,
    content text,
    created_at timestamptz not null default now()
);

create index cvs_user_id_idx on public.cvs (user_id);

-- ---------------------------------------------------------------------------
-- tailored_cvs — an AI-generated CV tailored to a job description.
-- ---------------------------------------------------------------------------
create table public.tailored_cvs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    source_cv_id uuid references public.cvs (id) on delete set null,
    job_description text not null,
    content text not null,
    created_at timestamptz not null default now()
);

create index tailored_cvs_user_id_created_at_idx
    on public.tailored_cvs (user_id, created_at desc);

-- ---------------------------------------------------------------------------
-- Row Level Security: users may only touch their own rows.
-- ---------------------------------------------------------------------------
alter table public.applications enable row level security;
alter table public.cvs enable row level security;
alter table public.tailored_cvs enable row level security;

create policy "own applications" on public.applications
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own cvs" on public.cvs
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own tailored_cvs" on public.tailored_cvs
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- Storage: private bucket for CV files, laid out as <user_id>/<filename>.
-- Policies allow a user to manage only objects under their own folder.
-- ---------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('cvs', 'cvs', false)
on conflict (id) do nothing;

create policy "own cv files" on storage.objects
    for all
    using (
        bucket_id = 'cvs'
        and auth.uid()::text = (storage.foldername(name))[1]
    )
    with check (
        bucket_id = 'cvs'
        and auth.uid()::text = (storage.foldername(name))[1]
    );
