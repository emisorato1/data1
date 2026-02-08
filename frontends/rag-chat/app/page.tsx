"use client";

import { Assistant } from "./assistant";
import { AppSidebar } from "@/components/app-sidebar";

export default function Home() {
  // El middleware de Next.js redirige a /auth/login si no hay cookie
  // Por lo tanto, si llegamos aquí es porque el usuario está autenticado
  return (
    <main className="flex h-dvh overflow-hidden">
      <AppSidebar />
      <div className="flex-1 min-w-0">
        <Assistant />
      </div>
    </main>
  );
}
