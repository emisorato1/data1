"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Square } from "lucide-react";
import { cn } from "@/lib/utils";

interface MessageInputProps {
    onSend: (text: string) => void;
    onStop: () => void;
    isLoading: boolean;
}

export function MessageInput({ onSend, onStop, isLoading }: MessageInputProps) {
    const [text, setText] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "inherit";
            const scrollHeight = textareaRef.current.scrollHeight;
            // The minimum height is now handled by min-h-[110px] via Tailwind,
            // but we still want it to grow up to a max (e.g. 180px or 250px)
            textareaRef.current.style.height = `${Math.min(Math.max(scrollHeight, 110), 250)}px`;
        }
    }, [text]);

    const handleSubmit = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (text.trim() && !isLoading) {
            onSend(text.trim());
            setText("");
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    const canSend = text.trim().length > 0 && !isLoading;

    return (
        <div className="w-full pb-6 pt-2">
            <form onSubmit={handleSubmit} className="w-full">
                <div
                    className={cn(
                        "relative flex flex-col bg-card border rounded-2xl p-4 transition-all duration-200",
                        "focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/10",
                        "border-border min-h-[110px]"
                    )}
                >
                    <textarea
                        ref={textareaRef}
                        rows={1}
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Hacé tu consulta..."
                        className="flex-1 w-full bg-transparent border-none resize-none text-[16px] focus:ring-0 outline-none text-foreground placeholder:text-muted-foreground/60 font-[450] leading-relaxed pb-8"
                        disabled={isLoading}
                    />

                    {/* Action buttons section at the bottom right */}
                    <div className="absolute bottom-3 right-3 flex items-center gap-2">
                        {/* Keyboard hint */}
                        <div className="hidden sm:flex items-center gap-1 px-2 py-1 text-[13px] font-medium text-muted-foreground/50 rounded-md select-none mr-2">
                            <span>Enter para enviar</span>
                        </div>

                        {isLoading ? (
                            <button
                                type="button"
                                onClick={onStop}
                                className="w-9 h-9 flex items-center justify-center bg-secondary text-foreground rounded-lg hover:bg-destructive/10 hover:text-destructive transition-all"
                                title="Detener"
                            >
                                <Square className="w-4 h-4 fill-current" />
                            </button>
                        ) : (
                            <button
                                type="submit"
                                disabled={!canSend}
                                className={cn(
                                    "w-9 h-9 flex items-center justify-center rounded-lg transition-all",
                                    canSend
                                        ? "bg-primary text-primary-foreground hover:opacity-90 active:scale-95 shadow-sm"
                                        : "bg-secondary text-muted-foreground/40 cursor-not-allowed"
                                )}
                                title="Enviar"
                            >
                                <Send className="w-4 h-4" />
                            </button>
                        )}
                    </div>
                </div>

                <p className="text-center text-[18px] flex items-center justify-center text-muted-foreground/60 mt-3 font-medium">
                    Las respuestas se generan a partir de la base documental interna del banco.
                </p>
            </form>
        </div>
    );
}
