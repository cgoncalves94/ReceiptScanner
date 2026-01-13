"use client";

import { useMemo, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Receipt, TrendingUp, ShoppingCart, CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useReceipts } from "@/hooks";
import { formatDistanceToNow } from "@/lib/format";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

// Group amounts by currency
function groupByCurrency(receipts: { total_amount: number; currency: string }[]) {
  const groups = new Map<string, number>();
  receipts.forEach((r) => {
    const current = groups.get(r.currency) ?? 0;
    groups.set(r.currency, current + Number(r.total_amount));
  });
  return groups;
}

// Format currency totals as string
function formatCurrencyTotals(groups: Map<string, number>) {
  if (groups.size === 0) return "0.00";
  return Array.from(groups.entries())
    .map(([currency, amount]) => `${currency}${amount.toFixed(2)}`)
    .join(" • ");
}

export default function Dashboard() {
  const { data: receipts, isLoading } = useReceipts();

  // Month/Year selector state - default to current month
  // Using "all" for all months view, or month index as string
  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth();
  const [selectedMonth, setSelectedMonth] = useState<string>(currentMonth.toString());
  const [selectedYear, setSelectedYear] = useState(currentYear);

  // Available years - go back 30 years to cover historical receipts (consistent with Analytics)
  const availableYears = Array.from(
    { length: 30 },
    (_, i) => currentYear - i
  );

  // Filter receipts for selected month
  const monthReceipts = useMemo(() => {
    return receipts?.filter((r) => {
      const purchaseDate = new Date(r.purchase_date);
      const yearMatches = purchaseDate.getFullYear() === selectedYear;
      if (selectedMonth === "all") return yearMatches;
      return yearMatches && purchaseDate.getMonth() === parseInt(selectedMonth);
    }) ?? [];
  }, [receipts, selectedMonth, selectedYear]);

  // Stats for selected month (grouped by currency)
  const monthTotals = groupByCurrency(monthReceipts);
  const receiptCount = monthReceipts.length;
  const recentReceipts = monthReceipts.slice(0, 5);

  // Navigation helpers
  const goToPrevMonth = () => {
    if (selectedMonth === "all") {
      setSelectedYear(selectedYear - 1);
    } else if (selectedMonth === "0") {
      setSelectedMonth("11");
      setSelectedYear(selectedYear - 1);
    } else {
      setSelectedMonth((parseInt(selectedMonth) - 1).toString());
    }
  };

  const goToNextMonth = () => {
    if (selectedMonth === "all") {
      setSelectedYear(selectedYear + 1);
    } else if (selectedMonth === "11") {
      setSelectedMonth("0");
      setSelectedYear(selectedYear + 1);
    } else {
      setSelectedMonth((parseInt(selectedMonth) + 1).toString());
    }
  };

  const isCurrentMonth = selectedMonth === currentMonth.toString() && selectedYear === currentYear;

  return (
    <div className="space-y-6">
      {/* Month Selector */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={goToPrevMonth}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-2">
            <Select value={selectedMonth} onValueChange={setSelectedMonth}>
              <SelectTrigger className="w-32">
                <SelectValue />
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
            <Select value={selectedYear.toString()} onValueChange={(v) => setSelectedYear(parseInt(v))}>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {availableYears.map((year) => (
                  <SelectItem key={year} value={year.toString()}>
                    {year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button variant="outline" size="icon" onClick={goToNextMonth}>
            <ChevronRight className="h-4 w-4" />
          </Button>
          {!isCurrentMonth && selectedMonth !== "all" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSelectedMonth(currentMonth.toString());
                setSelectedYear(currentYear);
              }}
            >
              Today
            </Button>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Receipts
            </CardTitle>
            <Receipt className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">{receiptCount}</div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card/50 border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Spent
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <div className="text-2xl font-bold text-amber-500">
                {formatCurrencyTotals(monthTotals)}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card/50 border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg per Receipt
            </CardTitle>
            <ShoppingCart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">
                {receiptCount > 0
                  ? formatCurrencyTotals(
                      new Map(
                        Array.from(monthTotals.entries()).map(([currency, total]) => [
                          currency,
                          total / receiptCount,
                        ])
                      )
                    )
                  : "—"}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Receipts for this Month */}
      <Card className="bg-card/50 border-border/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{selectedMonth === "all" ? `${selectedYear}` : MONTHS[parseInt(selectedMonth)]} Receipts</CardTitle>
              <CardDescription>
                {receiptCount === 0
                  ? `No receipts ${selectedMonth === "all" ? "this year" : "this month"}`
                  : `${receiptCount} receipt${receiptCount !== 1 ? "s" : ""} in ${selectedMonth === "all" ? selectedYear : `${MONTHS[parseInt(selectedMonth)]} ${selectedYear}`}`}
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" asChild>
              <Link href={`/receipts?year=${selectedYear}${selectedMonth !== "all" ? `&month=${selectedMonth}` : ""}`}>View All</Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : recentReceipts.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <CalendarDays className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No receipts in {selectedMonth === "all" ? selectedYear : MONTHS[parseInt(selectedMonth)]}</p>
              <p className="text-sm">Scan a receipt to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentReceipts.map((receipt) => (
                <Link
                  key={receipt.id}
                  href={`/receipts/${receipt.id}`}
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-accent transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                      <Receipt className="h-5 w-5 text-amber-500" />
                    </div>
                    <div>
                      <p className="font-medium">{receipt.store_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatDistanceToNow(receipt.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">
                      {receipt.currency}{Number(receipt.total_amount).toFixed(2)}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {receipt.items.length} items
                    </p>
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
