"use client";

import React, {
    createContext,
    useContext,
    useState,
    useCallback,
    useRef,
} from "react";
import { apiFetch } from "@/lib/api-client";

export interface Conversation {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
    is_pinned: boolean;
    is_favorite: boolean;
}

interface ChatContextType {
    conversations: Conversation[];
    currentConversationId: string | null;
    setCurrentConversationId: (id: string | null) => void;
    refreshConversations: () => Promise<void>;
    loadMoreConversations: () => Promise<void>;
    startNewConversation: () => void;
    removeConversation: (convId: string) => void;
    updateConversationTitle: (convId: string, title: string) => void;
    updateConversationPinFavorite: (convId: string, is_pinned?: boolean, is_favorite?: boolean) => void;
    isLoadingConversations: boolean;
    isLoadingMore: boolean;
    hasMoreConversations: boolean;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const PAGE_SIZE = 20;

export function ChatProvider({ children }: { children: React.ReactNode }) {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [currentConversationId, setCurrentConversationId] = useState<
        string | null
    >(null);
    const [isLoadingConversations, setIsLoadingConversations] = useState(false);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [hasMoreConversations, setHasMoreConversations] = useState(false);
    const nextCursorRef = useRef<string | null>(null);

    const refreshConversations = useCallback(async () => {
        setIsLoadingConversations(true);
        try {
            const res = await apiFetch(
                `/api/v1/conversations?limit=${PAGE_SIZE}`,
            );
            if (res.ok) {
                const result = await res.json();
                const page = result.data;
                setConversations(page?.items ?? []);
                nextCursorRef.current = page?.next_cursor ?? null;
                setHasMoreConversations(page?.has_more ?? false);
            }
        } catch (err) {
            console.error("Error cargando conversaciones:", err);
        } finally {
            setIsLoadingConversations(false);
        }
    }, []);

    const loadMoreConversations = useCallback(async () => {
        if (!nextCursorRef.current || isLoadingMore) return;

        setIsLoadingMore(true);
        try {
            const res = await apiFetch(
                `/api/v1/conversations?limit=${PAGE_SIZE}&cursor=${encodeURIComponent(nextCursorRef.current)}`,
            );
            if (res.ok) {
                const result = await res.json();
                const page = result.data;
                const newItems: Conversation[] = page?.items ?? [];
                setConversations((prev) => [...prev, ...newItems]);
                nextCursorRef.current = page?.next_cursor ?? null;
                setHasMoreConversations(page?.has_more ?? false);
            }
        } catch (err) {
            console.error("Error cargando mas conversaciones:", err);
        } finally {
            setIsLoadingMore(false);
        }
    }, [isLoadingMore]);

    const startNewConversation = useCallback(() => {
        setCurrentConversationId(null);
    }, []);

        const updateConversationPinFavorite = useCallback((convId: string, is_pinned?: boolean, is_favorite?: boolean) => {
        setConversations(prev => 
            prev.map(conv => {
                if (conv.id === convId) {
                    return {
                        ...conv,
                        ...(is_pinned !== undefined && { is_pinned }),
                        ...(is_favorite !== undefined && { is_favorite })
                    };
                }
                return conv;
            })
        );
    }, []);

    const updateConversationTitle = useCallback((convId: string, newTitle: string) => {
        setConversations((prev) => 
            prev.map(c => c.id === convId ? { ...c, title: newTitle } : c)
        );
    }, []);

    const removeConversation = useCallback((convId: string) => {
        setConversations((prev) => prev.filter((c) => c.id !== convId));
    }, []);

    return (
        <ChatContext.Provider
                        value={{
                conversations,
                currentConversationId,
                setCurrentConversationId,
                refreshConversations,
                loadMoreConversations,
                startNewConversation,
                removeConversation,
                updateConversationTitle,
                updateConversationPinFavorite,
                isLoadingConversations,
                isLoadingMore,
                hasMoreConversations,
            }}
        >
            {children}
        </ChatContext.Provider>
    );
}

export function useChatContext() {
    const ctx = useContext(ChatContext);
    if (!ctx) throw new Error("useChatContext must be used within ChatProvider");
    return ctx;
}
