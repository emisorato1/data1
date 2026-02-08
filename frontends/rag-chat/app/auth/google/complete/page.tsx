"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { handleGoogleCallback } from "@/lib/chatApi";

function GoogleAuthContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [error, setError] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState(true);

    useEffect(() => {
        async function processCallback() {
            const code = searchParams.get("code");
            const state = searchParams.get("state");

            if (!code) {
                setError("Código de autorización no encontrado");
                setIsProcessing(false);
                return;
            }

            // Validate state for CSRF protection
            const savedState = sessionStorage.getItem("google_oauth_state");
            if (state && savedState && state !== savedState) {
                setError("Error de seguridad: state no coincide");
                setIsProcessing(false);
                return;
            }

            try {
                // Exchange code for token
                await handleGoogleCallback(code, state || undefined);

                // Clear saved state
                sessionStorage.removeItem("google_oauth_state");

                // Redirect to main app
                router.push("/");
            } catch (err) {
                console.error("Google auth error:", err);
                setError(err instanceof Error ? err.message : "Error de autenticación");
                setIsProcessing(false);
            }
        }

        processCallback();
    }, [searchParams, router]);

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-900">
                <div className="bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full">
                    <div className="text-center">
                        <div className="text-red-500 text-5xl mb-4">⚠️</div>
                        <h1 className="text-xl font-semibold text-white mb-2">
                            Error de autenticación
                        </h1>
                        <p className="text-gray-400 mb-6">{error}</p>
                        <button
                            onClick={() => router.push("/")}
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                        >
                            Volver al inicio
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-900">
            <div className="bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <h1 className="text-xl font-semibold text-white mb-2">
                        Completando autenticación...
                    </h1>
                    <p className="text-gray-400">
                        Por favor espera mientras procesamos tu inicio de sesión con Google.
                    </p>
                </div>
            </div>
        </div>
    );
}

/**
 * Google OAuth Completion Page
 * 
 * This page handles the final step of the OAuth flow:
 * 1. Extracts code and state from URL
 * 2. Validates state against stored value (CSRF)
 * 3. Exchanges code for token via backend
 * 4. Redirects to main app on success
 */
export default function GoogleAuthComplete() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center bg-gray-900">
                <div className="bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
                        <h1 className="text-xl font-semibold text-white mb-2">
                            Cargando...
                        </h1>
                    </div>
                </div>
            </div>
        }>
            <GoogleAuthContent />
        </Suspense>
    );
}
