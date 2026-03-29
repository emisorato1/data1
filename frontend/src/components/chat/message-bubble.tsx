"use client";

import React from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { User, Bot, Loader2, Copy, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import { CitationChip } from "@/components/chat/citation-chip";
import { FeedbackWidget } from "@/components/chat/FeedbackWidget";

export interface Source {
    index: number;
    document_name: string;
    page: string | number;
    document_id?: number;
    chunk_text?: string;
}

export interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    isStreaming?: boolean;
    sources?: Source[];
}

interface MessageBubbleProps {
    message: Message;
    /** Index of the currently selected citation (for highlight) */
    activeCitationIndex?: number | null;
    /** Callback when an inline citation chip [N] is clicked */
    onCitationClick?: (index: number, source: Source) => void;
    /** Callback when a source document badge is clicked */
    onSourceBadgeClick?: (documentName: string, sources: Source[]) => void;
}

/**
 * Walk React children and replace text fragments matching [N] with
 * inline CitationChip components. This keeps chips inside the same <p>
 * without causing line breaks (Gemini style).
 */
function injectCitationChips(
    children: React.ReactNode,
    sourceIndexes: Set<number>,
    sources: Source[],
    activeCitationIndex: number | null | undefined,
    onCitationClick?: (index: number, source: Source) => void,
): React.ReactNode {
    return React.Children.map(children, (child) => {
        // Only process string nodes
        if (typeof child === "string") {
            const parts = child.split(/(\[\d+\])/g);
            if (parts.length === 1) return child; // no citation refs

            return parts.map((part, i) => {
                const m = part.match(/^\[(\d+)\]$/);
                if (m && m[1]) {
                    const idx = parseInt(m[1], 10);
                    if (sourceIndexes.has(idx)) {
                        const source = sources.find((s) => s.index === idx);
                        return (
                            <CitationChip
                                key={`cite-${idx}-${i}`}
                                index={idx}
                                isActive={activeCitationIndex === idx}
                                onClick={() => {
                                    if (source && onCitationClick) {
                                        onCitationClick(idx, source);
                                    }
                                }}
                            />
                        );
                    }
                }
                return part || null;
            });
        }

        // Recurse into React elements so chips work inside <strong>, <em>, <li>, etc.
        if (React.isValidElement<{ children?: React.ReactNode }>(child) && child.props.children) {
            return React.cloneElement(child, {}, injectCitationChips(
                child.props.children,
                sourceIndexes,
                sources,
                activeCitationIndex,
                onCitationClick,
            ));
        }

        return child;
    });
}

