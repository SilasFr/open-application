import type { NextRequest } from "next/server";
import { updateSession } from "@/lib/supabase/proxy-session";

// Next.js 16 renamed Middleware to Proxy (same functionality). This keeps the
// Supabase session fresh on every navigation.
export async function proxy(request: NextRequest) {
  return updateSession(request);
}

export const config = {
  // Run on all paths except static assets and image files.
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
