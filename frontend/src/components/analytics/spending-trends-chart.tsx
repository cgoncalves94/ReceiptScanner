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
    <Card className="bg-card/50 border-border/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-amber-500" />
          Spending Trends
        </CardTitle>
        <CardDescription>
          {isMonthlyView ? "Monthly" : "Daily"} spending over the selected period
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-[300px] w-full" />
        ) : !trends?.trends.length ? (
          <div className="h-[300px] flex flex-col items-center justify-center text-muted-foreground">
            <TrendingUp className="h-12 w-12 mb-3 opacity-50" />
            <p>No spending data for the selected period</p>
            <p className="text-sm">Scan receipts to see trends</p>
          </div>
        ) : (
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={trends.trends.map((t) => ({
                  ...t,
                  total_amount: convertCurrencyAmounts(t.totals_by_currency, displayCurrency, exchangeRates),
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
                  dataKey="period_label"
                  tick={{ fill: "#f59e0b", fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  tickMargin={10}
                />
                <YAxis
                  tick={{ fill: "#f59e0b", fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `${currencySymbol}${value.toFixed(0)}`}
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
                  fill="url(#colorTotal)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
