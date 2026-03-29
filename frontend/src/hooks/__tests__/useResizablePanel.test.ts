import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useResizablePanel } from "../useResizablePanel";

describe("useResizablePanel", () => {
  const originalInnerWidth = window.innerWidth;

  beforeEach(() => {
    localStorage.clear();
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 1280,
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
  });

  it("returns default width of 320px when no localStorage value", () => {
    const { result } = renderHook(() => useResizablePanel());
    // After mount effect, it loads from localStorage (empty) → falls back to 320
    expect(result.current.width).toBe(320);
    expect(result.current.isDragging).toBe(false);
  });

  it("loads persisted width from localStorage", () => {
    localStorage.setItem("source-panel-width", "450");
    const { result } = renderHook(() => useResizablePanel());
    expect(result.current.width).toBe(450);
  });

  it("clamps persisted width to minimum 250px", () => {
    localStorage.setItem("source-panel-width", "100");
    const { result } = renderHook(() => useResizablePanel());
    expect(result.current.width).toBe(250);
  });

  it("clamps persisted width to maximum 70% of viewport", () => {
    // viewport is 1280, so max = 896
    localStorage.setItem("source-panel-width", "1000");
    const { result } = renderHook(() => useResizablePanel());
    expect(result.current.width).toBe(896);
  });

  it("sets isDragging to true when startDragging is called", () => {
    const { result } = renderHook(() => useResizablePanel());

    act(() => {
      result.current.startDragging({
        clientX: 500,
      } as unknown as React.MouseEvent);
    });

    expect(result.current.isDragging).toBe(true);
  });

  it("updates width on mouse move while dragging", () => {
    const { result } = renderHook(() => useResizablePanel());

    // Start dragging at x=800
    act(() => {
      result.current.startDragging({
        clientX: 800,
      } as unknown as React.MouseEvent);
    });

    // Move mouse to x=700 → delta = 100 → width increases by 100
    act(() => {
      const moveEvent = new MouseEvent("mousemove", { clientX: 700 });
      document.dispatchEvent(moveEvent);
    });

    // Default 320 + 100 = 420
    expect(result.current.width).toBe(420);
  });

  it("persists width to localStorage on mouseup", () => {
    const { result } = renderHook(() => useResizablePanel());

    act(() => {
      result.current.startDragging({
        clientX: 800,
      } as unknown as React.MouseEvent);
    });

    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 700 }));
    });

    act(() => {
      document.dispatchEvent(new MouseEvent("mouseup"));
    });

    expect(result.current.isDragging).toBe(false);
    expect(localStorage.getItem("source-panel-width")).toBe("420");
  });

  it("enforces minimum width during drag", () => {
    const { result } = renderHook(() => useResizablePanel());

    act(() => {
      result.current.startDragging({
        clientX: 500,
      } as unknown as React.MouseEvent);
    });

    // Move right (decreases panel width): delta = 500 - 900 = -400 → 320 - 400 clamped to 250
    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 900 }));
    });

    expect(result.current.width).toBe(250);
  });

  it("enforces maximum width during drag", () => {
    const { result } = renderHook(() => useResizablePanel());

    act(() => {
      result.current.startDragging({
        clientX: 800,
      } as unknown as React.MouseEvent);
    });

    // Move far left: delta = 800 - 0 = 800 → 320 + 800 = 1120, clamped to 896 (70% of 1280)
    act(() => {
      document.dispatchEvent(new MouseEvent("mousemove", { clientX: 0 }));
    });

    expect(result.current.width).toBe(896);
  });

  it("re-clamps width on viewport resize", () => {
    localStorage.setItem("source-panel-width", "800");
    const { result } = renderHook(() => useResizablePanel());
    expect(result.current.width).toBe(800);

    // Shrink viewport to 900px → max = 630
    act(() => {
      Object.defineProperty(window, "innerWidth", { value: 900, writable: true, configurable: true });
      window.dispatchEvent(new Event("resize"));
    });

    expect(result.current.width).toBe(630);
  });

  it("handles touch events for dragging", () => {
    const { result } = renderHook(() => useResizablePanel());

    act(() => {
      result.current.startDragging({
        touches: [{ clientX: 800 }],
      } as unknown as React.TouchEvent);
    });

    expect(result.current.isDragging).toBe(true);

    act(() => {
      const touchMove = new TouchEvent("touchmove", {
        touches: [{ clientX: 700 } as Touch],
      });
      document.dispatchEvent(touchMove);
    });

    expect(result.current.width).toBe(420);

    act(() => {
      document.dispatchEvent(new TouchEvent("touchend"));
    });

    expect(result.current.isDragging).toBe(false);
  });

  it("restores body cursor and user-select after drag ends", () => {
    const { result } = renderHook(() => useResizablePanel());

    act(() => {
      result.current.startDragging({ clientX: 500 } as unknown as React.MouseEvent);
    });

    expect(document.body.style.userSelect).toBe("none");
    expect(document.body.style.cursor).toBe("col-resize");

    act(() => {
      document.dispatchEvent(new MouseEvent("mouseup"));
    });

    expect(document.body.style.userSelect).toBe("");
    expect(document.body.style.cursor).toBe("");
  });
});
