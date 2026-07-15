-- Adds BYOK: a user's own AI provider + API key, one row per user, mirroring the
-- "exactly one current" shape of `cvs`. See specs/008-byok-ai-provider-settings.
--
-- The key is stored AES-256-GCM-encrypted (encrypted_key + nonce); the backend
-- never persists a plaintext key. key_last4 is plaintext by design — it's a
-- non-secret display value ("sk-...a4f9") the settings page shows without a
-- decrypt on every read.

create table public.user_ai_keys (
    user_id uuid primary key references auth.users (id) on delete cascade,
    provider text not null
        check (provider in ('anthropic', 'gemini', 'openai_compatible')),
    encrypted_key text not null,
    nonce text not null,
    key_last4 text not null,
    model text not null,
    base_url text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create trigger user_ai_keys_set_updated_at
    before update on public.user_ai_keys
    for each row execute function public.set_updated_at();

-- Row Level Security: deliberately NO policy, unlike every other table in this
-- schema. Nothing outside the backend ever reads this table — not even its
-- owner, who has no reason to fetch their own ciphertext; the settings page is
-- served entirely from the backend's decrypted-then-redacted response. RLS
-- enabled with zero policies denies both anon and authenticated roles outright.
-- The backend's Supabase client uses the service key and bypasses RLS as usual.
alter table public.user_ai_keys enable row level security;
