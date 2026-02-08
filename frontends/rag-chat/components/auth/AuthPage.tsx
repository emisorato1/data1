"use client";

import { useState } from "react";
import { LoginForm } from "./LoginForm";
import { SignupForm } from "./SignupForm";
import { Button } from "@/components/ui/button";

export function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-8 rounded-lg border bg-card p-8 shadow-lg">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold">LangGraph Assistant</h1>
          <p className="text-muted-foreground">
            {isLogin ? "Inicia sesión para continuar" : "Crea una cuenta para comenzar"}
          </p>
        </div>

        <div className="flex gap-2 border-b">
          <Button
            variant={isLogin ? "default" : "ghost"}
            className="flex-1 rounded-b-none"
            onClick={() => setIsLogin(true)}
          >
            Iniciar Sesión
          </Button>
          <Button
            variant={!isLogin ? "default" : "ghost"}
            className="flex-1 rounded-b-none"
            onClick={() => setIsLogin(false)}
          >
            Registrarse
          </Button>
        </div>

        <div className="pt-4">
          {isLogin ? <LoginForm /> : <SignupForm onSuccess={() => setIsLogin(true)} />}
        </div>
      </div>
    </div>
  );
}



