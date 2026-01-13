"use client";

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
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp } from "lucide-react";
import { convertCurrencyAmounts } from "@/hooks";
import type { ExchangeRates } from "@/hooks";

interface TrendData {
  period_label: string;
  totals_by_currency: Array<{ currency: string; amount: string }>;
}

interface SpendingTrendsChartProps {
  trends?: {
    trends: TrendData[];
  };
  isLoading?: boolean;
  displayCurrency: string;
  currencySymbol: string;
  exchangeRates?: ExchangeRates;
  isMonthlyView: boolean;
}

export function SpendingTrendsChart({
  trends,
  isLoading = false,
  displayCurrency,
  currencySymbol,
  exchangeRates,
  isMonthlyView,
}: SpendingTrendsChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-blue-500" />
          Spending Trends
        </CardTitle>
        <CardDescription>
          {isMonthlyView ? "Monthly" : "Daily"} spending over the selected period
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-[300px] w-full" />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart
              data={trends?.trends.map((t) => ({
                ...t,
                total_amount: convertCurrencyAmounts(t.totals_by_currency, displayCurrency, exchangeRates),
              })) ?? []}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="period_label"
                tick={{ fontSize: 12 }}
                tickMargin={10}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `${currencySymbol}${value.toFixed(0)}`}
              />
              <Tooltip
                formatter={(value: number | undefined) => [
                  `${currencySymbol}${(value ?? 0).toFixed(2)}`,
                  "Total Spent",
                ]}
              />
              <Area
                type="monotone"
                dataKey="total_amount"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
