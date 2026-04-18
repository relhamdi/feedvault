import { FeedTabs } from "@/components/feeds/FeedTabs";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { SidebarProvider } from "@/components/ui/sidebar";
import { useState } from "react";

export default function App() {
  const [selectedSourceId, setSelectedSourceId] = useState<number | null>(null);

  return (
    <SidebarProvider>
      <div className="flex h-screen w-full overflow-hidden bg-background">
        <AppSidebar
          selectedSourceId={selectedSourceId}
          onSelectSource={setSelectedSourceId}
        />
        <main className="flex-1 overflow-hidden h-full">
          {selectedSourceId ? (
            <FeedTabs sourceId={selectedSourceId} />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              Select a source to get started
            </div>
          )}
        </main>
      </div>
    </SidebarProvider>
  );
}
