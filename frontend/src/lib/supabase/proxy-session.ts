import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

const PROTECTED_PATHS = ["/tracker", "/tailor", "/settings"];

function isProtectedPath(pathname: string): boolean {
  return PROTECTED_PATHS.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
}

/**
 * Refreshes the Supabase auth session on each request, syncs auth cookies onto
 * the response, and enforces route protection: unauthenticated users are
 * redirected to /login for protected paths; authenticated users visiting /login
 * are redirected to /tracker. Called from `src/proxy.ts` (Next.js 16's renamed
 * middleware). If Supabase env vars are absent, it is a no-op so the app still
 * runs unauthenticated in local dev.
 */
export async function updateSession(request: NextRequest): Promise<NextResponse> {
  let response = NextResponse.next({ request });

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anonKey) {
    return response;
  }

  const supabase = createServerClient(url, anonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) =>
          request.cookies.set(name, value),
        );
        response = NextResponse.next({ request });
        cookiesToSet.forEach(({ name, value, options }) =>
          response.cookies.set(name, value, options),
        );
      },
    },
  });

  // Do not run other logic between creating the client and this call — it
  // refreshes the token and must be able to write the updated cookies.
  const { data } = await supabase.auth.getClaims();
  const isAuthenticated = data !== null;
  const { pathname } = request.nextUrl;

  // Build a redirect response that carries any cookies written during getClaims
  // (e.g., a refreshed access token) so the session stays consistent.
  const buildRedirect = (destination: string): NextResponse => {
    const target = request.nextUrl.clone();
    target.pathname = destination;
    target.search = "";
    const redirectResponse = NextResponse.redirect(target);
    response.cookies.getAll().forEach(({ name, value, ...options }) => {
      redirectResponse.cookies.set(name, value, options);
    });
    return redirectResponse;
  };

  if (isProtectedPath(pathname) && !isAuthenticated) {
    return buildRedirect("/login");
  }

  if (pathname === "/login" && isAuthenticated) {
    return buildRedirect("/tracker");
  }

  return response;
}
