import { ArchiveIcon, MessageSquareIcon, SearchIcon, SettingsIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

const conversations = [
    { id: "1", title: "Project Planning" },
    { id: "2", title: "Debug API" },
    { id: "3", title: "React Components" },
    { id: "4", title: "Database Schema" },
];

export function AppSidebar() {
    return (
        <div className="flex h-full w-64 flex-col border-r bg-sidebar text-sidebar-foreground">
            <div className="flex h-14 items-center border-b px-4">
                <span className="font-semibold">History</span>
            </div>
            <div className="flex-1 overflow-auto py-2">
                <div className="px-2 mb-2">
                    <Button variant="outline" className="w-full justify-start gap-2">
                        <SearchIcon className="size-4" />
                        <span className="text-muted-foreground">Search...</span>
                    </Button>
                </div>
                <nav className="grid gap-1 px-2">
                    {conversations.map((conversation) => (
                        <button
                            key={conversation.id}
                            className="group flex h-9 items-center rounded-lg px-3 text-sm font-medium hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                        >
                            <MessageSquareIcon className="mr-2 size-4 text-muted-foreground" />
                            <span className="truncate">{conversation.title}</span>
                        </button>
                    ))}
                </nav>
            </div>
            <div className="mt-auto border-t p-4">
                <Button variant="ghost" className="w-full justify-start gap-2 px-2">
                    <SettingsIcon className="size-4" />
                    Settings
                </Button>
            </div>
        </div>
    );
}
