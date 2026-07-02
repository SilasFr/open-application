-- Application CRM (feature 002): notes/timeline, contacts, and tasks.
-- Each table is a child of public.applications, owner-scoped via RLS, and
-- cascade-deletes with its parent application (and with the user).
-- Reuses public.set_updated_at() from 20260701170000_init.sql.

-- ---------------------------------------------------------------------------
-- application_notes — unified activity + notes timeline
-- ---------------------------------------------------------------------------
create table public.application_notes (
    id uuid primary key default gen_random_uuid(),
    application_id uuid not null references public.applications (id) on delete cascade,
    user_id uuid not null references auth.users (id) on delete cascade,
    type text not null default 'note'
        check (type in ('note', 'activity', 'email', 'call', 'interview')),
    content text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index application_notes_application_id_created_at_idx
    on public.application_notes (application_id, created_at desc);

create trigger application_notes_set_updated_at
    before update on public.application_notes
    for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- application_contacts
-- ---------------------------------------------------------------------------
create table public.application_contacts (
    id uuid primary key default gen_random_uuid(),
    application_id uuid not null references public.applications (id) on delete cascade,
    user_id uuid not null references auth.users (id) on delete cascade,
    name text not null,
    role text,
    email text,
    phone text,
    linkedin_url text,
    notes text,
    created_at timestamptz not null default now()
);

create index application_contacts_application_id_idx
    on public.application_contacts (application_id);

-- ---------------------------------------------------------------------------
-- application_tasks
-- ---------------------------------------------------------------------------
create table public.application_tasks (
    id uuid primary key default gen_random_uuid(),
    application_id uuid not null references public.applications (id) on delete cascade,
    user_id uuid not null references auth.users (id) on delete cascade,
    title text not null,
    is_completed boolean not null default false,
    due_date timestamptz,
    created_at timestamptz not null default now()
);

create index application_tasks_application_id_idx
    on public.application_tasks (application_id);

-- ---------------------------------------------------------------------------
-- Row Level Security: owner-scoped on every table.
-- ---------------------------------------------------------------------------
alter table public.application_notes enable row level security;
alter table public.application_contacts enable row level security;
alter table public.application_tasks enable row level security;

create policy "own application_notes" on public.application_notes
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own application_contacts" on public.application_contacts
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own application_tasks" on public.application_tasks
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
