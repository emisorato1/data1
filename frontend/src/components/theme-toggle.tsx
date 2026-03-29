"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

/**
 * Minimal theme toggle — single icon button.
 * Shows Moon in light mode (click → go dark), Sun in dark mode (click → go light).
 * Smooth rotate + scale transition on switch.
 */
export function ThemeToggle() {
    const { resolvedTheme, setTheme } = useTheme();
    const [mounted, setMounted] = useState(false);
    const [animating, setAnimating] = useState(false);

    useEffect(() => setMounted(true), []);
    if (!mounted) return null;

    const isDark = resolvedTheme === "dark";

    const handleToggle = () => {
        setAnimating(true);
        setTimeout(() => setAnimating(false), 300);
        setTheme(isDark ? "light" : "dark");
    };

    return (
        <button
            onClick={handleToggle}
            title={isDark ? "Modo claro" : "Modo oscuro"}
            aria-label={isDark ? "Activar modo claro" : "Activar modo oscuro"}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors duration-150"
        >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className={`w-[15px] h-[15px] transition-transform duration-300 ${animating ? "rotate-[30deg] scale-75 opacity-0" : "rotate-0 scale-100 opacity-100"
                    }`}
            >
                {isDark ? (
                    /* Sun rays — shown in dark mode to switch to light */
                    <>
                        <circle cx="12" cy="12" r="4" />
                        <line x1="12" y1="2" x2="12" y2="4" />
                        <line x1="12" y1="20" x2="12" y2="22" />
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                        <line x1="2" y1="12" x2="4" y2="12" />
                        <line x1="20" y1="12" x2="22" y2="12" />
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                    </>
                ) : (
                    /* Crescent moon — shown in light mode to switch to dark */
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                )}
            </svg>
        </button>
    );
}
