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
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Receipt, TrendingUp, ShoppingCart, CalendarDays, ChevronLeft, ChevronRight, Info, FolderOpen, BarChart3 } from "lucide-react";
import Link from "next/link";
import {
  useReceipts,
  useExchangeRates,
  convertAndSum,
  convertCurrencyAmounts,
  codeToSymbol,
  SUPPORTED_CURRENCIES,
  useAnalyticsTrends,
  useCategoryBreakdown,
} from "@/hooks";
import { formatDistanceToNow } from "@/lib/format";
import { MONTHS } from "@/lib/constants";

export default function Dashboard() {
  const { data: receipts, isLoading } = useReceipts();

  // Currency selector for display conversion
  const [displayCurrency, setDisplayCurrency] = useState<string>("EUR");
  const { data: exchangeRates } = useExchangeRates(displayCurrency);
  const currencySymbol = codeToSymbol(displayCurrency);

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

  // Stats for selected month (converted to display currency)
  const totalSpent = convertAndSum(
    monthReceipts.map((r) => ({ amount: Number(r.total_amount), currency: r.currency })),
    displayCurrency,
    exchangeRates
  );
  const receiptCount = monthReceipts.length;
  const avgPerReceipt = receiptCount > 0 ? totalSpent / receiptCount : 0;
  const recentReceipts = monthReceipts.slice(0, 5);

  // Calculate date range for trends based on selected period
  const { trendStart, trendEnd } = useMemo(() => {
    if (selectedMonth === "all") {
      return {
        trendStart: new Date(selectedYear, 0, 1),
        trendEnd: new Date(selectedYear, 11, 31),
      };
    }
    const monthNum = parseInt(selectedMonth);
    const lastDay = new Date(selectedYear, monthNum + 1, 0).getDate();
    return {
      trendStart: new Date(selectedYear, monthNum, 1),
      trendEnd: new Date(selectedYear, monthNum, lastDay),
    };
  }, [selectedMonth, selectedYear]);

  // Fetch analytics data
  const isMonthlyView = selectedMonth === "all";
  const { data: trends, isLoading: trendsLoading } = useAnalyticsTrends(
    trendStart,
    trendEnd,
    isMonthlyView ? "monthly" : "daily"
  );

  const monthParam = selectedMonth === "all" ? undefined : parseInt(selectedMonth);
  const { data: categoryBreakdown, isLoading: categoriesLoading } = useCategoryBreakdown(
    selectedYear,
    monthParam
  );

  // Calculate category total for percentage calculations
  const categoryTotalSpent = useMemo(() => {
    if (!categoryBreakdown?.categories) return 0;
    return categoryBreakdown.categories.reduce((acc, cat) => {
      return acc + convertCurrencyAmounts(cat.totals_by_currency, displayCurrency, exchangeRates);
    }, 0);
  }, [categoryBreakdown, displayCurrency, exchangeRates]);

  // Get top 4 categories for preview (pre-compute totals to avoid redundant conversions)
  const topCategories = useMemo(() => {
    if (!categoryBreakdown?.categories) return [];
    return [...categoryBreakdown.categories]
      .map((cat) => ({
        ...cat,
        total: convertCurrencyAmounts(cat.totals_by_currency, displayCurrency, exchangeRates),
      }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 4);
  }, [categoryBreakdown, displayCurrency, exchangeRates]);

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
                {currencySymbol}{totalSpent.toFixed(2)}
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
                  ? `${currencySymbol}${avgPerReceipt.toFixed(2)}`
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
                      {codeToSymbol(receipt.currency)}{Number(receipt.total_amount).toFixed(2)}
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

      {/* Analytics Preview Section */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Spending Trends Mini Chart */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-amber-500" />
                  Spending Trends
                </CardTitle>
                <CardDescription>
                  {isMonthlyView ? "Monthly" : "Daily"} overview
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href={`/analytics?year=${selectedYear}${selectedMonth !== "all" ? `&month=${selectedMonth}` : ""}`}>View Details</Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {trendsLoading ? (
              <Skeleton className="h-50 w-full" />
            ) : !trends?.trends.length ? (
              <div className="h-50 flex flex-col items-center justify-center text-muted-foreground">
                <TrendingUp className="h-10 w-10 mb-3 opacity-50" />
                <p className="text-sm">No trend data available</p>
              </div>
            ) : (
              <div className="h-50">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={trends.trends.map((t) => ({
                      period_label: new Date(t.date).toLocaleDateString("en-US", {
                        month: "short",
                        day: isMonthlyView ? undefined : "numeric",
                      }),
                      total_amount: convertCurrencyAmounts(t.totals_by_currency, displayCurrency, exchangeRates),
                    }))}
                    margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                  >
                    <defs>
                      <linearGradient id="colorTotalDashboard" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                    <XAxis
                      dataKey="period_label"
                      tick={{ fill: "#f59e0b", fontSize: 11 }}
                      tickLine={false}
                      axisLine={false}
                      tickMargin={8}
                    />
                    <YAxis
                      tick={{ fill: "#f59e0b", fontSize: 11 }}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(value) => `${currencySymbol}${value.toFixed(0)}`}
                      width={50}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid #f59e0b",
                        borderRadius: "8px",
                      }}
                      labelStyle={{ color: "#f59e0b" }}
                      formatter={(value: number | undefined) => [
                        `${currencySymbol}${(value ?? 0).toFixed(2)}`,
                        "Total Spent",
                      ]}
                    />
                    <Area
                      type="monotone"
                      dataKey="total_amount"
                      stroke="#f59e0b"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorTotalDashboard)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Categories Preview */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-amber-500" />
                  Top Categories
                </CardTitle>
                <CardDescription>
                  {selectedMonth === "all" ? selectedYear : `${MONTHS[parseInt(selectedMonth)]} ${selectedYear}`}
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href={`/analytics?year=${selectedYear}${selectedMonth !== "all" ? `&month=${selectedMonth}` : ""}`}>View All</Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {categoriesLoading ? (
              <div className="space-y-3">
                {[...Array(4)].map((_, i) => (
                  <Skeleton key={i} className="h-14 w-full" />
                ))}
              </div>
            ) : topCategories.length === 0 ? (
              <div className="h-50 flex flex-col items-center justify-center text-muted-foreground">
                <FolderOpen className="h-10 w-10 mb-3 opacity-50" />
                <p className="text-sm">No category data available</p>
              </div>
            ) : (
              <div className="space-y-3">
                {topCategories.map((cat) => {
                  const catTotal = cat.total;
                  const percentage = categoryTotalSpent > 0 ? (catTotal / categoryTotalSpent) * 100 : 0;
                  return (
                    <div key={cat.category_id}>
                      <div className="flex items-center justify-between p-3 rounded-lg bg-accent/50">
                        <div className="flex items-center gap-3">
                          <div className="h-9 w-9 rounded-lg bg-amber-500/10 flex items-center justify-center">
                            <FolderOpen className="h-4 w-4 text-amber-500" />
                          </div>
                          <div>
                            <p className="font-medium text-sm">{cat.category_name}</p>
                            <p className="text-xs text-muted-foreground">
                              {cat.item_count} item{cat.item_count !== 1 ? "s" : ""} • {percentage.toFixed(1)}%
                            </p>
                          </div>
                        </div>
                        <p className="font-semibold text-amber-500">
                          {currencySymbol}{catTotal.toFixed(2)}
                        </p>
                      </div>
                      {/* Progress bar */}
                      <div className="h-1 mt-1 bg-accent rounded-full overflow-hidden">
                        <div
                          className="h-full bg-amber-500 rounded-full transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
