"use client";

import React from "react";
import { X, FileText, Link } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Source } from "@/components/chat/message-bubble";

export interface SourcePanelProps {
    /** The source to display, or null to hide the panel */
    source: Source | null;
    /** All sources for navigation context */
    sources: Source[];
    /** Callback to close the panel */
    onClose: () => void;
    /** Callback when a different source is selected from the list */
    onSelectSource: (index: number) => void;
    /** Panel width in pixels (controlled by useResizablePanel) */
    width?: number;
    /** Mouse/touch handler for the resize gutter */
    onGutterMouseDown?: (e: React.MouseEvent | React.TouchEvent) => void;
    /** Whether the gutter is currently being dragged */
    isDragging?: boolean;
}

/**
 * Side panel that shows detailed information about a cited source.
 * Slides in from the right. Displays each chunk as an individual card.
 */
export function SourcePanel({
    source,
    sources,
    onClose,
    onSelectSource,
    width,
    onGutterMouseDown,
    isDragging,
}: SourcePanelProps) {
    if (!source) return null;

    return (
        <aside
            className={cn(
                "border-l border-border bg-background flex flex-col h-full relative",
                !isDragging && "animate-in slide-in-from-right-5 fade-in duration-200",
            )}
            style={width ? { width: `${width}px`, minWidth: `${width}px` } : { width: "320px", minWidth: "320px" }}
        >
            {/* Resize gutter */}
            {onGutterMouseDown && (
                <div
                    role="separator"
                    aria-orientation="vertical"
                    aria-label="Redimensionar panel de fuentes"
                    tabIndex={0}
                    className={cn(
                        "absolute left-0 top-0 bottom-0 w-1.5 cursor-col-resize z-20",
                        "hover:bg-primary/20 active:bg-primary/30 transition-colors",
                        isDragging && "bg-primary/30",
                    )}
                    onMouseDown={onGutterMouseDown}
                    onTouchStart={onGutterMouseDown}
                />
            )}
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3.5 border-b border-border bg-card">
                <div className="flex items-center gap-2 min-w-0">
                    <div className="w-6 h-6 rounded-md bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <Link className="w-3.5 h-3.5 text-primary" />
                    </div>
                    <h2 className="text-[13px] font-semibold text-foreground truncate">
                        Fuente {source.index}
                    </h2>
                </div>
                <button
                    onClick={onClose}
                    className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                    title="Cerrar panel"
                    aria-label="Cerrar panel de fuentes"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>

            {/* Source detail as card */}
            <div className="flex-1 overflow-y-auto p-4">
                <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
                    {/* Card header: document name */}
                    <div className="flex items-start gap-2.5 px-4 py-3 border-b border-border/60 bg-accent/30">
                        <FileText className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                        <div className="min-w-0">
                            <p className="text-[13px] font-medium text-foreground leading-snug break-words">
                                {source.document_name}
                            </p>
                            {source.page && source.page !== "N/A" && (
                                <p className="text-[11px] text-muted-foreground mt-0.5">
                                    Página {source.page}
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Card body: chunk excerpt */}
                    {source.chunk_text && (
                        <div className="px-4 py-3">
                            <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                                Extracto
                            </p>
                            <blockquote className="text-[12.5px] text-muted-foreground leading-relaxed p-3 bg-muted/50 rounded-lg border-l-2 border-primary/30 italic">
                                {source.chunk_text}
                            </blockquote>
                        </div>
                    )}
                </div>
            </div>

            {/* Source navigation chips */}
            {sources.length > 1 && (
                <div className="border-t border-border px-4 py-3 bg-card">
                    <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                        Todas las fuentes
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                        {sources.map((s) => (
                            <button
                                key={s.index}
                                onClick={() => onSelectSource(s.index)}
                                className={cn(
                                    "inline-flex items-center gap-[2px]",
                                    "h-7 px-2 rounded-lg text-[12px] font-semibold",
                                    "transition-all duration-150",
                                    s.index === source.index
                                        ? "bg-primary text-primary-foreground shadow-sm"
                                        : "bg-secondary text-secondary-foreground hover:bg-primary/10 hover:text-primary",
                                )}
                                title={s.document_name}
                                aria-label={`Fuente ${s.index}: ${s.document_name}`}
                            >
                                <Link className="w-3 h-3" aria-hidden="true" />
                                {s.index}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </aside>
    );
}
