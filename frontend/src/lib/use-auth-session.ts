/**
 * useAuthSession — Silent Token Refresh Hook
 *
 * Mounts once in the root layout and silently refreshes the access_token
 * ~2 minutes before it expires (access token lives 15min → refresh at 13min).
 *
 * Strategy:
 *   - On mount: schedule a refresh after REFRESH_BEFORE_EXPIRY_MS
 *   - After each successful refresh: reschedule for the next cycle
 *   - On 401 from refresh endpoint: redirect to /login (refresh_token also expired)
 *   - On any tab becoming visible after being hidden: re-check proactively
 *
 * The hook is completely silent — the user never sees any loading indicator.
 */

"use client";

import { useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";

/** Access token lifetime in ms — must match backend ACCESS_TOKEN_EXPIRE_MINUTES (15min) */
const ACCESS_TOKEN_LIFETIME_MS = 15 * 60 * 1000;

/**
 * How early (in ms) to refresh before the token expires.
 * 2 minutes gives plenty of buffer for slow networks.
 */
const REFRESH_BEFORE_EXPIRY_MS = 2 * 60 * 1000;

/** Interval between proactive refreshes: 15min - 2min = 13min */
const REFRESH_INTERVAL_MS = ACCESS_TOKEN_LIFETIME_MS - REFRESH_BEFORE_EXPIRY_MS;

/** Backend base URL for auth calls (same origin via Next.js proxy) */
const REFRESH_URL = "/api/v1/auth/refresh";

export function useAuthSession(): void {
    const router = useRouter();
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const isMountedRef = useRef(true);

    const redirectToLogin = useCallback(() => {
        router.replace("/login?reason=session_expired");
    }, [router]);

    const scheduleRefresh = useCallback(
        (delayMs: number) => {
            if (timerRef.current) clearTimeout(timerRef.current);

            timerRef.current = setTimeout(async () => {
                if (!isMountedRef.current) return;

                try {
                    const res = await fetch(REFRESH_URL, {
                        method: "POST",
                        credentials: "include", // send refresh_token cookie
                    });

                    if (!isMountedRef.current) return;

                    if (res.ok) {
                        // New access_token cookie is now set by the server.
                        // Schedule the next refresh cycle.
                        scheduleRefresh(REFRESH_INTERVAL_MS);
                    } else if (res.status === 401) {
                        // refresh_token is also expired or revoked → force login
                        redirectToLogin();
                    }
                    // Other errors (5xx, network) are ignored — the next user action
                    // will trigger a 401 via apiFetch and redirect then.
                } catch {
                    // Network error — silent, will be caught on next user action
                }
            }, delayMs);
        },
        [redirectToLogin]
    );

    useEffect(() => {
        isMountedRef.current = true;

        // Start the refresh cycle slightly before first expiry
        scheduleRefresh(REFRESH_INTERVAL_MS);

        // When the user returns to a hidden tab, refresh immediately if needed.
        // (The timer may have fired while the tab was throttled by the browser.)
        const handleVisibilityChange = () => {
            if (document.visibilityState === "visible") {
                scheduleRefresh(0); // Try immediately on tab focus
            }
        };

        document.addEventListener("visibilitychange", handleVisibilityChange);

        return () => {
            isMountedRef.current = false;
            if (timerRef.current) clearTimeout(timerRef.current);
            document.removeEventListener("visibilitychange", handleVisibilityChange);
        };
    }, [scheduleRefresh]);
}
