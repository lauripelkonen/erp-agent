"use client";

import { useState, createContext, useContext } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  FileText,
  Activity,
  CheckSquare,
  Settings,
  Package,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const navigation = [
  { name: "Dashboard", href: "/offer-agent", icon: LayoutDashboard },
  { name: "Demo", href: "/offer-agent/demo", icon: Sparkles },
  { name: "Create Offer", href: "/offer-agent/offers/create", icon: FileText },
  { name: "Review Offers", href: "/offer-agent/offers/review", icon: CheckSquare },
  { name: "Monitoring", href: "/offer-agent/monitoring", icon: Activity },
];

// Context for sidebar state
interface SidebarContextType {
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
  isMobileOpen: boolean;
  setIsMobileOpen: (open: boolean) => void;
}

const SidebarContext = createContext<SidebarContextType | null>(null);

export function useSidebar() {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
}

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  return (
    <SidebarContext.Provider value={{ isCollapsed, setIsCollapsed, isMobileOpen, setIsMobileOpen }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function MobileMenuButton() {
  const { isMobileOpen, setIsMobileOpen } = useSidebar();

  return (
    <Button
      variant="ghost"
      size="icon"
      className="lg:hidden"
      onClick={() => setIsMobileOpen(!isMobileOpen)}
    >
      {isMobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
    </Button>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const { isCollapsed, setIsCollapsed, isMobileOpen, setIsMobileOpen } = useSidebar();

  const sidebarContent = (
    <>
      <div className="flex flex-1 flex-col overflow-y-auto pt-5 pb-4">
        <div className="flex flex-shrink-0 items-center justify-between px-4">
          <Link href="/offer-agent" className="flex items-center gap-2">
            <Package className="h-8 w-8 text-primary flex-shrink-0" />
            {!isCollapsed && <span className="text-xl font-bold">ERP Agent</span>}
          </Link>
          {/* Mobile close button */}
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setIsMobileOpen(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
        <nav className="mt-8 flex-1 space-y-1 px-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href ||
              (item.href !== "/offer-agent" && pathname?.startsWith(item.href));
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setIsMobileOpen(false)}
                className={cn(
                  "group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700",
                  isCollapsed && "justify-center"
                )}
                title={isCollapsed ? item.name : undefined}
              >
                <item.icon
                  className={cn(
                    "h-5 w-5 flex-shrink-0",
                    !isCollapsed && "mr-3",
                    isActive
                      ? "text-primary-foreground"
                      : "text-gray-400 group-hover:text-gray-500"
                  )}
                />
                {!isCollapsed && item.name}
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="flex flex-shrink-0 flex-col border-t p-4 space-y-2">
        <Link
          href="/offer-agent/settings"
          onClick={() => setIsMobileOpen(false)}
          className={cn(
            "group flex items-center px-3 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700",
            isCollapsed && "justify-center"
          )}
          title={isCollapsed ? "Settings" : undefined}
        >
          <Settings className={cn("h-5 w-5 text-gray-400 group-hover:text-gray-500", !isCollapsed && "mr-3")} />
          {!isCollapsed && "Settings"}
        </Link>
        {/* Collapse toggle button - desktop only */}
        <Button
          variant="ghost"
          size="sm"
          className={cn("hidden lg:flex w-full", isCollapsed && "justify-center")}
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4 mr-2" />
              Collapse
            </>
          )}
        </Button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 flex-col bg-white dark:bg-gray-800 border-r transition-transform duration-300 ease-in-out lg:hidden",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {sidebarContent}
      </div>

      {/* Desktop sidebar */}
      <div
        className={cn(
          "hidden lg:fixed lg:inset-y-0 lg:flex lg:flex-col border-r bg-white dark:bg-gray-800 transition-all duration-300 ease-in-out z-30",
          isCollapsed ? "lg:w-16" : "lg:w-64"
        )}
      >
        {sidebarContent}
      </div>
    </>
  );
}

// Export the width for layout calculations
export function useSidebarWidth() {
  const { isCollapsed } = useSidebar();
  return isCollapsed ? 64 : 256; // w-16 = 64px, w-64 = 256px
}
