"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Lock, Mail, Loader2 } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import Image from "next/image";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const response = await fetch("/api/v1/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            const result = await response.json();

            if (response.ok) {
                router.push("/chat");
            } else {
                setError(result.error?.message || "Credenciales inválidas");
            }
        } catch (err) {
            setError("Error de conexión con el servidor");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="relative min-h-screen w-full overflow-hidden bg-background">
            <div className="absolute top-6 right-6 z-50">
                <ThemeToggle />
            </div>

            {/* Elementos ambientales */}
            <div className="absolute top-[-15%] left-[-10%] w-[50vw] h-[50vw] bg-primary/10 rounded-full blur-[100px]" />
            <div className="absolute bottom-[-15%] right-[-10%] w-[40vw] h-[40vw] bg-secondary/50 dark:bg-primary/5 rounded-full blur-[100px]" />

            {/* Contenedor Grilla Fluida con máximo 1440px y Padding Lateral Variable */}
            <div className="mx-auto w-full max-w-[1440px] px-6 xl:px-[70px] xxl:px-[60px] min-h-screen flex items-center justify-center relative z-10">

                {/* Estructura Columnas con Gutter Variable */}
                <div className="w-full grid grid-cols-4 md:grid-cols-6 xl:grid-cols-12 gap-6 xl:gap-4 xxl:gap-6">

                    {/* El formulario abarca 4 columnas en todas las resoluciones, justificado al centro. Dialog/Card grande -> 16px o 12px (rounded-md o rounded-lg) */}
                    <div className="col-span-4 md:col-start-2 xl:col-start-5 xl:col-span-4 p-6 md:p-8">
                        <div className="mb-8 w-full max-w-[328px] mx-auto xl:max-w-full">
                            <div className="flex items-center justify-center mb-6">
                                <Image src="/isologo-macro.svg" alt="Banco Macro" width={328} height={33} className="w-full h-auto object-contain" priority />
                            </div>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label htmlFor="email" className="text-[12px] font-bold text-brand-light ml-2">
                                        Usuario
                                    </label>
                                    <div className="relative group">
                                        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-brand-accent transition-colors" />
                                        <input
                                            id="email"
                                            type="email"
                                            required
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            className="w-full pl-12 pr-4 py-3 bg-background/50 border-1 border-brand-accent rounded-md text-foreground font-medium placeholder:text-muted-foreground/70 focus:ring-2 focus:ring-brand-accent/50 focus:border-brand-accent transition-all outline-none"
                                            placeholder="nombre@macro.com.ar"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label htmlFor="password" className="text-[12px] font-bold text-brand-light ml-2">
                                        Contraseña
                                    </label>
                                    <div className="relative group">
                                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-brand-accent transition-colors" />
                                        <input
                                            id="password"
                                            type="password"
                                            required
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            className="w-full pl-12 pr-4 py-3 bg-background/50 border-1 border-brand-accent rounded-md text-foreground font-medium placeholder:text-muted-foreground/70 focus:ring-2 focus:ring-brand-accent/50 focus:border-brand-accent transition-all outline-none"
                                            placeholder="••••••••"
                                        />
                                    </div>
                                </div>
                            </div>

                            {error && (
                                <div className="p-3 text-sm text-destructive bg-destructive/10 border-1 border-destructive/20 rounded-xs text-center font-medium animate-shake">
                                    {error}
                                </div>
                            )}

                            <div className="flex justify-center w-full">
                                <button
                                    type="submit"
                                    disabled={loading}
                                    style={{ backgroundColor: "#2D5FFF" }}
                                    className="w-3/4 py-3 px-6 mt-4 hover:opacity-90 text-primary-foreground font-bold rounded-md shadow-md transition-all active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                            <span>Verificando...</span>
                                        </>
                                    ) : (
                                        <span>Ingresar</span>
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>

                </div>
            </div>
        </div>
    );
}
