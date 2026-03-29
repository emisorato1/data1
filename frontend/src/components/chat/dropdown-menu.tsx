"use client";

import React, { useState, useRef, useEffect, useLayoutEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { MoreVertical } from "lucide-react";
import { cn } from "@/lib/utils";
import { useClickOutside } from "@/hooks/useClickOutside";

export interface DropdownMenuItem {
  icon: React.ReactNode;
  label: string;
  onClick: (e: React.MouseEvent) => void;
  variant?: "default" | "destructive";
  active?: boolean; // For showing active state (Pin/Favorite)
  disabled?: boolean; // For disabling during async operations
}

export interface DropdownMenuProps {
  items: DropdownMenuItem[];
  align?: "left" | "right";
  className?: string;
  onOpenChange?: (isOpen: boolean) => void;
}

interface MenuCoords {
  top?: number;
  bottom?: number;
  left: number;
}

export function DropdownMenu({ items, align = "right", className, onOpenChange }: DropdownMenuProps) {
  // State
  const [isOpen, setIsOpen] = useState(false);
  const [coords, setCoords] = useState<MenuCoords>({ top: 0, left: 0 });
  const [openUpward, setOpenUpward] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const [mounted, setMounted] = useState(false);

  // Refs
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([]);

  // Mount guard for SSR safety
  useEffect(() => { setMounted(true); }, []);

  // Click outside detection
  useClickOutside([triggerRef, menuRef], {
    enabled: isOpen,
    onClickOutside: () => {
      setIsOpen(false);
      onOpenChange?.(false);
    },
  });

  // Notify parent of open state changes
  useEffect(() => {
    onOpenChange?.(isOpen);
  }, [isOpen, onOpenChange]);

  /** Recalculate the position of the floating panel relative to the viewport */
  const recalcPosition = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const menuHeight = 200; // estimated
    const menuWidth = 180;  // min-w-[180px]
    const spaceBelow = window.innerHeight - rect.bottom;
    const willOpenUpward = spaceBelow < menuHeight && rect.top > spaceBelow;
    setOpenUpward(willOpenUpward);

    // Horizontal: align the panel with the trigger's left edge (sidebar menu always aligns left)
    let left = rect.left;
    // Clamp so menu never goes off-screen right
    left = Math.min(left, window.innerWidth - menuWidth - 8);
    left = Math.max(left, 8);

    if (willOpenUpward) {
      setCoords({ bottom: window.innerHeight - rect.top + 4, left });
    } else {
      setCoords({ top: rect.bottom + 4, left });
    }
  }, []);

  // Keep position in sync while menu is open (scroll / resize)
  useLayoutEffect(() => {
    if (!isOpen) return;
    recalcPosition();
    window.addEventListener("scroll", recalcPosition, true);
    window.addEventListener("resize", recalcPosition);
    return () => {
      window.removeEventListener("scroll", recalcPosition, true);
      window.removeEventListener("resize", recalcPosition);
    };
  }, [isOpen, recalcPosition]);

  // Toggle menu open/close
  const toggleMenu = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isOpen) {
      setIsOpen(false);
      return;
    }
    // Calculate position BEFORE opening so the first render is already correct
    recalcPosition();
    setFocusedIndex(-1);
    setIsOpen(true);
  };

  // Auto-focus first item when menu opens
  useEffect(() => {
    if (isOpen && itemRefs.current[0]) {
      // Give time for animation before focusing
      const timer = setTimeout(() => {
        itemRefs.current[0]?.focus();
        setFocusedIndex(0);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // ESC: Close menu
      if (e.key === "Escape") {
        setIsOpen(false);
        triggerRef.current?.focus();
        return;
      }

      // Tab: Navigate between items (with wrap-around)
      if (e.key === "Tab") {
        e.preventDefault();
        const direction = e.shiftKey ? -1 : 1;
        const nextIndex = (focusedIndex + direction + items.length) % items.length;
        setFocusedIndex(nextIndex);
        itemRefs.current[nextIndex]?.focus();
        return;
      }

      // ArrowDown: Next item
      if (e.key === "ArrowDown") {
        e.preventDefault();
        const nextIndex = Math.min(focusedIndex + 1, items.length - 1);
        setFocusedIndex(nextIndex);
        itemRefs.current[nextIndex]?.focus();
        return;
      }

      // ArrowUp: Previous item
      if (e.key === "ArrowUp") {
        e.preventDefault();
        const prevIndex = Math.max(focusedIndex - 1, 0);
        setFocusedIndex(prevIndex);
        itemRefs.current[prevIndex]?.focus();
        return;
      }

      // Enter/Space: Execute focused item action
      if ((e.key === "Enter" || e.key === " ") && focusedIndex >= 0) {
        e.preventDefault();
        itemRefs.current[focusedIndex]?.click();
        return;
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, focusedIndex, items.length]);

  // Handle item click
  const handleItemClick = (e: React.MouseEvent, item: DropdownMenuItem) => {
    e.stopPropagation();

    if (item.disabled) return;

    item.onClick(e);
    setIsOpen(false);
    onOpenChange?.(false);

    // Return focus to trigger after closing
    setTimeout(() => triggerRef.current?.focus(), 0);
  };

  const floatingMenu = isOpen && mounted && (
    <div
      ref={menuRef}
      style={{
        position: "fixed",
        zIndex: 9999,
        left: coords.left,
        ...(openUpward ? { bottom: coords.bottom } : { top: coords.top }),
        minWidth: 180,
      }}
      className={cn(
        "bg-popover border border-border rounded-lg shadow-lvl-3 p-1",
        "animate-in fade-in-0 zoom-in-95 duration-150",
        openUpward ? "slide-in-from-bottom-2" : "slide-in-from-top-2"
      )}
      role="menu"
      aria-orientation="vertical"
    >
      {items.map((item, index) => (
        <button
          key={index}
          ref={(el) => {
            itemRefs.current[index] = el;
          }}
          onClick={(e) => handleItemClick(e, item)}
          disabled={item.disabled}
          role="menuitem"
          tabIndex={focusedIndex === index ? 0 : -1}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2 rounded-md",
            "text-sm font-medium text-left transition-colors duration-100",
            "focus-visible:outline-none",

            // Active state (Pin/Favorite)
            item.active && "text-primary bg-primary/10",

            // Normal hover
            !item.active && !item.disabled && "hover:bg-accent",

            // Destructive variant
            item.variant === "destructive" &&
              !item.disabled &&
              "hover:bg-destructive/10 hover:text-destructive",

            // Disabled
            item.disabled && "opacity-50 cursor-not-allowed",

            // Focus visible
            "focus-visible:bg-accent focus-visible:text-accent-foreground"
          )}
        >
          <span className="flex-shrink-0 w-4 h-4 flex items-center justify-center">
            {item.icon}
          </span>
          <span className="flex-1 truncate">{item.label}</span>
        </button>
      ))}
    </div>
  );

  return (
    <div className={cn("relative", className)}>
      {/* Trigger Button - Kebab Icon */}
      <button
        ref={triggerRef}
        onClick={toggleMenu}
        className={cn(
          "w-7 h-7 flex items-center justify-center rounded-lg",
          "text-muted-foreground/60 hover:text-foreground hover:bg-secondary/80",
          "transition-all duration-150",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          isOpen && "bg-secondary/80 text-foreground"
        )}
        aria-label="Más opciones"
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        <MoreVertical className="w-4 h-4" />
      </button>

      {/* Floating menu rendered in document.body via portal to escape overflow/z-index stacking contexts */}
      {mounted && createPortal(floatingMenu, document.body)}
    </div>
  );
}
