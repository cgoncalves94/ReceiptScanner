"use client";

import { useState, useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
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
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { BarChart3, TrendingUp, FolderOpen, ChevronLeft, ChevronRight, Receipt, Store, Info } from "lucide-react";
import {
  useAnalyticsSummary,
  useAnalyticsTrends,
  useCategoryBreakdown,
  useCategoryItems,
  useTopStores,
  useExchangeRates,
  convertAmount,
  convertAndSum,
  convertCurrencyAmounts,
  codeToSymbol,
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

  // Currency selector - for display conversion only
  const [displayCurrency, setDisplayCurrency] = useState<string>("EUR");

  // Category detail modal
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const { data: categoryItems, isLoading: itemsLoading } = useCategoryItems(selectedCategoryId);

  // Fetch exchange rates for currency conversion
  const { data: exchangeRates } = useExchangeRates(displayCurrency);

  // Parse month for API calls
  const monthForApi = selectedMonth === "all" ? undefined : parseInt(selectedMonth);

  // Backend analytics hooks - no currency filter, backend returns all currencies
  const { data: summary, isLoading: summaryLoading } = useAnalyticsSummary(
    selectedYear,
    monthForApi
  );

  const { data: categoryBreakdown, isLoading: breakdownLoading } = useCategoryBreakdown(
    selectedYear,
    monthForApi
  );

  const { data: topStores, isLoading: topStoresLoading } = useTopStores(
    selectedYear,
    monthForApi,
    10
  );

  // Calculate date range for trends
  const { startDate, endDate } = useMemo(() => {
    if (selectedMonth === "all") {
      return {
        startDate: new Date(selectedYear, 0, 1),
        endDate: new Date(selectedYear, 11, 31, 23, 59, 59),
      };
    }
    const month = parseInt(selectedMonth);
    const lastDay = new Date(selectedYear, month + 1, 0).getDate();
    return {
      startDate: new Date(selectedYear, month, 1),
      endDate: new Date(selectedYear, month, lastDay, 23, 59, 59),
    };
  }, [selectedYear, selectedMonth]);

  const trendPeriod = selectedMonth === "all" ? "monthly" : "daily";

  const { data: trends, isLoading: trendsLoading } = useAnalyticsTrends(
    startDate,
    endDate,
    trendPeriod
  );

  const isLoading = summaryLoading || breakdownLoading || topStoresLoading || trendsLoading;

  // Available years - go back 30 years to cover historical receipts
  const availableYears = Array.from(
    { length: 30 },
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
  const filteredCategoryItems = categoryItems ?? [];

  const selectedCategory = categoryBreakdown?.categories.find(
    (c) => c.category_id === selectedCategoryId
  );
  const currencySymbol = codeToSymbol(displayCurrency);

  // Period label
  const periodLabel = selectedMonth === "all"
    ? `${selectedYear}`
    : `${MONTHS[parseInt(selectedMonth)]} ${selectedYear}`;

  // Convert backend data to display currency
  const totalSpent = convertCurrencyAmounts(summary?.totals_by_currency, displayCurrency, exchangeRates);
  const receiptCount = summary?.receipt_count ?? 0;
  const avgPerReceipt = receiptCount > 0 ? totalSpent / receiptCount : 0;
  const categoriesCount = categoryBreakdown?.categories.length ?? 0;

  // Calculate total for category breakdown (for percentage calculation)
  const categoryTotalSpent = convertCurrencyAmounts(categoryBreakdown?.totals_by_currency, displayCurrency, exchangeRates);

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
          <TooltipProvider>
            <UITooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  aria-label="Currency conversion info"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  <Info className="h-4 w-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Converted using live rates from Frankfurter API</p>
              </TooltipContent>
            </UITooltip>
          </TooltipProvider>
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
            {isLoading ? (
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
              <div className="text-2xl font-bold">{categoriesCount}</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Spending Trends Chart */}
      <Card className="bg-card/50 border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Spending Trends
          </CardTitle>
          <CardDescription>
            {selectedMonth === "all" ? "Monthly" : "Daily"} spending in {periodLabel}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-75 w-full" />
          ) : !trends?.trends.length ? (
            <div className="h-75 flex flex-col items-center justify-center text-muted-foreground">
              <TrendingUp className="h-12 w-12 mb-3 opacity-50" />
              <p>No spending data for {periodLabel}</p>
              <p className="text-sm">Scan receipts to see trends</p>
            </div>
          ) : (
            <div className="h-75">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={trends.trends.map((t) => ({
                    date: new Date(t.date).toLocaleDateString("en-US", {
                      month: "short",
                      day: selectedMonth === "all" ? undefined : "numeric",
                    }),
                    total: convertCurrencyAmounts(t.totals_by_currency, displayCurrency, exchangeRates),
                    receipts: t.receipt_count,
                  }))}
                  margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: "#f59e0b", fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fill: "#f59e0b", fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) => `${currencySymbol}${value}`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid #f59e0b",
                      borderRadius: "8px",
                    }}
                    labelStyle={{ color: "#f59e0b" }}
                    formatter={(value) => [`${currencySymbol}${Number(value).toFixed(2)}`, "Spent"]}
                  />
                  <Area
                    type="monotone"
                    dataKey="total"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorTotal)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

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
              {categoryBreakdown.categories.map((cat) => {
                const catTotal = convertCurrencyAmounts(cat.totals_by_currency, displayCurrency, exchangeRates);
                const percentage = categoryTotalSpent > 0 ? (catTotal / categoryTotalSpent) * 100 : 0;
                return (
                  <button
                    type="button"
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
                            {cat.item_count} item{cat.item_count !== 1 ? "s" : ""} • {percentage.toFixed(1)}%
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-amber-500">
                          {currencySymbol}{catTotal.toFixed(2)}
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

      {/* Top Stores */}
      <Card className="bg-card/50 border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Store className="h-5 w-5" />
            Top Stores
          </CardTitle>
          <CardDescription>Where you spend the most in {periodLabel}</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : !topStores?.stores.length ? (
            <div className="text-center py-12 text-muted-foreground">
              <Store className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No store data for {periodLabel}</p>
              <p className="text-sm">Scan receipts to see your top stores</p>
            </div>
          ) : (
            <div className="space-y-3">
              {topStores.stores.map((store, index) => {
                const storeTotal = convertCurrencyAmounts(store.totals_by_currency, displayCurrency, exchangeRates);
                const avgPerVisit = store.visit_count > 0 ? storeTotal / store.visit_count : 0;
                return (
                  <div
                    key={store.store_name}
                    className="flex items-center justify-between p-4 rounded-lg bg-accent/50"
                  >
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                        <span className="text-amber-500 font-bold">#{index + 1}</span>
                      </div>
                      <div>
                        <p className="font-medium">{store.store_name}</p>
                        <p className="text-sm text-muted-foreground">
                          {store.visit_count} visit{store.visit_count !== 1 ? "s" : ""}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-amber-500">
                        {currencySymbol}{storeTotal.toFixed(2)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        avg {currencySymbol}{avgPerVisit.toFixed(2)}/visit
                      </p>
                    </div>
                  </div>
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
                const isConverted = item.currency !== displayCurrency;
                return (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-accent/50"
                  >
                    <div>
                      <p className="font-medium">{item.name}</p>
                      <p className="text-sm text-muted-foreground">
                        Qty: {item.quantity} × {codeToSymbol(item.currency)}{Number(item.unit_price).toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge variant="secondary" className="font-semibold">
                        {currencySymbol}{convertedPrice.toFixed(2)}
                      </Badge>
                      {isConverted && (
                        <p className="text-xs text-muted-foreground mt-1">
                          ({codeToSymbol(item.currency)}{Number(item.total_price).toFixed(2)})
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
