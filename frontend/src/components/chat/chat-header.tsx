"use client";

import React from "react";
import { useChatContext } from "@/context/chat-context";

export function ChatHeader() {
    const { conversations, currentConversationId } = useChatContext();

    const currentConversation = conversations.find(c => c.id === currentConversationId);

    if (!currentConversation) {
        return (
            <header className="sticky top-0 z-10 border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="flex items-center justify-between px-6 h-[72px]">
                    <h1 className="text-lg font-semibold text-foreground">
                        Nueva Consulta
                    </h1>
                </div>
            </header>
        );
    }

    return (
        <header className="sticky top-0 z-10 border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="flex items-center justify-between px-6 h-[72px]">
                <h1 className="text-lg font-semibold text-foreground truncate">
                    {currentConversation.title || "Sin título"}
                </h1>
            </div>
        </header>
    );
}
