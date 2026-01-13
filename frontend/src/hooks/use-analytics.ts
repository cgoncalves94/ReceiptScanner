"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

const ANALYTICS_KEY = ["analytics"];

export function useAnalyticsSummary(
  year: number,
  month: number | undefined
) {
  return useQuery({
    queryKey: [...ANALYTICS_KEY, "summary", year, month],
    queryFn: () => api.getAnalyticsSummary(year, month),
  });
}

export function useAnalyticsTrends(
  start: Date,
  end: Date,
  period: "daily" | "weekly" | "monthly"
) {
  return useQuery({
    queryKey: [...ANALYTICS_KEY, "trends", start.toISOString(), end.toISOString(), period],
    queryFn: () => api.getAnalyticsTrends(start, end, period),
  });
}

export function useTopStores(
  year: number,
  month: number | undefined,
  limit: number
) {
  return useQuery({
    queryKey: [...ANALYTICS_KEY, "top-stores", year, month, limit],
    queryFn: () => api.getTopStores(year, month, limit),
  });
}

export function useCategoryBreakdown(
  year: number,
  month: number | undefined
) {
  return useQuery({
    queryKey: [...ANALYTICS_KEY, "category-breakdown", year, month],
    queryFn: () => api.getCategoryBreakdown(year, month),
  });
}
