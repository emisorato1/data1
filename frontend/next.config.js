/** @type {import('next').NextConfig} */
const nextConfig = {
    // Standalone output para Docker (reduce imagen de ~1GB a ~100MB)
    output: 'standalone',

    // API proxy via Route Handler (src/app/api/[...path]/route.ts)
    // que propaga Set-Cookie headers correctamente (requerido por ADR-006).
    // SSE streaming va directo al backend via NEXT_PUBLIC_BACKEND_URL (ADR-003).
};

module.exports = nextConfig;
