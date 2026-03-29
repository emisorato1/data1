"use client";

import { useState, useCallback, useEffect, useRef } from "react";

const STORAGE_KEY = "source-panel-width";
const DEFAULT_WIDTH = 320;
const MIN_WIDTH = 250;
const MAX_WIDTH_PERCENT = 0.7;

export interface UseResizablePanelReturn {
  /** Current panel width in pixels */
  width: number;
  /** Whether the user is currently dragging the gutter */
  isDragging: boolean;
  /** Attach to the gutter's onMouseDown / onTouchStart */
  startDragging: (e: React.MouseEvent | React.TouchEvent) => void;
}

function clampWidth(px: number, viewportWidth: number): number {
  const maxPx = Math.floor(viewportWidth * MAX_WIDTH_PERCENT);
  return Math.max(MIN_WIDTH, Math.min(px, maxPx));
}

function loadPersistedWidth(): number {
  if (typeof window === "undefined") return DEFAULT_WIDTH;
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = Number(stored);
      if (!Number.isNaN(parsed) && parsed > 0) {
        return clampWidth(parsed, window.innerWidth);
      }
    }
  } catch {
    // localStorage unavailable (SSR, private mode, etc.)
  }
  return DEFAULT_WIDTH;
}

function persistWidth(px: number): void {
  try {
    localStorage.setItem(STORAGE_KEY, String(Math.round(px)));
  } catch {
    // ignore
  }
}

export function useResizablePanel(): UseResizablePanelReturn {
  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const [isDragging, setIsDragging] = useState(false);
  const startXRef = useRef(0);
  const startWidthRef = useRef(0);

  // Hydrate from localStorage after mount
  useEffect(() => {
    setWidth(loadPersistedWidth());
  }, []);

  // Re-clamp on viewport resize
  useEffect(() => {
    const onResize = () => {
      setWidth((prev) => clampWidth(prev, window.innerWidth));
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const onMove = useCallback((clientX: number) => {
    // Panel is on the right: dragging left increases width
    const delta = startXRef.current - clientX;
    const next = clampWidth(startWidthRef.current + delta, window.innerWidth);
    setWidth(next);
  }, []);

  const onEnd = useCallback(() => {
    setIsDragging(false);
    setWidth((cur) => {
      persistWidth(cur);
      return cur;
    });
  }, []);

  // Attach/detach global move/up listeners while dragging
  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      e.preventDefault();
      onMove(e.clientX);
    };
    const handleTouchMove = (e: TouchEvent) => {
      const touch = e.touches[0];
      if (touch) onMove(touch.clientX);
    };
    const handleUp = () => onEnd();

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleUp);
    document.addEventListener("touchmove", handleTouchMove);
    document.addEventListener("touchend", handleUp);

    // Prevent text selection while dragging
    document.body.style.userSelect = "none";
    document.body.style.cursor = "col-resize";

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleUp);
      document.removeEventListener("touchmove", handleTouchMove);
      document.removeEventListener("touchend", handleUp);
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
    };
  }, [isDragging, onMove, onEnd]);

  const startDragging = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      const clientX =
        "touches" in e ? (e.touches[0]?.clientX ?? 0) : e.clientX;
      startXRef.current = clientX;
      startWidthRef.current = width;
      setIsDragging(true);
    },
    [width],
  );

  return { width, isDragging, startDragging };
}
