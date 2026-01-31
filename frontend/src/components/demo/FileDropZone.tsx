"use client";

import { useState, useCallback } from "react";
import { Upload, FileText, Image, FileSpreadsheet, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface DroppedFile {
  name: string;
  type: string;
  size: number;
}

interface FileDropZoneProps {
  onFilesChanged?: (files: DroppedFile[]) => void;
  className?: string;
}

function getFileIcon(type: string) {
  if (type.startsWith("image/")) {
    return <Image className="h-4 w-4" />;
  }
  if (type.includes("spreadsheet") || type.includes("excel") || type.includes("xlsx") || type.includes("xls")) {
    return <FileSpreadsheet className="h-4 w-4" />;
  }
  return <FileText className="h-4 w-4" />;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileDropZone({ onFilesChanged, className }: FileDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<DroppedFile[]>([]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files).map((file) => ({
      name: file.name,
      type: file.type,
      size: file.size,
    }));

    const newFiles = [...files, ...droppedFiles];
    setFiles(newFiles);
    onFilesChanged?.(newFiles);
  }, [files, onFilesChanged]);

  const removeFile = useCallback((index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    setFiles(newFiles);
    onFilesChanged?.(newFiles);
  }, [files, onFilesChanged]);

  return (
    <div className={cn("space-y-3", className)}>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "border-2 border-dashed rounded-lg p-6 transition-colors cursor-pointer",
          "flex flex-col items-center justify-center gap-2 text-center",
          isDragging
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-muted-foreground/50"
        )}
      >
        <Upload className={cn("h-8 w-8", isDragging ? "text-primary" : "text-muted-foreground")} />
        <div>
          <p className="text-sm font-medium">
            {isDragging ? "Drop files here" : "Drag and drop files"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Images, Excel, PDFs, Word documents
          </p>
        </div>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground">{files.length} file(s) attached</p>
          <div className="space-y-1">
            {files.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center gap-2 p-2 bg-muted/50 rounded-md text-sm"
              >
                {getFileIcon(file.type)}
                <span className="flex-1 truncate">{file.name}</span>
                <span className="text-xs text-muted-foreground">{formatFileSize(file.size)}</span>
                <button
                  onClick={() => removeFile(index)}
                  className="p-1 hover:bg-muted rounded"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
