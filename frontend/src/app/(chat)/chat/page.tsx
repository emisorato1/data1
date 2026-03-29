"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { MessageBubble, Message, Source } from "@/components/chat/message-bubble";
import { MessageInput } from "@/components/chat/message-input";
import { SourcePanel } from "@/components/chat/source-panel";
import { ChatHeader } from "@/components/chat/chat-header";
import { streamChat } from "@/lib/sse-client";
import { apiFetch } from "@/lib/api-client";
import { useChatContext } from "@/context/chat-context";
import { useResizablePanel } from "@/hooks/useResizablePanel";
import Image from "next/image";
import { cn } from "@/lib/utils";

export default function ChatPage() {
    const { currentConversationId, setCurrentConversationId, refreshConversations } = useChatContext();
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const skipLoadRef = useRef(false);

    // Source panel state
    const [selectedSource, setSelectedSource] = useState<Source | null>(null);
    const [allSourcesForPanel, setAllSourcesForPanel] = useState<Source[]>([]);
    const [activeCitationIndex, setActiveCitationIndex] = useState<number | null>(null);

    // Resizable panel
    const { width: panelWidth, isDragging, startDragging } = useResizablePanel();

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, []);

    const closeSourcePanel = useCallback(() => {
        setSelectedSource(null);
        setAllSourcesForPanel([]);
        setActiveCitationIndex(null);
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, scrollToBottom]);

    // Load messages when conversation changes
    useEffect(() => {
        if (skipLoadRef.current) {
            skipLoadRef.current = false;
            return;
        }

        if (!currentConversationId) {
            setMessages([]);
            closeSourcePanel();
            return;
        }

        const loadMessages = async () => {
            try {
                const res = await apiFetch(`/api/v1/conversations/${currentConversationId}`);
                if (res.ok) {
                    const result = await res.json();
                    const items = result.data?.messages || [];
                    setMessages(
                        items.map((m: Record<string, unknown>) => ({
                            id: m.id as string,
                            role: m.role as "user" | "assistant",
                            content: m.content as string,
                            sources: ((m.sources as Record<string, unknown>)?.items as Source[]) || [],
                        }))
                    );
                }
            } catch (err) {
                console.error("Error cargando mensajes:", err);
            }
        };

        loadMessages();
    }, [currentConversationId, closeSourcePanel]);

    const handleSourceBadgeClick = useCallback((documentName: string, sources: Source[]) => {
        // If clicking the same document that's already shown, toggle off
        if (selectedSource && selectedSource.document_name === documentName) {
            closeSourcePanel();
        } else {
            // Open panel with the first source for this document
            const source = sources.find((s) => s.document_name === documentName);
            if (source) {
                setSelectedSource(source);
                setAllSourcesForPanel(sources);
                setActiveCitationIndex(source.index);
            }
        }
    }, [selectedSource, closeSourcePanel]);

    const handleCitationClick = useCallback((_index: number, source: Source) => {
        // Find the message that contains this source to get all sources
        const parentMessage = messages.find(
            (m) => m.sources?.some((s) => s.index === source.index && s.document_name === source.document_name)
        );
        const allSources = parentMessage?.sources || [source];

        if (activeCitationIndex === source.index) {
            // Toggle off if clicking the same citation
            closeSourcePanel();
        } else {
            setSelectedSource(source);
            setAllSourcesForPanel(allSources);
            setActiveCitationIndex(source.index);
        }
    }, [messages, activeCitationIndex, closeSourcePanel]);

    const handleSelectSourceFromPanel = useCallback((index: number) => {
        const source = allSourcesForPanel.find((s) => s.index === index);
        if (source) {
            setSelectedSource(source);
            setActiveCitationIndex(index);
        }
    }, [allSourcesForPanel]);

    const handleSend = async (query: string) => {
        let conversationId = currentConversationId;

        // Close source panel when sending a new message
        closeSourcePanel();

        if (!conversationId) {
            try {
                const res = await apiFetch("/api/v1/conversations", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ title: query.slice(0, 50) }),
                });
                const result = await res.json();
                if (res.ok && result.data?.id) {
                    conversationId = result.data.id;
                    skipLoadRef.current = true;
                    setCurrentConversationId(conversationId);
                    refreshConversations();
                } else {
                    throw new Error("No se pudo iniciar la conversacion");
                }
            } catch {
                setMessages(prev => [...prev, {
                    id: "error-init",
                    role: "assistant",
                    content: "No se pudo establecer la sesión. Verifica tu conexion."
                }]);
                return;
            }
        }

        const userMsg: Message = {
            id: Date.now().toString(),
            role: "user",
            content: query,
        };

        const assistantMsgId = (Date.now() + 1).toString();
        const assistantMsg: Message = {
            id: assistantMsgId,
            role: "assistant",
            content: "",
            isStreaming: true,
        };

        setMessages((prev) => [...prev, userMsg, assistantMsg]);
        setIsLoading(true);

        try {
            const stream = streamChat(query, conversationId!);

            for await (const { event, data } of stream) {
                if (event === "token") {
                    const content = typeof data === "string" ? data : data?.content || "";
                    setMessages((prev) =>
                        prev.map((msg) =>
                            msg.id === assistantMsgId
                                ? { ...msg, content: msg.content + content }
                                : msg
                        )
                    );
                } else if (event === "done") {
                    const sources = data?.sources || [];
                    setMessages((prev) =>
                        prev.map((msg) =>
                            msg.id === assistantMsgId
                                ? { ...msg, isStreaming: false, sources }
                                : msg
                        )
                    );
                }
            }
        } catch {
            setMessages((prev) =>
                prev.map((msg) =>
                    msg.id === assistantMsgId
                        ? { ...msg, content: "Error de conexion. Reintenta la consulta.", isStreaming: false }
                        : msg
                )
            );
        } finally {
            setIsLoading(false);
        }
    };

    const isNewChat = messages.length === 0;

    return (
        <div className="flex-1 flex h-full bg-background relative overflow-hidden">
            {/* Main chat area */}
            <div className="flex-1 flex flex-col h-full min-w-0 relative">
                {/* Header */}
                <ChatHeader />

                {/* Messages area - scrollable */}
                <div className="flex-1 overflow-y-auto scrollbar-hide">
                    {isNewChat ? (
                        /* Empty state — greeting + prompter centrados verticalmente */
                        <div className="h-full flex flex-col items-center justify-center px-4 py-8">
                            <div className="text-center animate-in fade-in zoom-in-95 duration-700 delay-150 mb-8 w-full max-w-5xl">
                                <div className="relative mb-6 flex justify-center">
                                    <div className="absolute inset-0 bg-primary/5 rounded-full blur-[60px] scale-[1.5]" />
                                    <Image src="/isologo-macro.svg" alt="Banco Macro" width={300} height={60} className="relative z-10 opacity-80" priority />
                                </div>
                                <h1 className="text-2xl font-semibold mb-8" style={{ color: "#2D5FFF" }}>
                                    Hola, soy <span className="font-bold">Eme</span> ¿En qué puedo ayudarte?
                                </h1>
                                {/* Prompter centrado junto al greeting */}
                                <MessageInput
                                    onSend={handleSend}
                                    onStop={() => setIsLoading(false)}
                                    isLoading={isLoading}
                                />
                            </div>
                        </div>
                    ) : (
                        /* Mensajes */
                        <div className="w-full max-w-5xl mx-auto px-4 md:px-6 py-8 md:py-12 animate-in fade-in duration-500">
                            {messages.map((msg) => (
                                <MessageBubble
                                    key={msg.id}
                                    message={msg}
                                    activeCitationIndex={activeCitationIndex}
                                    onCitationClick={handleCitationClick}
                                    onSourceBadgeClick={handleSourceBadgeClick}
                                />
                            ))}
                            <div ref={messagesEndRef} className="h-2" />
                        </div>
                    )}
                </div>

                {/* Input footer — solo cuando hay mensajes, sibling del scroll, nunca se superpone */}
                {!isNewChat && (
                    <div className="relative z-10 flex-shrink-0 border-t border-border/40">
                        <div className="absolute inset-x-0 top-0 h-6 -translate-y-full bg-gradient-to-t from-background to-transparent pointer-events-none" />
                        <div className="w-full max-w-5xl mx-auto px-4 md:px-6">
                            <MessageInput
                                onSend={handleSend}
                                onStop={() => setIsLoading(false)}
                                isLoading={isLoading}
                            />
                        </div>
                    </div>
                )}
            </div>

            {/* Source panel (right side, resizable) */}
            {selectedSource && (
                <SourcePanel
                    source={selectedSource}
                    sources={allSourcesForPanel}
                    onClose={closeSourcePanel}
                    onSelectSource={handleSelectSourceFromPanel}
                    width={panelWidth}
                    onGutterMouseDown={startDragging}
                    isDragging={isDragging}
                />
            )}
        </div>
    );
}