"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import {
  login as loginApi,
  register as registerApi,
  logout as logoutApi,
  getAuthToken,
  initiateGoogleLogin,
} from "@/lib/chatApi";

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => void;
  checkAuth: () => void;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check if user is authenticated
  const checkAuth = useCallback(() => {
    const token = getAuthToken();
    setIsAuthenticated(!!token);
    setIsLoading(false);
  }, []);

  // Check auth on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = useCallback(async (email: string, password: string) => {
    try {
      setError(null);
      setIsLoading(true);
      await loginApi(email, password);
      setIsAuthenticated(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error al iniciar sesión";
      setError(errorMessage);
      setIsAuthenticated(false);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    try {
      setError(null);
      setIsLoading(true);
      await registerApi(email, password);
      // NO setIsAuthenticated(true) - el usuario debe hacer login manualmente
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error al registrarse";
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loginWithGoogle = useCallback(async () => {
    try {
      setError(null);
      setIsLoading(true);
      // This will redirect to Google
      await initiateGoogleLogin();
      // Note: We won't reach here as the page will redirect
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error al iniciar sesión con Google";
      setError(errorMessage);
      setIsLoading(false);
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    await logoutApi();
    setIsAuthenticated(false);
    setError(null);
    // Redirigir a la página de login
    window.location.href = "/auth/login";
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        login,
        register,
        loginWithGoogle,
        logout,
        checkAuth,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
