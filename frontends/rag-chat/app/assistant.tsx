"use client";

import { useRef } from "react";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useLangGraphRuntime } from "@assistant-ui/react-langgraph";
import type { LangChainMessage, LangGraphCommand, LangGraphMessagesEvent } from "@assistant-ui/react-langgraph";

import { getThreadState, sendMessage } from "@/lib/chatApi";
import { Thread } from "@/components/assistant-ui/thread";
import { LogoutButton } from "@/components/auth/LogoutButton";

export function Assistant() {
  // Thread ID persistente para toda la sesión del componente.
  // Se genera UNA sola vez al montar y se reutiliza en todos los mensajes.
  const threadIdRef = useRef<string | null>(null);
  if (!threadIdRef.current) {
    threadIdRef.current = crypto.randomUUID();
  }

  const runtime = useLangGraphRuntime({
    stream: async function* (
      messages: LangChainMessage[],
      { initialize, command }: { initialize: () => Promise<{ externalId?: string }>, command?: LangGraphCommand }
    ): AsyncGenerator<LangGraphMessagesEvent<LangChainMessage>, void, unknown> {
      const initResult = await initialize();
      // Usar el externalId del runtime si existe, sino el ref persistente
      const externalId = initResult?.externalId || threadIdRef.current!;

      // Filtrar mensajes de tipo "system" que no son soportados por el backend
      const filteredMessages = messages.filter(
        (msg): msg is LangChainMessage & { type: "human" | "ai" } =>
          msg.type === "human" || msg.type === "ai"
      );

      const generator = await sendMessage({
        threadId: externalId,
        messages: filteredMessages,
        command,
      });

      // Convert backend stream chunks to LangGraph events
      // NOTE: chatApi.ts sendMessage already yields ACCUMULATED content,
      // so each 'chunk' here is actually the full response so far
      const messageId = `msg-${Date.now()}`;
      let lastContent = "";

      for await (const chunk of generator) {
        // chunk is already the full accumulated content from chatApi
        lastContent = chunk;
        // Yield partial messages event with the accumulated content
        yield {
          event: "messages/partial" as const,
          data: [
            {
              type: "ai",
              content: chunk,
              id: messageId,
            } as LangChainMessage,
          ],
        };
      }

      // Yield complete message event
      yield {
        event: "messages/complete" as const,
        data: [
          {
            type: "ai",
            content: lastContent,
            id: messageId,
          } as LangChainMessage,
        ],
      };
    },
    create: async () => {
      // Retornar siempre el mismo threadId persistente
      return { externalId: threadIdRef.current! };
    },
    load: async (externalId: string) => {
      const state = await getThreadState(externalId);
      return {
        messages: state.messages,
      };
    },
  });

  return (
    <div className="relative h-full">
      <div className="absolute top-4 right-4 z-50">
        <LogoutButton />
      </div>
      <AssistantRuntimeProvider runtime={runtime}>
        <Thread />
      </AssistantRuntimeProvider>
    </div>
  );
}