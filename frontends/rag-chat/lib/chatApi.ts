/**
 * Chat API Client
 * 
 * Funciones para interactuar con el API Gateway de la plataforma.
 * Maneja autenticación, threads y mensajes.
 */

import type { LangChainMessage } from "@assistant-ui/react-langgraph";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";

// ============================================================================
// Token Management (ahora manejado por cookies HttpOnly)
// ============================================================================

export function getAuthToken(): string | null {
  // Con cookies HttpOnly, no podemos leer el token directamente
  // Usamos un flag en sessionStorage para saber si el usuario hizo login
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("is_authenticated") ? "cookie" : null;
}

function setAuthenticated(value: boolean): void {
  if (value) {
    sessionStorage.setItem("is_authenticated", "true");
  } else {
    sessionStorage.removeItem("is_authenticated");
  }
}

export function getUserRole(): string {
  if (typeof window === "undefined") return "public";
  return sessionStorage.getItem("user_role") || "public";
}

// ============================================================================
// Auth Functions
// ============================================================================

export async function login(email: string, password: string): Promise<void> {
  const res = await fetch(`${API_URL}${API_PREFIX}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include", // Importante para recibir cookies
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Error al iniciar sesión");
  }

  // La cookie ya fue seteada por el backend
  setAuthenticated(true);

  // Obtener info del usuario para guardar el rol
  await fetchAndStoreUserInfo();
}

export async function register(email: string, password: string): Promise<void> {
  const res = await fetch(`${API_URL}${API_PREFIX}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      tenant_id: "00000000-0000-0000-0000-000000000001",
    }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Error al registrarse");
  }

  // Registro exitoso - el usuario debe hacer login manualmente
}

