"use client";

import { useState } from "react";
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
import { BarChart3, TrendingUp, FolderOpen, ChevronLeft, ChevronRight, Receipt } from "lucide-react";
import {
  useAnalyticsSummary,
  useCategoryBreakdown,
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
  // Month/Year selector - "all" means all months in the year
  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth();
  const [selectedMonth, setSelectedMonth] = useState<string>(currentMonth.toString());
  const [selectedYear, setSelectedYear] = useState(currentYear);

  // Currency selector
  const [displayCurrency, setDisplayCurrency] = useState<string>("EUR");

  // Category detail modal
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const { data: categoryItems, isLoading: itemsLoading } = useCategoryItems(selectedCategoryId);

  // Fetch exchange rates for category items display (still needed for modal)
  const { data: exchangeRates } = useExchangeRates(displayCurrency);

  // Parse month for API calls
  const monthForApi = selectedMonth === "all" ? undefined : parseInt(selectedMonth);

  // Backend analytics hooks
  const { data: summary, isLoading: summaryLoading } = useAnalyticsSummary(
    selectedYear,
    monthForApi,
    displayCurrency
  );

  const { data: categoryBreakdown, isLoading: breakdownLoading } = useCategoryBreakdown(
    selectedYear,
    monthForApi,
    displayCurrency
  );

  const isLoading = summaryLoading || breakdownLoading;

  // Available years (simple range for now)
  const availableYears = Array.from(
    { length: 10 },
    (_, i) => currentYear - i
  );

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

  const isCurrentPeriod = selectedMonth === currentMonth.toString() && selectedYear === currentYear;

  // Filter category items by selected period for modal
  const filteredCategoryItems = categoryItems?.filter((item) => {
    // We don't have receipt data here, so show all items from this category
    // In future, we could add a dedicated endpoint for this
    return true;
  }) ?? [];

  const selectedCategory = categoryBreakdown?.categories.find(
    (c) => c.category_id === selectedCategoryId
  );
  const currencySymbol = codeToSymbol(displayCurrency);

  // Period label
  const periodLabel = selectedMonth === "all"
    ? `${selectedYear}`
    : `${MONTHS[parseInt(selectedMonth)]} ${selectedYear}`;

  // Stats from backend
  const totalSpent = summary?.total_spent ?? 0;
  const receiptCount = summary?.receipt_count ?? 0;
  const avgPerReceipt = summary?.avg_per_receipt ?? 0;
  const categoriesCount = categoryBreakdown?.categories.length ?? 0;

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
          {!isCurrentPeriod && selectedMonth !== "all" && (
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

        {/* Currency Selector */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Display in:</span>
          <Select value={displayCurrency} onValueChange={setDisplayCurrency}>
            <SelectTrigger className="w-28">
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
        </div>
      </div>

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
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <div className="text-2xl font-bold text-amber-500">
                {currencySymbol}{Number(totalSpent).toFixed(2)}
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
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">
                {currencySymbol}{Number(avgPerReceipt).toFixed(2)}
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
              <div className="text-2xl font-bold">{categoriesCount}</div>
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
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : !categoryBreakdown?.categories.length ? (
            <div className="text-center py-12 text-muted-foreground">
              <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No category data for {periodLabel}</p>
              <p className="text-sm">Scan receipts to see breakdown</p>
            </div>
          ) : (
            <div className="space-y-3">
              {categoryBreakdown.categories.map((cat) => (
                <button
                  key={cat.category_id}
                  onClick={() => setSelectedCategoryId(cat.category_id)}
                  className="w-full text-left"
                >
                  <div className="flex items-center justify-between p-4 rounded-lg bg-accent/50 hover:bg-accent transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                        <FolderOpen className="h-5 w-5 text-amber-500" />
                      </div>
                      <div>
                        <p className="font-medium">{cat.category_name}</p>
                        <p className="text-sm text-muted-foreground">
                          {cat.item_count} item{cat.item_count !== 1 ? "s" : ""} • {Number(cat.percentage).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-amber-500">
                        {currencySymbol}{Number(cat.total_spent).toFixed(2)}
                      </p>
                    </div>
                  </div>
                  {/* Progress bar */}
                  <div className="h-1 mt-1 bg-accent rounded-full overflow-hidden">
                    <div
                      className="h-full bg-amber-500 rounded-full transition-all"
                      style={{ width: `${cat.percentage}%` }}
                    />
                  </div>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Category Items Modal */}
      <Dialog open={selectedCategoryId !== null} onOpenChange={(open) => !open && setSelectedCategoryId(null)}>
        <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedCategory?.category_name} Items</DialogTitle>
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
