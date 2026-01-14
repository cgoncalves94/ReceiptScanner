"use client";

import { useCallback, useState } from "react";
import { cn } from "@/lib/utils";
import { Upload, Image as ImageIcon, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DropzoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  fullPage?: boolean;
}

export function Dropzone({ onFileSelect, disabled, fullPage }: DropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFile = useCallback(
    (file: File) => {
      if (!file.type.startsWith("image/")) {
        return;
      }

      setSelectedFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    },
    []
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const file = e.dataTransfer.files[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  const handleClear = useCallback(() => {
    setPreview(null);
    setSelectedFile(null);
  }, []);

  const handleScan = useCallback(() => {
    if (selectedFile) {
      onFileSelect(selectedFile);
    }
  }, [selectedFile, onFileSelect]);

  if (preview && selectedFile) {
    return (
      <div className={cn("space-y-4", fullPage && "max-w-4xl mx-auto")}>
        <div className="relative rounded-xl overflow-hidden border border-border/50 bg-card/50">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={preview}
            alt="Receipt preview"
            className="w-full max-h-[60vh] object-contain"
          />
          <Button
            variant="secondary"
            size="icon"
            className="absolute top-3 right-3"
            onClick={handleClear}
            disabled={disabled}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex items-center justify-between p-4 rounded-lg bg-card/50 border border-border/50">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
              <ImageIcon className="h-5 w-5 text-amber-500" />
            </div>
            <div>
              <p className="font-medium truncate max-w-50">{selectedFile.name}</p>
              <p className="text-sm text-muted-foreground">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>

          <Button
            className="bg-amber-500 hover:bg-amber-600 text-black"
            onClick={handleScan}
            disabled={disabled}
          >
            {disabled ? "Scanning..." : "Scan Receipt"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={cn(
        "relative rounded-xl border-2 border-dashed transition-colors",
        "flex flex-col items-center justify-center",
        fullPage
          ? "min-h-[calc(100vh-10rem)] p-8"
          : "p-12 min-h-100",
        isDragging
          ? "border-amber-500 bg-amber-500/5"
          : "border-border/50 hover:border-amber-500/50 hover:bg-amber-500/5",
        disabled && "opacity-50 pointer-events-none"
      )}
    >
      <input
        type="file"
        accept="image/*"
        onChange={handleInputChange}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        disabled={disabled}
        aria-label="Upload receipt image"
      />

      <div className={cn(
        "rounded-2xl bg-amber-500/10 flex items-center justify-center mb-6",
        fullPage ? "h-24 w-24" : "h-16 w-16"
      )}>
        <Upload className={cn("text-amber-500", fullPage ? "h-12 w-12" : "h-8 w-8")} />
      </div>

      <p className={cn("font-medium mb-2", fullPage ? "text-2xl" : "text-lg")}>
        {isDragging ? "Drop your receipt here" : "Drag & drop your receipt"}
      </p>
      <p className={cn("text-muted-foreground mb-4", fullPage && "text-lg")}>
        or click anywhere to browse
      </p>

      <p className="text-sm text-muted-foreground">
        Supports JPG, PNG, HEIC up to 10MB
      </p>
    </div>
  );
}
