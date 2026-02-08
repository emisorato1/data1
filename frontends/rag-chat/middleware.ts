/**
 * Next.js Middleware para protección de rutas
 * 
 * Este middleware se ejecuta ANTES de que se cargue cualquier página.
 * Verifica si el usuario tiene la cookie de autenticación y redirige
 * según sea necesario.
 * 
 * Flujo:
 * 1. Usuario visita una ruta protegida (ej: /)
 * 2. Middleware verifica si existe la cookie `eai_access_token`
 * 3. Si no hay cookie → Redirige a /auth/login
 * 4. Si hay cookie → Permite el acceso
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Nombre de la cookie de autenticación (debe coincidir con el backend)
const AUTH_COOKIE_NAME = "eai_access_token";

// Rutas públicas que NO requieren autenticación
const PUBLIC_ROUTES = [
    "/auth/login",
    "/auth/register",
    "/auth/google",
];

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // No procesar archivos estáticos ni rutas de API
    if (
        pathname.startsWith("/_next") ||
        pathname.startsWith("/api") ||
        pathname.startsWith("/favicon") ||
        pathname.includes(".")
    ) {
        return NextResponse.next();
    }

    // Verificar si existe la cookie de autenticación
    const authCookie = request.cookies.get(AUTH_COOKIE_NAME);
    const isAuthenticated = !!authCookie?.value;

    // Verificar si la ruta actual es pública (login, register, etc.)
    const isPublicRoute = PUBLIC_ROUTES.some((route) =>
        pathname.startsWith(route)
    );

    // CASO 1: Usuario NO autenticado intenta acceder a ruta protegida
    if (!isPublicRoute && !isAuthenticated) {
        // Guardar la URL original para redirigir después del login
        const loginUrl = new URL("/auth/login", request.url);
        if (pathname !== "/") {
            loginUrl.searchParams.set("callbackUrl", pathname);
        }
        return NextResponse.redirect(loginUrl);
    }

    // CASO 2: Usuario AUTENTICADO intenta acceder a login/register
    if (isPublicRoute && isAuthenticated) {
        // Redirigir a la página principal
        return NextResponse.redirect(new URL("/", request.url));
    }

    // En cualquier otro caso, permitir el acceso
    return NextResponse.next();
}

// Configuración: en qué rutas se ejecuta el middleware
export const config = {
    matcher: [
        /*
         * Match all request paths except:
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         */
        "/((?!_next/static|_next/image|favicon.ico).*)",
    ],
};
