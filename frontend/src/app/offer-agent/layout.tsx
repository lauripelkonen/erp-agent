"use client";

import { Sidebar, SidebarProvider, MobileMenuButton, useSidebar } from "@/components/layout/sidebar";
import { cn } from "@/lib/utils";

function MainContent({ children }: { children: React.ReactNode }) {
  const { isCollapsed } = useSidebar();

  return (
    <main
      className={cn(
        "flex-1 overflow-auto bg-gray-50 dark:bg-gray-900 transition-all duration-300 ease-in-out",
        // Add left margin on desktop to account for fixed sidebar
        isCollapsed ? "lg:ml-16" : "lg:ml-64"
      )}
    >
      {/* Mobile header with menu button */}
      <div className="sticky top-0 z-20 flex items-center gap-4 border-b bg-white dark:bg-gray-800 px-4 py-3 lg:hidden">
        <MobileMenuButton />
        <span className="font-semibold">ERP Agent</span>
      </div>

      <div className="container mx-auto p-6">
        {children}
      </div>
    </main>
  );
}

export default function OfferAgentLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <div className="flex h-screen">
        <Sidebar />
        <MainContent>{children}</MainContent>
      </div>
    </SidebarProvider>
  );
}
