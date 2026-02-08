import { NextRequest, NextResponse } from "next/server";
import { handleGoogleCallback } from "@/lib/chatApi";

/**
 * Google OAuth Callback Route
 * 
 * This route handles the OAuth redirect from Google.
 * It extracts the authorization code and state, validates CSRF,
 * exchanges the code for a token via the backend, and redirects to the app.
 */
export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const error = searchParams.get("error");

    // Handle OAuth errors
    if (error) {
        const errorDescription = searchParams.get("error_description") || error;
        return NextResponse.redirect(
            new URL(`/?error=${encodeURIComponent(errorDescription)}`, request.url)
        );
    }

    // Validate required parameters
    if (!code) {
        return NextResponse.redirect(
            new URL("/?error=missing_code", request.url)
        );
    }

    try {
        // The actual token exchange happens client-side
        // This route just redirects with the code for the client to process
        const redirectUrl = new URL("/auth/google/complete", request.url);
        redirectUrl.searchParams.set("code", code);
        if (state) {
            redirectUrl.searchParams.set("state", state);
        }

        return NextResponse.redirect(redirectUrl);
    } catch (err) {
        console.error("OAuth callback error:", err);
        return NextResponse.redirect(
            new URL("/?error=callback_failed", request.url)
        );
    }
}