export async function logout(): Promise<void> {
  try {
    await fetch(`${API_URL}${API_PREFIX}/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
  } catch (e) {
    console.error("Error during logout:", e);
  }
  setAuthenticated(false);
  sessionStorage.removeItem("user_role");
}

async function fetchAndStoreUserInfo(): Promise<void> {
  try {
    const res = await fetch(`${API_URL}${API_PREFIX}/auth/me`, {
      credentials: "include", // Enviar cookie
    });

    if (res.ok) {
      const user = await res.json();
      const role = user.role;
      if (role === "private" || role === "admin") {
        sessionStorage.setItem("user_role", "private");
      } else {
        sessionStorage.setItem("user_role", "public");
      }
    }
  } catch (error) {
    console.error("Error fetching user info:", error);
  }
}

// ============================================================================
// Google OAuth Functions
// ============================================================================

interface GoogleAuthUrlResponse {
  auth_url: string;
  state: string;
}

/**
 * Get Google OAuth authorization URL from backend.
 * The frontend should redirect the user to this URL.
 */
export async function getGoogleAuthUrl(): Promise<GoogleAuthUrlResponse> {
  const res = await fetch(`${API_URL}${API_PREFIX}/auth/google/url`);

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Error al obtener URL de Google");
  }

  return res.json();
}

/**
 * Handle Google OAuth callback - exchange code for JWT token.
 * @param code - Authorization code from Google
 * @param state - State parameter for CSRF validation (optional)
 */
export async function handleGoogleCallback(
  code: string,
  state?: string
): Promise<void> {
  const res = await fetch(`${API_URL}${API_PREFIX}/auth/google/callback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include", // Importante para recibir cookies
    body: JSON.stringify({ code, state }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Error en autenticación con Google");
  }

  // La cookie ya fue seteada por el backend
  setAuthenticated(true);

  // Store user role
  await fetchAndStoreUserInfo();
}

/**
 * Initiate Google OAuth flow by redirecting to Google.
 * Saves state in sessionStorage for CSRF validation.
 */
export async function initiateGoogleLogin(): Promise<void> {
  const { auth_url, state } = await getGoogleAuthUrl();

  // Save state for CSRF validation in callback
  if (typeof window !== "undefined") {
    sessionStorage.setItem("google_oauth_state", state);
  }

  // Redirect to Google
  window.location.href = auth_url;
}

// ============================================================================
// Thread/Chat Functions
// ============================================================================

export async function createThread(): Promise<{ thread_id: string }> {
  // Generamos un thread_id local (UUID v4)
  const threadId = crypto.randomUUID();
  return { thread_id: threadId };
}

export async function getThreadState(
  threadId: string
): Promise<{ messages: LangChainMessage[] }> {
  // Por ahora retornamos un estado vacío
  // En el futuro se puede implementar persistencia de conversaciones
  return { messages: [] };
}

// Helper para extraer el contenido como string
function extractContent(content: string | unknown[]): string {
  if (typeof content === "string") {
    return content;
  }
  // Si es un array, extraer el texto de los items
  return content
    .map((item) => {
      if (typeof item === "string") return item;
      if (typeof item === "object" && item !== null && "text" in item) {
        return (item as { text: string }).text;
      }
      return "";
    })
    .join("");
}

export async function* sendMessage(params: {
  threadId: string;
  messages: LangChainMessage[];
  command?: unknown;
}): AsyncGenerator<string, void, unknown> {
  const userRole = getUserRole();
  const lastMessage = params.messages[params.messages.length - 1];

  const res = await fetch(`${API_URL}${API_PREFIX}/chatbot/stream?session_id=${params.threadId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include", // Enviar cookie HttpOnly
    body: JSON.stringify({
      session_id: params.threadId,
      message: extractContent(lastMessage.content),
      user_role: userRole,
    }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Error desconocido" }));
    throw new Error(error.detail || "Error al enviar mensaje");
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";
  let fullResponse = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const dataStr = line.slice(6);
          try {
            const data = JSON.parse(dataStr);

            // Verificar si es evento de contenido
            if (data.content !== undefined) {
              // El backend manda chunks, no el texto completo acumulado (excepto si fuera un done event con content=full)
              // Pero mi logica de ChatService manda chunks.
              // El frontend (assistant-ui o lo que use) espera el texto "acumulado" o "chunk"? 
              // AsyncGenerator espera yield string.
              // Si el componente de UI acumula, yield chunks es mejor.
              // SI el componente espera el texto completo en cada yield, debo acumular.
              // "assistant-ui/react-langgraph" useStream suele acumular? 
              // Revisemos la implementacion original. `data.assistant_message.content` era el full text. `yield response` una vez.
              // Si yield "H", "e", "l", "l", "o".
              // Si el UI solo reemplaza el ultimo mensaje con lo que recibe, entonces necesito acumular.
              // Si el UI hace append, envio chunks.
              // Asumamos que necesito ACUMULAR para ser seguro (React state update suele reemplazar).

                          if (data.done) {
                                // Si trae sources válidas, append to fullResponse
                                const sources = data.sources || [];
                                // Filtrar sources válidas (que tengan nombre)
                                const validSources = sources.filter((source: Record<string, unknown>) => {
                                  const name = source.source_name || source.name || source.title;
                                  return name && name !== "undefined" && name !== "unknown";
                                });
                                
                                if (validSources.length > 0) {
                                  let sourceText = "\n\n📚 **Fuentes consultadas:**\n";
                                  for (const source of validSources) {
                                    const sourceName = source.source_name || source.name || source.title || "Documento";
                                    sourceText += `- [Fuente: ${sourceName}]`;
                                    if (source.score && !isNaN(Number(source.score))) {
                                      sourceText += ` (relevancia: ${(Number(source.score) * 100).toFixed(0)}%)`;
                                    }
                                    sourceText += "\n";
                                  }
                                  fullResponse += sourceText;
                                  yield fullResponse;
                                }
                                // Si no hay sources válidas, simplemente no agregamos nada
                              } else {
                                fullResponse += data.content;
                                yield fullResponse;
                              }
            }
          } catch (e) {
            console.error("Error parsing JSON SSE", e);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
