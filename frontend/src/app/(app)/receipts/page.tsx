"use client";

import { useState, Suspense, useMemo } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Receipt, ChevronRight, Calendar, Scan, Download, Loader2, FileText } from "lucide-react";
import { useReceipts, useStores, useExportReceipts, useExportReceiptsPdf } from "@/hooks";
import { FilterBar } from "@/components/receipts/filter-bar";
import { formatCurrency, formatDate, formatDistanceToNow } from "@/lib/format";
import type { ReceiptFilters } from "@/types";
import { toast } from "sonner";

function ReceiptsPageLoading() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4">
        <Skeleton className="h-10 w-full max-w-md" />
        <div className="flex items-center gap-2">
          <Skeleton className="h-10 w-45" />
          <Skeleton className="h-10 w-45" />
        </div>
      </div>
      <Card className="bg-card/50 border-border/50">
        <CardHeader>
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-24" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

const formatLocalDate = (date: Date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

export default function ReceiptsPage() {
  return (
    <Suspense fallback={<ReceiptsPageLoading />}>
      <ReceiptsPageContent />
    </Suspense>
  );
}

function ReceiptsPageContent() {
  const searchParams = useSearchParams();

  // Compute initial filters from URL params (year/month from dashboard)
  const initialFilters = useMemo((): ReceiptFilters => {
    const yearParam = searchParams.get("year");
    const monthParam = searchParams.get("month");

    if (!yearParam) return {};

    const year = parseInt(yearParam);
    if (isNaN(year)) return {};

    // If month is provided and not "all", filter to that specific month
    // Month is 0-indexed (0=January, 11=December) to match Dashboard/Analytics state
    if (monthParam && monthParam !== "all") {
      const month = parseInt(monthParam);
      if (!isNaN(month) && month >= 0 && month <= 11) {
        const startDate = new Date(year, month, 1);
        const endDate = new Date(year, month + 1, 0); // Last day of month
        return {
          after: formatLocalDate(startDate),
          before: formatLocalDate(endDate),
        };
      }
    }

    // Otherwise filter to entire year
    return {
      after: `${year}-01-01`,
      before: `${year}-12-31`,
    };
  }, [searchParams]);

  const [filters, setFilters] = useState<ReceiptFilters>(initialFilters);

  // Fetch receipts with server-side filtering
  const { data: receipts, isLoading } = useReceipts(
    Object.keys(filters).length > 0 ? filters : undefined
  );

  // Fetch unique store names from dedicated endpoint
  const { data: stores = [] } = useStores();

  // Export receipts mutation
  const exportMutation = useExportReceipts();
  const exportPdfMutation = useExportReceiptsPdf();

  const hasFilters = Object.keys(filters).length > 0;

  const handleExport = async () => {
    try {
      await exportMutation.mutateAsync(
        Object.keys(filters).length > 0 ? filters : undefined
      );
      toast.success("Receipts exported successfully!");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to export receipts"
      );
    }
  };

  const handleExportPdf = async () => {
    try {
      await exportPdfMutation.mutateAsync(
        Object.keys(filters).length > 0 ? filters : undefined
      );
      toast.success("PDF report generated successfully!");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to generate PDF report"
      );
    }
  };

  return (
    <div className="space-y-6">
      {/* Export Buttons */}
      <div className="flex justify-end gap-2">
        <Button
          onClick={handleExportPdf}
          disabled={exportPdfMutation.isPending || isLoading || receipts?.length === 0}
          variant="outline"
          className="border-amber-500/20 hover:bg-amber-500/10 hover:text-amber-500"
        >
          {exportPdfMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <FileText className="h-4 w-4 mr-2" />
              Export PDF
            </>
          )}
        </Button>
        <Button
          onClick={handleExport}
          disabled={exportMutation.isPending || isLoading || receipts?.length === 0}
          className="bg-amber-500 hover:bg-amber-600 text-black"
        >
          {exportMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Exporting...
            </>
          ) : (
            <>
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </>
          )}
        </Button>
      </div>

      {/* Filter Bar */}
      <FilterBar
        filters={filters}
        onFiltersChange={setFilters}
        stores={stores}
      />

      {/* Receipts List */}
      <Card className="bg-card/50 border-border/50">
        <CardHeader>
          <CardTitle>
            {hasFilters ? "Filtered Receipts" : "All Receipts"}
          </CardTitle>
          <CardDescription>
            {isLoading
              ? "Loading..."
              : `${receipts?.length ?? 0} receipt${receipts?.length !== 1 ? "s" : ""} found`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : receipts?.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Receipt className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-lg font-medium">No receipts found</p>
              <p className="text-sm">
                {hasFilters
                  ? "Try adjusting your filters"
                  : "Scan your first receipt to get started"}
              </p>
              {!hasFilters && (
                <Button
                  className="mt-4 bg-amber-500 hover:bg-amber-600 text-black"
                  asChild
                >
                  <Link href="/scan">
                    <Scan className="h-4 w-4 mr-2" />
                    Scan Receipt
                  </Link>
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {receipts?.map((receipt) => (
                <Link
                  key={receipt.id}
                  href={`/receipts/${receipt.id}`}
                  className="flex items-center justify-between p-4 rounded-lg hover:bg-accent transition-colors group"
                >
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-amber-500/10 flex items-center justify-center shrink-0">
                      <Receipt className="h-6 w-6 text-amber-500" />
                    </div>
                    <div>
                      <p className="font-medium group-hover:text-amber-500 transition-colors">
                        {receipt.store_name}
                      </p>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Calendar className="h-3.5 w-3.5" />
                        <span>{formatDate(receipt.purchase_date)}</span>
                        <span className="text-border">•</span>
                        <span>{receipt.items.length} items</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-semibold text-lg">
                        {formatCurrency(Number(receipt.total_amount), receipt.currency)}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {formatDistanceToNow(receipt.created_at)}
                      </p>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-amber-500 transition-colors" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
