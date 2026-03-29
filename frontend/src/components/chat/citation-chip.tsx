"use client";

import React from "react";
import { Link } from "lucide-react";
import { cn } from "@/lib/utils";

export interface CitationChipProps {
    /** 1-based index shown inside the chip */
    index: number;
    /** Whether this chip is currently selected (source panel open for it) */
    isActive?: boolean;
    /** Callback when the chip is clicked */
    onClick?: (index: number) => void;
}

/**
 * Inline citation chip rendered as 🔗1, 🔗2, etc.
 * Designed to sit inline within markdown prose without breaking reading flow.
 */
export function CitationChip({ index, isActive, onClick }: CitationChipProps) {
    return (
        <button
            type="button"
            onClick={(e) => {
                e.stopPropagation();
                onClick?.(index);
            }}
            className={cn(
                "inline-flex items-center justify-center gap-[2px]",
                "h-[18px] px-1.5 mx-0.5",
                "rounded text-[11px] font-semibold leading-none",
                "transition-all duration-150 cursor-pointer",
                "align-super -top-0.5 relative",
                isActive
                    ? "bg-primary text-primary-foreground shadow-sm shadow-primary/25"
                    : "bg-primary/10 text-primary hover:bg-primary/20 hover:shadow-sm",
            )}
            title={`Ver fuente ${index}`}
            aria-label={`Fuente ${index}`}
        >
            <Link className="w-2.5 h-2.5" aria-hidden="true" />
            {index}
        </button>
    );
}
