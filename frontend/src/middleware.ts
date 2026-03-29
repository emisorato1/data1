/**
 * Next.js Edge Middleware — Route Protection
 *
 * Runs on the Edge before every request. Redirects unauthenticated users to
 * /login when they try to access protected routes (everything under /chat).
 *
 * NOTE: The `access_token` cookie is HTTPOnly, so JS cannot read it.
 * The middleware CAN read it because it runs server-side on the Edge.
 * We only check for the cookie's *presence* here; actual JWT signature
 * validation happens in the FastAPI backend on every API call.
 */

import { NextRequest, NextResponse } from "next/server";

/** Routes that require an authenticated session. */
const PROTECTED_PREFIXES = ["/chat"];

/** Routes that are always public (bypass auth check). */
const PUBLIC_PREFIXES = ["/login", "/_next", "/favicon.ico", "/api"];

export function middleware(request: NextRequest): NextResponse {
    const { pathname } = request.nextUrl;

    // Always allow public routes
    if (PUBLIC_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
        return NextResponse.next();
    }

    // Check if the route needs protection
    const isProtected = PROTECTED_PREFIXES.some((prefix) =>
        pathname.startsWith(prefix)
    );

    if (!isProtected) {
        return NextResponse.next();
    }

    // Read the HTTPOnly access_token cookie
    const accessToken = request.cookies.get("access_token")?.value;

    if (!accessToken) {
        // No token → redirect to login, preserving the intended destination
        const loginUrl = new URL("/login", request.url);
        loginUrl.searchParams.set("next", pathname);
        return NextResponse.redirect(loginUrl);
    }

    return NextResponse.next();
}

export const config = {
    /*
     * Match all paths except:
     * - _next/static  (static files)
     * - _next/image   (image optimization)
     * - favicon.ico
     */
    matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
