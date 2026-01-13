"use client";

import { useState, useMemo } from "react";
import { BarChart3, TrendingUp, FolderOpen, Receipt } from "lucide-react";
import {
  useAnalyticsSummary,
  useAnalyticsTrends,
  useCategoryBreakdown,
  useCategoryItems,
  useTopStores,
  useReceipts,
  useExchangeRates,
  convertCurrencyAmounts,
  codeToSymbol,
} from "@/hooks";
import {
  DateNavigator,
  CurrencySelector,
  StatCard,
  SpendingTrendsChart,
  CategoryBreakdownList,
  TopStoresList,
  CategoryItemsModal,
} from "@/components/analytics";
import { MONTHS } from "@/lib/constants";

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

  // Fetch exchange rates for currency conversion
  const { data: exchangeRates } = useExchangeRates(displayCurrency);

  // Parse month for API calls
  const monthForApi = selectedMonth === "all" ? undefined : parseInt(selectedMonth);

  // Fetch category items and receipts for client-side period filtering
  const { data: categoryItems, isLoading: itemsLoading } = useCategoryItems(selectedCategoryId);
  const { data: receipts } = useReceipts();

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

  // Handler for "Today" button
  const handleToday = () => {
    setSelectedMonth(currentMonth.toString());
    setSelectedYear(currentYear);
  };

  // Filter category items by selected period using receipt purchase dates
  const filteredCategoryItems = (categoryItems ?? []).filter((item) => {
    const receipt = receipts?.find((r) => r.id === item.receipt_id);
    if (!receipt) return false;
    const date = new Date(receipt.purchase_date);
    if (date.getFullYear() !== selectedYear) return false;
    if (monthForApi !== undefined && date.getMonth() !== monthForApi) return false;
    return true;
  });

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
        <DateNavigator
          selectedMonth={selectedMonth}
          selectedYear={selectedYear}
          onMonthChange={setSelectedMonth}
          onYearChange={setSelectedYear}
          onPrevious={goToPrevMonth}
          onNext={goToNextMonth}
          availableYears={availableYears}
          showTodayButton={!isCurrentPeriod && selectedMonth !== "all"}
          onToday={handleToday}
        />
        <CurrencySelector
          value={displayCurrency}
          onChange={setDisplayCurrency}
        />
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Spent"
          value={`${currencySymbol}${totalSpent.toFixed(2)}`}
          icon={<TrendingUp className="h-4 w-4 text-amber-500" />}
          isLoading={isLoading}
          iconClassName="h-4 w-4 text-amber-500"
          valueClassName="text-2xl font-bold text-amber-500"
        />

        <StatCard
          title="Receipts"
          value={receiptCount}
          icon={<Receipt className="h-4 w-4 text-muted-foreground" />}
          isLoading={isLoading}
        />

        <StatCard
          title="Avg per Receipt"
          value={`${currencySymbol}${avgPerReceipt.toFixed(2)}`}
          icon={<BarChart3 className="h-4 w-4 text-muted-foreground" />}
          isLoading={isLoading}
        />

        <StatCard
          title="Categories Used"
          value={categoriesCount}
          icon={<FolderOpen className="h-4 w-4 text-muted-foreground" />}
          isLoading={isLoading}
        />
      </div>

      {/* Spending Trends Chart */}
      <SpendingTrendsChart
        trends={trends ? {
          trends: trends.trends.map((t) => ({
            period_label: new Date(t.date).toLocaleDateString("en-US", {
              month: "short",
              day: selectedMonth === "all" ? undefined : "numeric",
            }),
            totals_by_currency: t.totals_by_currency,
          })),
        } : undefined}
        isLoading={isLoading}
        displayCurrency={displayCurrency}
        currencySymbol={currencySymbol}
        exchangeRates={exchangeRates}
        isMonthlyView={selectedMonth === "all"}
      />

      {/* Category Breakdown */}
      <CategoryBreakdownList
        categories={categoryBreakdown?.categories ?? []}
        isLoading={isLoading}
        displayCurrency={displayCurrency}
        exchangeRates={exchangeRates}
        periodLabel={periodLabel}
        categoryTotalSpent={categoryTotalSpent}
        onCategoryClick={setSelectedCategoryId}
      />

      {/* Top Stores */}
      <TopStoresList
        stores={topStores?.stores}
        isLoading={isLoading}
        displayCurrency={displayCurrency}
        exchangeRates={exchangeRates}
        periodLabel={periodLabel}
      />

      {/* Category Items Modal */}
      <CategoryItemsModal
        open={selectedCategoryId !== null}
        onOpenChange={(open) => !open && setSelectedCategoryId(null)}
        categoryName={selectedCategory?.category_name}
        periodLabel={periodLabel}
        items={filteredCategoryItems.map((item) => ({
          id: item.id,
          name: item.name,
          quantity: item.quantity,
          unit_price: item.unit_price.toString(),
          total_price: item.total_price.toString(),
          currency: item.currency,
        }))}
        isLoading={itemsLoading}
        displayCurrency={displayCurrency}
        currencySymbol={currencySymbol}
        exchangeRates={exchangeRates}
      />
    </div>
  );
}
