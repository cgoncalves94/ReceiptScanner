"use client";

import { useState, useMemo, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Receipt, Search, ChevronRight, Calendar, Scan, X } from "lucide-react";
import { useReceipts } from "@/hooks";
import { formatCurrency, formatDate, formatDistanceToNow } from "@/lib/format";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

function ReceiptsPageLoading() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <Skeleton className="h-10 w-full max-w-sm" />
          <div className="flex items-center gap-2">
            <Skeleton className="h-10 w-[120px]" />
            <Skeleton className="h-10 w-[140px]" />
          </div>
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
  const searchParams = useSearchParams();
  const { data: receipts, isLoading } = useReceipts();
  const [search, setSearch] = useState("");

  // Initialize filters from URL params (from Dashboard "View All" link)
  const initialYear = searchParams.get("year");
  const initialMonth = searchParams.get("month");

  const [selectedYear, setSelectedYear] = useState<string>(initialYear ?? "all");
  const [selectedMonth, setSelectedMonth] = useState<string>(initialMonth ?? "all");

  // Get unique years from receipts (based on purchase_date)
  // Always include current year even if no receipts exist for it
  const availableYears = useMemo(() => {
    const currentYear = new Date().getFullYear();
    const years = new Set<number>([currentYear]);

    receipts?.forEach((r) => {
      years.add(new Date(r.purchase_date).getFullYear());
    });

    // Also include the year from URL param if provided
    if (initialYear && initialYear !== "all") {
      years.add(parseInt(initialYear));
    }

    return Array.from(years).sort((a, b) => b - a); // Descending
  }, [receipts, initialYear]);

  // Filter receipts by search, year, and month
  const filteredReceipts = useMemo(() => {
    return receipts?.filter((receipt) => {
      // Search filter
      if (search && !receipt.store_name.toLowerCase().includes(search.toLowerCase())) {
        return false;
      }
      // Year filter
      if (selectedYear !== "all") {
        const year = new Date(receipt.purchase_date).getFullYear();
        if (year !== parseInt(selectedYear)) return false;
      }
      // Month filter
      if (selectedMonth !== "all") {
        const month = new Date(receipt.purchase_date).getMonth();
        if (month !== parseInt(selectedMonth)) return false;
      }
      return true;
    });
  }, [receipts, search, selectedYear, selectedMonth]);

  const hasFilters = selectedYear !== "all" || selectedMonth !== "all";

  const clearFilters = () => {
    setSelectedYear("all");
    setSelectedMonth("all");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search receipts..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <div className="flex items-center gap-2">
            <Select value={selectedYear} onValueChange={setSelectedYear}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Year" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Years</SelectItem>
                {availableYears.map((year) => (
                  <SelectItem key={year} value={year.toString()}>
                    {year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={selectedMonth} onValueChange={setSelectedMonth}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Month" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Months</SelectItem>
                {MONTHS.map((month, index) => (
                  <SelectItem key={index} value={index.toString()}>
                    {month}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {hasFilters && (
              <Button variant="ghost" size="icon" onClick={clearFilters}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Receipts List */}
      <Card className="bg-card/50 border-border/50">
        <CardHeader>
          <CardTitle>
            {hasFilters
              ? `${selectedMonth !== "all" ? MONTHS[parseInt(selectedMonth)] : ""} ${selectedYear !== "all" ? selectedYear : ""}`.trim() || "Filtered Receipts"
              : "All Receipts"}
          </CardTitle>
          <CardDescription>
            {isLoading
              ? "Loading..."
              : `${filteredReceipts?.length ?? 0} receipt${filteredReceipts?.length !== 1 ? "s" : ""} found`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : filteredReceipts?.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Receipt className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-lg font-medium">No receipts found</p>
              <p className="text-sm">
                {search
                  ? "Try a different search term"
                  : "Scan your first receipt to get started"}
              </p>
              {!search && (
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
              {filteredReceipts?.map((receipt) => (
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
