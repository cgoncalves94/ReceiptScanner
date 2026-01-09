"use client";

import { useMemo, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { BarChart3, TrendingUp, FolderOpen, ChevronLeft, ChevronRight, Receipt, RefreshCw } from "lucide-react";
import {
  useReceipts,
  useCategories,
  useCategoryItems,
  useExchangeRates,
  convertAmount,
  convertAndSum,
  codeToSymbol,
  symbolToCode,
  SUPPORTED_CURRENCIES,
} from "@/hooks";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

export default function AnalyticsPage() {
  const { data: receipts, isLoading: receiptsLoading } = useReceipts();
  const { data: categories, isLoading: categoriesLoading } = useCategories();

  // Month/Year selector - "all" means all months in the year
  const now = new Date();
  const [selectedMonth, setSelectedMonth] = useState<string>(now.getMonth().toString());
  const [selectedYear, setSelectedYear] = useState(now.getFullYear());

  // Currency selector - default to most common currency in receipts
  const [displayCurrency, setDisplayCurrency] = useState<string>("EUR");

  // Category detail modal
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const { data: categoryItems, isLoading: itemsLoading } = useCategoryItems(selectedCategoryId);

  // Fetch exchange rates for display currency
  const { data: exchangeRates, isLoading: ratesLoading, refetch: refetchRates } = useExchangeRates(displayCurrency);

  const isLoading = receiptsLoading || categoriesLoading;

  // Get available years
  const availableYears = useMemo(() => {
    if (!receipts?.length) return [now.getFullYear()];
    const years = new Set(receipts.map((r) => new Date(r.purchase_date).getFullYear()));
    years.add(now.getFullYear());
    return Array.from(years).sort((a, b) => b - a);
  }, [receipts, now]);

  // Filter receipts for selected period
  const filteredReceipts = useMemo(() => {
    return receipts?.filter((r) => {
      const purchaseDate = new Date(r.purchase_date);
      const yearMatch = purchaseDate.getFullYear() === selectedYear;
      if (selectedMonth === "all") return yearMatch;
      return yearMatch && purchaseDate.getMonth() === parseInt(selectedMonth);
    }) ?? [];
  }, [receipts, selectedMonth, selectedYear]);

  // Get all items from filtered receipts
  const filteredItems = useMemo(() => {
    return filteredReceipts.flatMap((r) => r.items);
  }, [filteredReceipts]);

  // Category spending breakdown
  const categorySpending = useMemo(() => {
    const spending = new Map<number, { name: string; items: typeof filteredItems; total: number }>();

    // Initialize with all categories
    categories?.forEach((cat) => {
      spending.set(cat.id, { name: cat.name, items: [], total: 0 });
    });

    // Group items by category and convert to display currency
    filteredItems.forEach((item) => {
      if (item.category_id) {
        const entry = spending.get(item.category_id);
        if (entry) {
          entry.items.push(item);
          const converted = convertAmount(
            Number(item.total_price),
            item.currency,
            displayCurrency,
            exchangeRates
          );
          entry.total += converted;
        }
      }
    });

    // Filter to only categories with spending and sort by total
    return Array.from(spending.entries())
      .filter(([_, data]) => data.items.length > 0)
      .sort((a, b) => b[1].total - a[1].total);
  }, [categories, filteredItems, displayCurrency, exchangeRates]);

  // Stats - convert all to display currency
  const totalSpent = useMemo(() => {
    return convertAndSum(
      filteredReceipts.map((r) => ({ amount: Number(r.total_amount), currency: r.currency })),
      displayCurrency,
      exchangeRates
    );
  }, [filteredReceipts, displayCurrency, exchangeRates]);

  const receiptCount = filteredReceipts.length;
  const avgPerReceipt = receiptCount > 0 ? totalSpent / receiptCount : 0;

  // Navigation
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

  const isCurrentPeriod = selectedMonth === now.getMonth().toString() && selectedYear === now.getFullYear();

  // Filter category items by selected period (using Map for O(1) receipt lookup)
  const filteredCategoryItems = useMemo(() => {
    if (!categoryItems || !receipts) return [];
    const receiptsMap = new Map(receipts.map((r) => [r.id, r]));
    return categoryItems.filter((item) => {
      const receipt = receiptsMap.get(item.receipt_id);
      if (!receipt) return false;
      const purchaseDate = new Date(receipt.purchase_date);
      const yearMatch = purchaseDate.getFullYear() === selectedYear;
      if (selectedMonth === "all") return yearMatch;
      return yearMatch && purchaseDate.getMonth() === parseInt(selectedMonth);
    });
  }, [categoryItems, receipts, selectedMonth, selectedYear]);

  const selectedCategory = categories?.find((c) => c.id === selectedCategoryId);
  const currencySymbol = codeToSymbol(displayCurrency);

  // Period label
  const periodLabel = selectedMonth === "all"
    ? `${selectedYear}`
    : `${MONTHS[parseInt(selectedMonth)]} ${selectedYear}`;

  return (
    <div className="space-y-6">
      {/* Controls Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Month/Year Navigation */}
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={goToPrevMonth}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-2">
            <Select value={selectedMonth} onValueChange={setSelectedMonth}>
              <SelectTrigger className="w-[130px]">
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
              <SelectTrigger className="w-[100px]">
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
          {!isCurrentPeriod && selectedMonth !== "all" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSelectedMonth(now.getMonth().toString());
                setSelectedYear(now.getFullYear());
              }}
            >
              Today
            </Button>
          )}
        </div>

        {/* Currency Selector */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Display in:</span>
          <Select value={displayCurrency} onValueChange={setDisplayCurrency}>
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SUPPORTED_CURRENCIES.map((curr) => (
                <SelectItem key={curr.code} value={curr.code}>
                  {curr.symbol} {curr.code}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => refetchRates()}
            disabled={ratesLoading}
            title="Refresh exchange rates"
          >
            <RefreshCw className={`h-4 w-4 ${ratesLoading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Exchange rate info */}
      {exchangeRates && (
        <p className="text-xs text-muted-foreground">
          Rates as of {exchangeRates.date} from Frankfurter API
        </p>
      )}

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Spent
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            {isLoading || ratesLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <div className="text-2xl font-bold text-amber-500">
                {currencySymbol}{totalSpent.toFixed(2)}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card/50 border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Receipts
            </CardTitle>
            <Receipt className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{receiptCount}</div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card/50 border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg per Receipt
            </CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading || ratesLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">
                {currencySymbol}{avgPerReceipt.toFixed(2)}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card/50 border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Categories Used
            </CardTitle>
            <FolderOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{categorySpending.length}</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Category Breakdown */}
      <Card className="bg-card/50 border-border/50">
        <CardHeader>
          <CardTitle>Spending by Category</CardTitle>
          <CardDescription>{periodLabel} breakdown</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading || ratesLoading ? (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : categorySpending.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No category data for {periodLabel}</p>
              <p className="text-sm">Scan receipts to see breakdown</p>
            </div>
          ) : (
            <div className="space-y-3">
              {categorySpending.map(([categoryId, data]) => {
                const percentage = totalSpent > 0 ? (data.total / totalSpent) * 100 : 0;
                return (
                  <button
                    key={categoryId}
                    onClick={() => setSelectedCategoryId(categoryId)}
                    className="w-full text-left"
                  >
                    <div className="flex items-center justify-between p-4 rounded-lg bg-accent/50 hover:bg-accent transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                          <FolderOpen className="h-5 w-5 text-amber-500" />
                        </div>
                        <div>
                          <p className="font-medium">{data.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {data.items.length} item{data.items.length !== 1 ? "s" : ""} • {percentage.toFixed(1)}%
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-amber-500">
                          {currencySymbol}{data.total.toFixed(2)}
                        </p>
                      </div>
                    </div>
                    {/* Progress bar */}
                    <div className="h-1 mt-1 bg-accent rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber-500 rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Category Items Modal */}
      <Dialog open={selectedCategoryId !== null} onOpenChange={(open) => !open && setSelectedCategoryId(null)}>
        <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedCategory?.name} Items</DialogTitle>
            <DialogDescription>
              {periodLabel} • {filteredCategoryItems.length} item{filteredCategoryItems.length !== 1 ? "s" : ""}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 pt-4">
            {itemsLoading ? (
              <div className="space-y-2">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : filteredCategoryItems.length === 0 ? (
              <p className="text-center text-muted-foreground py-4">
                No items in this category for {periodLabel}
              </p>
            ) : (
              filteredCategoryItems.map((item) => {
                const convertedPrice = convertAmount(
                  Number(item.total_price),
                  item.currency,
                  displayCurrency,
                  exchangeRates
                );
                const isConverted = symbolToCode(item.currency) !== displayCurrency;
                return (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-accent/50"
                  >
                    <div>
                      <p className="font-medium">{item.name}</p>
                      <p className="text-sm text-muted-foreground">
                        Qty: {item.quantity} × {item.currency}{Number(item.unit_price).toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge variant="secondary" className="font-semibold">
                        {currencySymbol}{convertedPrice.toFixed(2)}
                      </Badge>
                      {isConverted && (
                        <p className="text-xs text-muted-foreground mt-1">
                          ({item.currency}{Number(item.total_price).toFixed(2)})
                        </p>
                      )}
                    </div>
                  </div>
                );
              })
            )}
            {filteredCategoryItems.length > 0 && (
              <div className="pt-4 border-t flex justify-between items-center">
                <span className="font-medium">Total</span>
                <span className="font-bold text-amber-500">
                  {currencySymbol}
                  {convertAndSum(
                    filteredCategoryItems.map((i) => ({
                      amount: Number(i.total_price),
                      currency: i.currency,
                    })),
                    displayCurrency,
                    exchangeRates
                  ).toFixed(2)}
                </span>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
