"use client";

import React, { useState, useRef, useEffect } from "react";
import { MessageSquare, Trash2, Loader2, Pencil, Check, X, Pin, Star } from "lucide-react";
import { DropdownMenu } from "./dropdown-menu";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import { cn } from "@/lib/utils";
import type { Conversation } from "@/context/chat-context";
import { useChatContext } from "@/context/chat-context";

interface ConversationItemProps {
    conversation: Conversation;
    isActive: boolean;
    collapsed: boolean;
    isDeleting: boolean;
    onSelect: (id: string) => void;
    onDelete: (e: React.MouseEvent, id: string) => void;
    onTogglePin: (e: React.MouseEvent, id: string, isPinned: boolean) => void;
    onToggleFavorite: (e: React.MouseEvent, id: string, isFavorite: boolean) => void;
}

export function ConversationItem({
    conversation,
    isActive,
    collapsed,
    isDeleting,
    onSelect,
    onDelete,
    onTogglePin,
    onToggleFavorite,
}: ConversationItemProps) {
    const { updateConversationTitle } = useChatContext();
    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState(conversation.title || "");
    const [isSaving, setIsSaving] = useState(false);
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        setEditValue(conversation.title || "");
    }, [conversation.title]);

    useEffect(() => {
        if (isEditing && inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
        }
    }, [isEditing]);

    const handleSave = async (e: React.MouseEvent | React.FormEvent) => {
        e.stopPropagation();
        if (!editValue.trim() || editValue === conversation.title) {
            setIsEditing(false);
            setEditValue(conversation.title || "");
            return;
        }

        setIsSaving(true);
        try {
            const res = await fetch(`/api/v1/conversations/${conversation.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: editValue.trim() })
            });
            if (res.ok) {
                updateConversationTitle(conversation.id, editValue.trim()); 
            }
        } catch (error) {
            setEditValue(conversation.title || "");
        } finally {
            setIsSaving(false);
            setIsEditing(false);
        }
    };

    const handleCancel = (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsEditing(false);
        setEditValue(conversation.title || "");
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSave(e as unknown as React.FormEvent);
        } else if (e.key === 'Escape') {
            handleCancel(e as unknown as React.MouseEvent);
        }
    };

    const relativeDate = formatDistanceToNow(
        new Date(conversation.updated_at || conversation.created_at),
        { addSuffix: true, locale: es },
    );

    return (
        <div className="group relative">
            {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-primary rounded-r-full" />
            )}
            <button
                onClick={() => onSelect(conversation.id)}
                className={cn(
                    "flex items-center gap-3 rounded-xl text-left transition-all duration-150",
                    collapsed ? "justify-center w-10 h-10" : "w-full py-2.5 pl-4 pr-9",
                    isActive
                        ? "bg-accent/70 text-foreground"
                        : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground",
                )}
            >
                <MessageSquare
                    className={cn(
                        "w-3.5 h-3.5 flex-shrink-0 transition-colors",
                        isActive
                            ? "text-brand-light"
                            : "text-brand-light/50",
                    )}
                />
                {!collapsed && (
                    <div className="flex-1 min-w-0 pr-10">
                        {isEditing ? (
                            <div className="flex items-center" onClick={e => e.stopPropagation()}>
                                <input
                                    ref={inputRef}
                                    value={editValue}
                                    onChange={(e) => setEditValue(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    disabled={isSaving}
                                    className="w-full bg-background border border-input rounded px-1.5 py-0.5 text-[13px] text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                                />
                            </div>
                        ) : (
                            <span className="truncate text-[13px] font-[450] leading-snug block" title={conversation.title || "Sin titulo"}>
                                {conversation.title || "Sin titulo"}
                            </span>
                        )}
                        {!isEditing && (
                            <span className="text-[11px] text-muted-foreground/60 block mt-0.5">
                                {relativeDate}
                            </span>
                        )}
                    </div>
                )}
            </button>
            {!collapsed && !isEditing && (
                <div className={cn(
                    "absolute right-2 top-1/2 -translate-y-1/2 transition-opacity duration-150",
                    isMenuOpen ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                )}>
                    <DropdownMenu
                        align="right"
                        onOpenChange={setIsMenuOpen}
                        items={[
                            {
                                icon: <Pin className={cn("w-4 h-4", conversation.is_pinned && "fill-current")} />,
                                label: conversation.is_pinned ? "Desfijar" : "Fijar",
                                onClick: (e) => onTogglePin(e, conversation.id, !conversation.is_pinned),
                                active: conversation.is_pinned,
                            },
                            {
                                icon: <Star className={cn("w-4 h-4", conversation.is_favorite && "fill-current")} />,
                                label: conversation.is_favorite ? "Quitar de favoritos" : "Favorito",
                                onClick: (e) => onToggleFavorite(e, conversation.id, !conversation.is_favorite),
                                active: conversation.is_favorite,
                            },
                            {
                                icon: <Pencil className="w-4 h-4" />,
                                label: "Editar nombre",
                                onClick: (e) => {
                                    e.stopPropagation();
                                    setIsEditing(true);
                                },
                            },
                            {
                                icon: isDeleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />,
                                label: "Eliminar",
                                onClick: (e) => onDelete(e, conversation.id),
                                variant: "destructive" as const,
                                disabled: isDeleting,
                            },
                        ]}
                    />
                </div>
            )}
            {!collapsed && isEditing && (
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-0.5 z-10 bg-background/80 backdrop-blur-sm rounded-lg px-0.5">
                    <button
                        onClick={handleSave}
                        disabled={isSaving}
                        className="w-6 h-6 flex items-center justify-center rounded-lg text-emerald-500 hover:bg-emerald-500/10"
                        title="Guardar"
                    >
                        {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-4 h-4" />}
                    </button>
                    <button
                        onClick={handleCancel}
                        disabled={isSaving}
                        className="w-6 h-6 flex items-center justify-center rounded-lg text-muted-foreground hover:bg-secondary"
                        title="Cancelar"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            )}
        </div>
    );
}
