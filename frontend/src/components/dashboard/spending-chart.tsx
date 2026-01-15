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

interface SpendingChartProps {
  data: Array<{
    period_label: string;
    total_amount: number;
  }>;
  currencySymbol: string;
}

export function SpendingChart({ data, currencySymbol }: SpendingChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
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
  );
}