export function MessageBubble({
    message,
    activeCitationIndex,
    onCitationClick,
    onSourceBadgeClick,
}: MessageBubbleProps) {
    const isUser = message.role === "user";
    const hasSources = !isUser && message.sources && message.sources.length > 0;

    // Build custom ReactMarkdown components that inject CitationChip inline
    const mdComponents = React.useMemo<Components>(() => {
        if (!hasSources) return {};

        const sourceIndexes = new Set(message.sources!.map((s) => s.index));
        const sources = message.sources!;

        const inject = (children: React.ReactNode) =>
            injectCitationChips(children, sourceIndexes, sources, activeCitationIndex, onCitationClick);

        return {
            p: ({ children, ...props }) => <p {...props}>{inject(children)}</p>,
            li: ({ children, ...props }) => <li {...props}>{inject(children)}</li>,
            td: ({ children, ...props }) => <td {...props}>{inject(children)}</td>,
            th: ({ children, ...props }) => <th {...props}>{inject(children)}</th>,
            blockquote: ({ children, ...props }) => <blockquote {...props}>{inject(children)}</blockquote>,
        };
    }, [hasSources, message.sources, activeCitationIndex, onCitationClick]);

    return (
        <div
            className={cn(
                "group flex w-full mb-8 animate-in fade-in slide-in-from-bottom-3 duration-300",
                isUser ? "justify-end" : "justify-start"
            )}
        >
            <div
                className={cn(
                    "flex max-w-[90%] md:max-w-[85%] gap-3",
                    isUser ? "flex-row-reverse" : "flex-row"
                )}
            >
                {/* Avatar */}
                <div className="flex flex-col flex-shrink-0 justify-start pt-1">
                    <div
                        className={cn(
                            "w-7 h-7 rounded-full flex items-center justify-center transition-transform shadow-sm",
                            isUser
                                ? "bg-primary text-primary-foreground"
                                : "bg-card text-primary border border-border"
                        )}
                    >
                        {isUser
                            ? <User className="w-3.5 h-3.5" />
                            : <Bot className="w-3.5 h-3.5" />
                        }
                    </div>
                </div>

                {/* Content */}
                <div className="space-y-1.5">
                    <div
                        className={cn(
                            "px-4 py-3 rounded-2xl text-[14px] leading-relaxed transition-all",
                            isUser
                                ? "bg-primary text-primary-foreground rounded-tr-sm"
                                : "bg-card text-foreground border border-border rounded-tl-sm shadow-sm"
                        )}
                    >
                        {isUser ? (
                            <div className="whitespace-pre-wrap font-[450]">{message.content}</div>
                        ) : (
                            <div className="prose prose-sm prose-slate dark:prose-invert max-w-none prose-p:leading-relaxed prose-p:my-1.5 prose-pre:bg-muted prose-pre:rounded-xl prose-headings:font-semibold prose-headings:text-foreground prose-code:text-primary prose-code:bg-accent prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs">
                                <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                                    {message.content}
                                </ReactMarkdown>
                            </div>
                        )}

                        {/* Streaming indicator */}
                        {message.isStreaming && !message.content && (
                            <div className="flex items-center gap-2 text-muted-foreground py-0.5">
                                <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
                                <span className="text-sm animate-pulse">Analizando documentos...</span>
                            </div>
                        )}

                        {/* Typing cursor while streaming */}
                        {message.isStreaming && message.content && (
                            <span className="inline-block w-0.5 h-4 bg-primary ml-0.5 animate-pulse align-middle" />
                        )}
                    </div>

                    {/* Sources summary (shown below bubble when sources exist) */}
                    {hasSources && (() => {
                        const uniqueSources = new Map<string, { name: string; pages: Set<string | number> }>();
                        for (const src of message.sources!) {
                            const key = src.document_name;
                            if (!uniqueSources.has(key)) {
                                uniqueSources.set(key, { name: src.document_name, pages: new Set() });
                            }
                            if (src.page && src.page !== "N/A") {
                                uniqueSources.get(key)!.pages.add(src.page);
                            }
                        }
                        return (
                            <div className="px-1 pt-1 animate-in fade-in duration-300">
                                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 ml-0.5">
                                    Fuentes
                                </p>
                                <div className="flex flex-wrap gap-1.5">
                                    {Array.from(uniqueSources.entries()).map(([docName, info]) => (
                                        <button
                                            key={docName}
                                            type="button"
                                            onClick={() => onSourceBadgeClick?.(docName, message.sources!)}
                                            className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-accent text-accent-foreground rounded-md text-[11px] font-medium border border-border/60 hover:bg-accent/80 hover:border-primary/40 transition-colors cursor-pointer"
                                            title={`Ver fuente: ${docName}`}
                                        >
                                            <FileText className="w-3 h-3 opacity-50" />
                                            <span className="truncate max-w-[180px]">{docName}</span>
                                            {info.pages.size > 0 && (
                                                <span className="text-muted-foreground font-normal">
                                                    p.{Array.from(info.pages).join(", ")}
                                                </span>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        );
                    })()}

                    {/* Action buttons — feedback always visible, copy on hover */}
                    {!isUser && !message.isStreaming && message.content && (
                        <div className="flex items-center gap-1 px-1 mt-2">
                            <button
                                className="min-w-[44px] min-h-[44px] inline-flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-secondary rounded-lg transition-all"
                                title="Copiar"
                                aria-label="Copiar respuesta"
                                onClick={() => navigator.clipboard.writeText(message.content)}
                            >
                                <Copy className="w-5 h-5" />
                            </button>
                            <FeedbackWidget messageId={message.id} />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
