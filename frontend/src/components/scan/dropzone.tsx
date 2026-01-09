"use client";

import { useCallback, useState } from "react";
import { cn } from "@/lib/utils";
import { Upload, Image as ImageIcon, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DropzoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export function Dropzone({ onFileSelect, disabled }: DropzoneProps) {
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
      <div className="space-y-4">
        <div className="relative rounded-xl overflow-hidden border border-border/50 bg-card/50">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={preview}
            alt="Receipt preview"
            className="w-full max-h-125 object-contain"
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
        "flex flex-col items-center justify-center p-12",
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

      <div className="h-16 w-16 rounded-2xl bg-amber-500/10 flex items-center justify-center mb-4">
        <Upload className="h-8 w-8 text-amber-500" />
      </div>

      <p className="text-lg font-medium mb-1">
        {isDragging ? "Drop your receipt here" : "Drag & drop your receipt"}
      </p>
      <p className="text-muted-foreground mb-4">or click to browse</p>

      <p className="text-sm text-muted-foreground">
        Supports JPG, PNG, HEIC up to 10MB
      </p>
    </div>
  );
}
