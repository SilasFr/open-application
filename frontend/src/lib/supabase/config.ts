// Public Supabase config, inlined at build time from NEXT_PUBLIC_* env vars.
// When absent (e.g. local dev before Supabase is set up), the app runs
// unauthenticated instead of crashing.

export const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
export const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export const isSupabaseConfigured = Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
