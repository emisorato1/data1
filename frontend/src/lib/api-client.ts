/**
 * Centralized API client with automatic 401 → /login redirect.
 *
 * All frontend API calls should go through `apiFetch` instead of raw `fetch`
 * so that session expiry is handled consistently across the entire app.
 *
 * Usage:
 *   const res = await apiFetch("/api/v1/conversations?limit=50");
 *   const data = await res.json();
 */

"use client";

/** Redirect the browser to the login page, preserving the current path. */
function redirectToLogin(): void {
    const currentPath = window.location.pathname;
    const loginUrl = `/login?next=${encodeURIComponent(currentPath)}&reason=session_expired`;
    window.location.replace(loginUrl);
}

/**
 * Drop-in replacement for `fetch` that:
 *  1. Always sends cookies (`credentials: "include"`).
 *  2. On a 401 response, redirects the user to the login page.
 *
 * @param input  - URL string or Request (same as fetch).
 * @param init   - RequestInit options (same as fetch).
 * @returns The Response object (same as fetch).
 * @throws On network errors.
 */
export async function apiFetch(
    input: RequestInfo | URL,
    init: RequestInit = {}
): Promise<Response> {
    const response = await fetch(input, {
        ...init,
        credentials: "include", // Always send HTTPOnly cookies
    });

    if (response.status === 401) {
        redirectToLogin();
        // Return the response anyway so callers don't crash, but the redirect
        // means this code path is effectively terminal.
        return response;
    }

    return response;
}

/**
 * Streaming variant — wraps `apiFetch` for SSE endpoints.
 * Throws an error with a user-friendly message if the server returns 401.
 */
export async function apiStream(
    input: RequestInfo | URL,
    init: RequestInit = {}
): Promise<Response> {
    const response = await fetch(input, {
        ...init,
        credentials: "include",
    });

    if (response.status === 401) {
        redirectToLogin();
        throw new Error("Sesión expirada. Redirigiendo al login...");
    }

    return response;
}
