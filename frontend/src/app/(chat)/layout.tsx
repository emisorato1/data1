"use client";

import React from "react";
import { ChatProvider } from "@/context/chat-context";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { useAuthSession } from "@/lib/use-auth-session";

/** Inner layout — useAuthSession requires being inside the client tree */
function AuthenticatedShell({ children }: { children: React.ReactNode }) {
    // Silently refreshes the access token every 13 minutes.
    // Redirects to /login if the refresh_token is also expired.
    useAuthSession();

    return (
        <div className="flex h-screen bg-background overflow-hidden font-sans">
            <ChatSidebar />
            <main className="flex-1 flex flex-col relative h-full overflow-hidden">
                {children}
            </main>
        </div>
    );
}

export default function ChatLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <ChatProvider>
            <AuthenticatedShell>{children}</AuthenticatedShell>
        </ChatProvider>
    );
}
