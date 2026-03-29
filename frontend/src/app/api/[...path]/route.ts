/**
 * Catch-all Route Handler — proxies /api/* requests to FastAPI backend.
 *
 * Unlike Next.js rewrites, Route Handlers correctly propagate Set-Cookie
 * headers from the upstream response back to the browser.  This is critical
 * for the HTTPOnly cookie auth flow (ADR-006).
 *
 * SSE streaming is intentionally NOT proxied here — the SSE client
 * (sse-client.ts) calls the backend directly to avoid buffering (ADR-003).
 *
 * Environment variables (resolved at runtime, server-side only):
 *   BACKEND_INTERNAL_URL — Docker/K8s internal URL (e.g. http://backend:8000)
 *   NEXT_PUBLIC_BACKEND_URL — fallback (works in local dev without Docker)
 */

import { NextRequest, NextResponse } from "next/server";

// Server-side only: prefer internal Docker/K8s DNS name for container-to-container calls.
// Falls back to NEXT_PUBLIC_BACKEND_URL (useful in local dev where everything is localhost).
const BACKEND_URL =
  process.env.BACKEND_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "http://localhost:8000";

async function proxyRequest(req: NextRequest): Promise<NextResponse> {
  // Build the upstream URL preserving path and query string
  const { pathname, search } = req.nextUrl;
  const upstream = `${BACKEND_URL}${pathname}${search}`;

  // Forward relevant headers (strip host — we're proxying)
  const headers = new Headers(req.headers);
  headers.delete("host");

  // Forward the request body for methods that have one
  const hasBody = !["GET", "HEAD"].includes(req.method);
  const body = hasBody ? await req.arrayBuffer() : undefined;

  const upstreamResponse = await fetch(upstream, {
    method: req.method,
    headers,
    body,
    cache: "no-store",
  });

  // Copy ALL headers from the upstream response (including Set-Cookie)
  const responseHeaders = new Headers();
  upstreamResponse.headers.forEach((value, key) => {
    responseHeaders.append(key, value);
  });

  // Remove hop-by-hop headers that should not be forwarded
  responseHeaders.delete("transfer-encoding");

  return new NextResponse(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers: responseHeaders,
  });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const DELETE = proxyRequest;
export const PATCH = proxyRequest;
export const OPTIONS = proxyRequest;
export const HEAD = proxyRequest;
