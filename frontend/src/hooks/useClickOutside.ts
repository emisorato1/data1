"use client";

import { useEffect, RefObject } from "react";

interface UseClickOutsideOptions {
  enabled?: boolean;
  onClickOutside: () => void;
}

/**
 * Hook to detect clicks outside of one or more elements.
 * Useful for closing dropdowns, modals, etc.
 * 
 * @param refs - Single ref or array of refs to elements that should be excluded from "outside" clicks
 * @param options - Configuration options
 * @param options.enabled - Whether the listener is active (default: true)
 * @param options.onClickOutside - Callback fired when a click outside occurs
 * 
 * @example
 * const menuRef = useRef<HTMLDivElement>(null);
 * const triggerRef = useRef<HTMLButtonElement>(null);
 * 
 * useClickOutside([menuRef, triggerRef], {
 *   enabled: isOpen,
 *   onClickOutside: () => setIsOpen(false)
 * });
 */
export function useClickOutside(
  refs: RefObject<HTMLElement | null> | RefObject<HTMLElement | null>[],
  { enabled = true, onClickOutside }: UseClickOutsideOptions
): void {
  useEffect(() => {
    if (!enabled) return;

    const refsArray = Array.isArray(refs) ? refs : [refs];

    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      const target = event.target as Node;

      // Check if click is inside any of the refs
      const isInside = refsArray.some((ref) => ref.current?.contains(target));

      if (!isInside) {
        onClickOutside();
      }
    };

    // Listen for both mouse and touch events
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("touchstart", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("touchstart", handleClickOutside);
    };
  }, [refs, enabled, onClickOutside]);
}
