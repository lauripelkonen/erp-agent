"use client";

import { useState } from "react";
import { Users, UserCheck, Search, Brain, Calculator, Package, Check, Loader2, ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DemoToolCall } from "@/lib/demo-data";

type ToolStatus = "running" | "completed";

interface ToolCallCardProps {
  tool: DemoToolCall;
  status: ToolStatus;
}

const iconMap = {
  Users,
  UserCheck,
  Search,
  Brain,
  Calculator,
  Package,
};

const colorMap: Record<string, string> = {
  blue: "text-blue-500 bg-blue-500/10",
  green: "text-green-500 bg-green-500/10",
  purple: "text-purple-500 bg-purple-500/10",
  orange: "text-orange-500 bg-orange-500/10",
  teal: "text-teal-500 bg-teal-500/10",
};

export function ToolCallCard({ tool, status }: ToolCallCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const Icon = iconMap[tool.icon];
  const colorClasses = colorMap[tool.color] || "text-gray-500 bg-gray-500/10";

  return (
    <div
      className={cn(
        "border rounded-lg transition-all duration-300 animate-in slide-in-from-left-2 fade-in",
        status === "running" && "border-primary shadow-sm",
        status === "completed" && "opacity-80"
      )}
    >
      <div
        className={cn(
          "flex items-center gap-3 p-3 cursor-pointer hover:bg-muted/50 rounded-lg",
          status === "running" && "bg-primary/5"
        )}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {/* Status Icon */}
        <div className={cn("flex-shrink-0 p-1.5 rounded-md", colorClasses)}>
          <Icon className="h-4 w-4" />
        </div>

        {/* Tool Name */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{tool.displayName}</p>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center gap-2">
          {status === "running" && <Loader2 className="h-4 w-4 text-primary animate-spin" />}
          {status === "completed" && <Check className="h-4 w-4 text-green-500" />}

          {/* Expand/Collapse */}
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="px-3 pb-3 pt-1 space-y-2 border-t bg-muted/30">
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Input</p>
            <pre className="text-xs bg-background p-2 rounded border overflow-x-auto">
              {JSON.stringify(tool.input, null, 2)}
            </pre>
          </div>
          {status === "completed" && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Output</p>
              <pre className="text-xs bg-background p-2 rounded border overflow-x-auto">
                {JSON.stringify(tool.output, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
