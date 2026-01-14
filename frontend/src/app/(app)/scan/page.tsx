"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Dropzone, ScanResult } from "@/components/scan";
import { useScanReceipt } from "@/hooks";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import type { Receipt } from "@/types";

export default function ScanPage() {
  const [scannedReceipt, setScannedReceipt] = useState<Receipt | null>(null);
  const scanMutation = useScanReceipt();

  const handleFileSelect = async (file: File) => {
    try {
      const receipt = await scanMutation.mutateAsync(file);
      setScannedReceipt(receipt);
      toast.success("Receipt scanned successfully!");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to scan receipt"
      );
    }
  };

  const handleScanAnother = () => {
    setScannedReceipt(null);
  };

  // Show scan result in a card when we have one
  if (scannedReceipt) {
    return (
      <div className="max-w-3xl mx-auto">
        <Card className="bg-card/50 border-border/50">
          <CardContent className="pt-6">
            <ScanResult
              receipt={scannedReceipt}
              onScanAnother={handleScanAnother}
            />
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show loading state
  if (scanMutation.isPending) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-10rem)]">
        <Loader2 className="h-20 w-20 text-amber-500 animate-spin mb-6" />
        <p className="text-2xl font-medium">Analyzing receipt...</p>
        <p className="text-muted-foreground mt-2">
          This may take a few seconds
        </p>
      </div>
    );
  }

  // Full-page dropzone
  return (
    <Dropzone
      onFileSelect={handleFileSelect}
      disabled={scanMutation.isPending}
      fullPage
    />
  );
}
