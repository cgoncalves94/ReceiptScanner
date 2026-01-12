"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

const ANALYTICS_KEY = ["analytics"];

export function useAnalyticsSummary(
  year: number,
  month: number | undefined,
  currency: string
) {
  return useQuery({
    queryKey: [...ANALYTICS_KEY, "summary", year, month, currency],
    queryFn: () => api.getAnalyticsSummary(year, month, currency),
  });
}

export function useAnalyticsTrends(
  start: Date,
  end: Date,
  period: "daily" | "weekly" | "monthly",
  currency: string
) {
  return useQuery({
    queryKey: [...ANALYTICS_KEY, "trends", start.toISOString(), end.toISOString(), period, currency],
    queryFn: () => api.getAnalyticsTrends(start, end, period, currency),
  });
}

export function useTopStores(
  year: number,
  month: number | undefined,
  limit: number,
  currency: string
) {
  return useQuery({
    queryKey: [...ANALYTICS_KEY, "top-stores", year, month, limit, currency],
    queryFn: () => api.getTopStores(year, month, limit, currency),
  });
}

export function useCategoryBreakdown(
  year: number,
  month: number | undefined,
  currency: string
) {
  return useQuery({
    queryKey: [...ANALYTICS_KEY, "category-breakdown", year, month, currency],
    queryFn: () => api.getCategoryBreakdown(year, month, currency),
  });
}
