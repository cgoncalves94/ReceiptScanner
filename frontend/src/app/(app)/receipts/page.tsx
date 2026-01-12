"use client";

import { useState, useMemo, Suspense } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Receipt, ChevronRight, Calendar, Scan } from "lucide-react";
import { useReceipts } from "@/hooks";
import { FilterBar } from "@/components/receipts/filter-bar";
import { formatCurrency, formatDate, formatDistanceToNow } from "@/lib/format";
import type { ReceiptFilters } from "@/types";

function ReceiptsPageLoading() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4">
        <Skeleton className="h-10 w-full max-w-md" />
        <div className="flex items-center gap-2">
          <Skeleton className="h-10 w-[180px]" />
          <Skeleton className="h-10 w-[180px]" />
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

export default function ReceiptsPage() {
  return (
    <Suspense fallback={<ReceiptsPageLoading />}>
      <ReceiptsPageContent />
    </Suspense>
  );
}

function ReceiptsPageContent() {
  const [filters, setFilters] = useState<ReceiptFilters>({});

  // Fetch receipts with server-side filtering
  const { data: receipts, isLoading } = useReceipts(
    Object.keys(filters).length > 0 ? filters : undefined
  );

  // Also fetch all receipts (without filters) to extract unique stores
  const { data: allReceipts } = useReceipts();

  // Extract unique store names for the store filter dropdown
  const uniqueStores = useMemo(() => {
    if (!allReceipts) return [];
    const stores = new Set(allReceipts.map((r) => r.store_name));
    return Array.from(stores).sort();
  }, [allReceipts]);

  const hasFilters = Object.keys(filters).length > 0;

  return (
    <div className="space-y-6">
      {/* Filter Bar */}
      <FilterBar
        filters={filters}
        onFiltersChange={setFilters}
        stores={uniqueStores}
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
