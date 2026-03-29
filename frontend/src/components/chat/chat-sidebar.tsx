"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import {
    Plus,
    Loader2,
    LogOut,
    ChevronLeft,
    ChevronRight,
    MessageSquare,
    Pin,
    Star,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useChatContext } from "@/context/chat-context";
import { ConversationItem } from "@/components/chat/conversation-item";
import { useRouter } from "next/navigation";
import { ThemeToggle } from "@/components/theme-toggle";
import Image from "next/image";

const COLLAPSED_KEY = "sidebar_collapsed";

/** Tooltip visible only when sidebar is collapsed */
function Tooltip({
    label,
    children,
}: {
    label: string;
    children: React.ReactNode;
}) {
    return (
        <div className="relative group/tip">
            {children}
            <div
                className="
                pointer-events-none absolute left-full top-1/2 -translate-y-1/2 ml-3 z-50
                px-2.5 py-1.5 rounded-lg bg-popover border border-border text-foreground
                text-[12px] font-medium whitespace-nowrap shadow-lg
                opacity-0 group-hover/tip:opacity-100
                translate-x-1 group-hover/tip:translate-x-0
                transition-all duration-150
            "
            >
                {label}
            </div>
        </div>
    );
}

export function ChatSidebar() {
    const router = useRouter();
    const {
        conversations,
        currentConversationId,
        setCurrentConversationId,
        refreshConversations,
        loadMoreConversations,
        startNewConversation,
        removeConversation,
        updateConversationPinFavorite,
        isLoadingConversations,
        isLoadingMore,
        hasMoreConversations,
    } = useChatContext();

    const [collapsed, setCollapsed] = useState(false);
    const [mounted, setMounted] = useState(false);
    const [deletingId, setDeletingId] = useState<string | null>(null);
    const [filterMode, setFilterMode] = useState<"all" | "favorites">("all");

    // Ref for infinite scroll sentinel
    const sentinelRef = useRef<HTMLDivElement>(null);
    const scrollContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const saved = localStorage.getItem(COLLAPSED_KEY) === "true";
        setCollapsed(saved);
        setMounted(true);

        const handleResize = () => {
            if (window.innerWidth < 960) {
                setCollapsed(true);
            }
        };
        handleResize();
        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);

    useEffect(() => {
        refreshConversations();
    }, [refreshConversations]);

    // Infinite scroll via IntersectionObserver
    useEffect(() => {
        const sentinel = sentinelRef.current;
        if (!sentinel || collapsed) return;

        const observer = new IntersectionObserver(
            (entries) => {
                const entry = entries[0];
                if (entry?.isIntersecting && hasMoreConversations && !isLoadingMore) {
                    loadMoreConversations();
                }
            },
            {
                root: scrollContainerRef.current,
                rootMargin: "100px",
                threshold: 0,
            },
        );

        observer.observe(sentinel);
        return () => observer.disconnect();
    }, [collapsed, hasMoreConversations, isLoadingMore, loadMoreConversations]);

    const toggleCollapsed = () => {
        setCollapsed((prev) => {
            const next = !prev;
            localStorage.setItem(COLLAPSED_KEY, String(next));
            return next;
        });
    };

    const handleDelete = async (e: React.MouseEvent, convId: string) => {
        e.stopPropagation();
        setDeletingId(convId);
        if (currentConversationId === convId) startNewConversation();
        removeConversation(convId);
        try {
            await fetch(`/api/v1/conversations/${convId}`, {
                method: "DELETE",
                credentials: "include",
            });
        } catch {
            refreshConversations();
        } finally {
            setDeletingId(null);
        }
    };

    const handleLogout = async () => {
        try {
            await fetch("/api/v1/auth/logout", {
                method: "POST",
                credentials: "include",
            });
        } catch {
            /* logout best-effort */
        }
        router.replace("/login");
    };

    const handleTogglePin = async (e: React.MouseEvent, convId: string, isPinned: boolean) => {
        e.stopPropagation();
        updateConversationPinFavorite(convId, isPinned, undefined);
        try {
            await fetch(`/api/v1/conversations/${convId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_pinned: isPinned })
            });
        } catch {
            updateConversationPinFavorite(convId, !isPinned, undefined);
        }
    };

    const handleToggleFavorite = async (e: React.MouseEvent, convId: string, isFavorite: boolean) => {
        e.stopPropagation();
        updateConversationPinFavorite(convId, undefined, isFavorite);
        try {
            await fetch(`/api/v1/conversations/${convId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_favorite: isFavorite })
            });
        } catch {
            updateConversationPinFavorite(convId, undefined, !isFavorite);
        }
    };

    // Date grouping
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const groupDate = useCallback(
        (dateStr: string) => {
            const d = new Date(dateStr);
            d.setHours(0, 0, 0, 0);
            const ts = d.getTime();
            if (ts === today.getTime()) return "Hoy";
            if (ts === yesterday.getTime()) return "Ayer";
            return "Anteriores";
        },
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [today.getTime(), yesterday.getTime()],
    );

    // Filter conversations based on mode
    const filteredConversations = filterMode === "favorites" 
        ? conversations.filter(c => c.is_favorite)
        : conversations;

    // Separate pinned and unpinned
    const pinnedConversations = filteredConversations.filter(c => c.is_pinned);
    const unpinnedConversations = filteredConversations.filter(c => !c.is_pinned);

    // Date grouping for unpinned conversations
    const todayItems = unpinnedConversations.filter(
        (c) => groupDate(c.created_at) === "Hoy",
    );
    const yesterdayItems = unpinnedConversations.filter(
        (c) => groupDate(c.created_at) === "Ayer",
    );
    const olderItems = unpinnedConversations.filter(
        (c) => groupDate(c.created_at) === "Anteriores",
    );

    const groups = [
        { label: "Hoy", items: todayItems },
        { label: "Ayer", items: yesterdayItems },
        { label: "Anteriores", items: olderItems },
    ].filter((g) => g.items.length > 0);

    // Render conversation item (collapsed = tooltip wrapper)
    const renderConvItem = (conv: (typeof conversations)[0]) => {
        const isActive = currentConversationId === conv.id;

        const item = (
            <ConversationItem
                key={conv.id}
                conversation={conv}
                isActive={isActive}
                collapsed={collapsed}
                isDeleting={deletingId === conv.id}
                onSelect={setCurrentConversationId}
                onDelete={handleDelete}
                onTogglePin={handleTogglePin}
                onToggleFavorite={handleToggleFavorite}
            />
        );

        return collapsed ? (
            <Tooltip key={conv.id} label={conv.title || "Sin titulo"}>
                {item}
            </Tooltip>
        ) : (
            <div key={conv.id}>{item}</div>
        );
    };

    // Render nothing until mounted to prevent hydration flash
    if (!mounted) {
        return (
            <aside className="w-[60px] lg:w-64 border-r border-sidebar-border bg-sidebar flex flex-col z-20" />
        );
    }

    return (
        <aside
            className={cn(
                "relative border-r border-sidebar-border bg-sidebar flex flex-col z-20",
                "transition-[width] duration-200 ease-in-out overflow-visible",
                collapsed ? "w-[60px]" : "w-64",
            )}
        >
            {/* Collapse / expand handle */}
            <button
                onClick={toggleCollapsed}
                title={collapsed ? "Expandir" : "Contraer"}
                aria-label={collapsed ? "Expandir barra lateral" : "Contraer barra lateral"}
                aria-expanded={!collapsed}
                className="
                    absolute -right-3.5 top-1/2 -translate-y-1/2 z-30
                    w-7 h-7 flex items-center justify-center
                    rounded-full bg-card border border-border shadow-md
                    text-muted-foreground hover:text-foreground hover:bg-secondary
                    transition-all duration-150
                "
            >
                {collapsed ? (
                    <ChevronRight className="w-4 h-4 ml-0.5" />
                ) : (
                    <ChevronLeft className="w-4 h-4 pr-0.5" />
                )}
            </button>

            {/* Brand */}
            <div className="flex items-center justify-center border-b border-sidebar-border h-[72px]">
                <div className="relative flex items-center justify-center flex-shrink-0">
                    {collapsed ? (
                        <Image src="/iso-macro.svg" alt="Banco Macro" width={24} height={24} className="object-contain" />
                    ) : (
                        <Image src="/isologo-macro.svg" alt="Banco Macro" width={147} height={30} className="object-contain" />
                    )}
                </div>
            </div>
            <div className={cn("pt-3 pb-3", collapsed ? "px-2" : "px-4")}>
                {!collapsed && (
                    <div className="flex items-center gap-1 p-1 bg-secondary/50 rounded-lg mb-3">
                        <button
                            onClick={() => setFilterMode("all")}
                            className={cn(
                                "flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-all",
                                filterMode === "all"
                                    ? "bg-background text-foreground shadow-sm"
                                    : "text-muted-foreground hover:text-foreground"
                            )}
                        >
                            Todos
                        </button>
                        <button
                            onClick={() => setFilterMode("favorites")}
                            className={cn(
                                "flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center justify-center gap-1.5",
                                filterMode === "favorites"
                                    ? "bg-background text-foreground shadow-sm"
                                    : "text-muted-foreground hover:text-foreground"
                            )}
                        >
                            <Star className="w-3 h-3" />
                            Favoritos
                        </button>
                    </div>
                )}
                {collapsed ? (
                    <Tooltip label="Nueva consulta">
                        <button onClick={startNewConversation} className="w-full flex items-center justify-center py-2.5 bg-brand hover:bg-brand/90 active:scale-95 text-primary-foreground rounded-xl transition-all duration-150 shadow-md shadow-brand/20"><Plus className="w-4 h-4" strokeWidth={2.5} /></button>
                    </Tooltip>
                ) : (
                    <button onClick={startNewConversation} className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-brand hover:bg-brand/90 active:scale-[0.98] text-primary-foreground rounded-xl text-[13px] font-semibold transition-all duration-150 shadow-md shadow-brand/20"><Plus className="w-4 h-4" strokeWidth={2.5} />Nueva consulta</button>
                )}
            </div>
            <div ref={scrollContainerRef} className={cn("flex-1 overflow-y-auto scrollbar-hide", collapsed ? "px-1.5" : "px-3")}>
                {isLoadingConversations ? (
                    <div className="flex justify-center py-4"><Loader2 className="w-3.5 h-3.5 animate-spin text-muted-foreground" /></div>
                ) : conversations.length === 0 ? (
                    !collapsed && (
                        <div className="flex flex-col items-center gap-3 py-14 px-6 text-center">
                            <div className="w-10 h-10 rounded-2xl bg-secondary flex items-center justify-center"><MessageSquare className="w-5 h-5 text-brand-light/40" /></div>
                            <p className="text-[12px] text-muted-foreground leading-relaxed">Tus conversaciones<br />aparecerán aquí</p>
                        </div>
                    )
                ) : (
                    <div className={cn("space-y-5 pb-3", collapsed ? "mt-4" : "")}>
                        {pinnedConversations.length > 0 && (
                            <div key="pinned" className={collapsed ? "space-y-2 flex flex-col items-center" : ""}>
                                {!collapsed && (
                                    <p className="px-4 mb-1.5 text-[10.5px] font-semibold text-muted-foreground/60 uppercase tracking-[0.07em] flex items-center gap-1.5">
                                        <Pin className="w-3 h-3" />
                                        Fijados
                                    </p>
                                )}
                                <div className={cn("space-y-0.5 w-full", collapsed && "flex flex-col items-center")}>
                                    {pinnedConversations.map(renderConvItem)}
                                </div>
                            </div>
                        )}
                        {groups.map(({ label, items }) => (
                            <div key={label} className={collapsed ? "space-y-2 flex flex-col items-center" : ""}>
                                {!collapsed && (
                                    <p className="px-4 mb-1.5 text-[10.5px] font-semibold text-muted-foreground/60 uppercase tracking-[0.07em]">
                                        {label}
                                    </p>
                                )}
                                <div className={cn("space-y-0.5 w-full", collapsed && "flex flex-col items-center")}>
                                    {items.map(renderConvItem)}
                                </div>
                            </div>
                        ))}
                        <div ref={sentinelRef} className="h-1" />
                        {isLoadingMore && <div className="flex justify-center py-3"><Loader2 className="w-3.5 h-3.5 animate-spin text-muted-foreground" /></div>}
                    </div>
                )}
            </div>
            <div className={cn("border-t border-sidebar-border py-3.5", collapsed ? "px-1.5 flex flex-col items-center gap-2" : "px-4 space-y-1")}>
                {collapsed ? (
                    <>
                        <ThemeToggle />
                        <Tooltip label="Usuario · Analista">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-indigo-400 flex items-center justify-center ring-2 ring-primary/15 cursor-default mt-1"><span className="text-[11px] font-bold text-white leading-none">U</span></div>
                        </Tooltip>
                        <Tooltip label="Cerrar sesión">
                            <button onClick={handleLogout} className="w-8 h-8 flex items-center justify-center rounded-lg text-muted-foreground/50 hover:text-destructive hover:bg-destructive/10 transition-all duration-150"><LogOut className="w-3.5 h-3.5" /></button>
                        </Tooltip>
                    </>
                ) : (
                    <>
                        <div className="flex items-center gap-3 px-1 py-1 mb-1">
                            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary to-indigo-400 flex items-center justify-center flex-shrink-0 ring-2 ring-primary/15"><span className="text-[11px] font-bold text-white leading-none">U</span></div>
                            <div className="flex-1 min-w-0"><p className="text-[13px] font-medium text-foreground truncate leading-none">Usuario</p><p className="text-[11px] text-muted-foreground mt-0.5 truncate">Analista</p></div>
                            <ThemeToggle />
                        </div>
                        <button onClick={handleLogout} className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-[12.5px] font-medium text-muted-foreground hover:text-destructive hover:bg-destructive/8 transition-all duration-150 group"><LogOut className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform duration-150" />Cerrar sesión</button>
                    </>
                )}
            </div>
        </aside>
    );
}
