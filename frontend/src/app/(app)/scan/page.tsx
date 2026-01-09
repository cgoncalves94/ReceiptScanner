"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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

  return (
    <div className="max-w-2xl mx-auto">
      <Card className="bg-card/50 border-border/50">
        <CardHeader>
          <CardTitle>Scan Receipt</CardTitle>
          <CardDescription>
            Upload a photo of your receipt and let AI extract the details
          </CardDescription>
        </CardHeader>
        <CardContent>
          {scanMutation.isPending ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-12 w-12 text-amber-500 animate-spin mb-4" />
              <p className="text-lg font-medium">Analyzing receipt...</p>
              <p className="text-muted-foreground">
                This may take a few seconds
              </p>
            </div>
          ) : scannedReceipt ? (
            <ScanResult
              receipt={scannedReceipt}
              onScanAnother={handleScanAnother}
            />
          ) : (
            <Dropzone
              onFileSelect={handleFileSelect}
              disabled={scanMutation.isPending}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
