/**
 * Cliente para el manejo de Server-Sent Events (SSE).
 * Usa la API fetch + ReadableStream para mayor flexibilidad con headers y POST.
 */

import { apiStream } from "./api-client";

export interface ChatEvent {
    event: "token" | "metadata" | "error" | "done";
    data: any;
}

export async function* streamChat(
    query: string,
    conversationId: string
): AsyncGenerator<ChatEvent> {
    // SSE directo al backend FastAPI (el proxy de Next.js bufferéa SSE)
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
    // apiStream maneja 401 → redirect automático al login
    const response = await apiStream(`${backendUrl}/api/v1/conversations/${conversationId}/messages`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            message: query,
        }),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ message: "Error desconocido" }));
        throw new Error(error.error?.message || "Error al conectar con el servidor de chat");
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No se pudo inicializar el stream");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Normalizar saltos de línea y separar eventos por el estándar SSE (\n\n o \r\n\r\n)
        const parts = buffer.split(/\n\n|\r\n\r\n/);
        buffer = parts.pop() || ""; // Mantener el último fragmento incompleto en el buffer

        for (const part of parts) {
            if (!part.trim()) continue;

            const lines = part.split(/\r?\n/);
            let eventType: any = "token";
            let dataPayload = "";

            for (const line of lines) {
                if (line.startsWith("event: ")) {
                    eventType = line.replace("event: ", "").trim();
                } else if (line.startsWith("data: ")) {
                    dataPayload = line.replace("data: ", "").trim();
                }
            }

            console.log(`[SSE-Client] Event: ${eventType}, Data: ${dataPayload.substring(0, 50)}...`);

            if (dataPayload) {
                try {
                    const parsed = JSON.parse(dataPayload);
                    // Si es un objeto de Token de LangChain {"content": "..."}
                    if (parsed && typeof parsed === 'object' && 'content' in parsed) {
                        yield { event: eventType as any, data: parsed.content };
                    } else {
                        yield { event: eventType as any, data: parsed };
                    }
                } catch (e) {
                    // Si no es JSON (token puro), enviarlo tal cual
                    yield { event: eventType as any, data: dataPayload };
                }
            }
        }
    }
}
