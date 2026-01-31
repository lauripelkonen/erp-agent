"use client";

import { Progress } from "@/components/ui/progress";
import { ToolCallCard } from "./ToolCallCard";
import type { DemoToolCall } from "@/lib/demo-data";

type ToolStatus = "running" | "completed";

interface ToolVisualizationProps {
  tools: DemoToolCall[];
  currentToolIndex: number;
  isProcessing: boolean;
}

export function ToolVisualization({ tools, currentToolIndex, isProcessing }: ToolVisualizationProps) {
  const completedCount = currentToolIndex;
  const totalTools = tools.length;
  const progress = totalTools > 0 ? (completedCount / totalTools) * 100 : 0;

  // Only show tools that have been started (index <= currentToolIndex)
  const visibleTools = tools.slice(0, currentToolIndex + (isProcessing ? 1 : 0));

  const getToolStatus = (index: number): ToolStatus => {
    if (index < currentToolIndex) return "completed";
    return "running";
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">AI Tool Execution</span>
          <span className="font-medium">
            {completedCount}/{totalTools} completed
          </span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
        {visibleTools.map((tool, index) => (
          <ToolCallCard
            key={tool.tool}
            tool={tool}
            status={getToolStatus(index)}
          />
        ))}
      </div>

      {!isProcessing && currentToolIndex === 0 && (
        <p className="text-sm text-muted-foreground text-center py-8">
          Click "Process Offer" to start the AI workflow
        </p>
      )}

      {!isProcessing && currentToolIndex === totalTools && totalTools > 0 && (
        <p className="text-sm text-green-600 text-center py-2 font-medium">
          All tools completed successfully!
        </p>
      )}
    </div>
  );
}
