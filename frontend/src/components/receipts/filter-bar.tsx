"use client";

import { useEffect, useState, useCallback } from "react";
import { Search, X, Filter, ChevronDown, ChevronUp } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCategories } from "@/hooks";
import type { ReceiptFilters } from "@/types";

interface FilterBarProps {
  filters: ReceiptFilters;
  onFiltersChange: (filters: ReceiptFilters) => void;
  stores?: string[]; // Unique stores extracted from receipts
}

// Debounce helper
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export function FilterBar({ filters, onFiltersChange, stores = [] }: FilterBarProps) {
  const { data: categories } = useCategories();
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Local state for search input (for debouncing)
  const [searchInput, setSearchInput] = useState(filters.search || "");
  const debouncedSearch = useDebounce(searchInput, 300);

  // Update filters when debounced search changes
  useEffect(() => {
    if (debouncedSearch !== filters.search) {
      onFiltersChange({
        ...filters,
        search: debouncedSearch || undefined,
      });
    }
  }, [debouncedSearch]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleStoreChange = useCallback(
    (value: string) => {
      onFiltersChange({
        ...filters,
        store: value === "all" ? undefined : value,
      });
    },
    [filters, onFiltersChange]
  );

  const handleCategoryChange = useCallback(
    (value: string) => {
      const categoryIds =
        value === "all" ? undefined : [parseInt(value)];
      onFiltersChange({
        ...filters,
        category_ids: categoryIds,
      });
    },
    [filters, onFiltersChange]
  );

  const handleDateChange = useCallback(
    (field: "after" | "before", value: string) => {
      onFiltersChange({
        ...filters,
        [field]: value || undefined,
      });
    },
    [filters, onFiltersChange]
  );

  const handleAmountChange = useCallback(
    (field: "min_amount" | "max_amount", value: string) => {
      const numValue = value ? parseFloat(value) : undefined;
      onFiltersChange({
        ...filters,
        [field]: numValue,
      });
    },
    [filters, onFiltersChange]
  );

  const clearFilters = useCallback(() => {
    setSearchInput("");
    onFiltersChange({});
  }, [onFiltersChange]);

  // Count active filters
  const activeFilterCount = [
    filters.search,
    filters.store,
    filters.after,
    filters.before,
    filters.category_ids?.length,
    filters.min_amount,
    filters.max_amount,
  ].filter(Boolean).length;

  const hasFilters = activeFilterCount > 0;

  return (
    <div className="space-y-4">
      {/* Main filter row */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search input */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search store name..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Store filter */}
        <Select
          value={filters.store || "all"}
          onValueChange={handleStoreChange}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Stores" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Stores</SelectItem>
            {stores.map((store) => (
              <SelectItem key={store} value={store}>
                {store}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Category filter */}
        <Select
          value={filters.category_ids?.[0]?.toString() || "all"}
          onValueChange={handleCategoryChange}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories?.map((category) => (
              <SelectItem key={category.id} value={category.id.toString()}>
                {category.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Advanced toggle & Clear */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={showAdvanced ? "bg-accent" : ""}
          >
            <Filter className="h-4 w-4" />
            {showAdvanced ? (
              <ChevronUp className="h-3 w-3 ml-1" />
            ) : (
              <ChevronDown className="h-3 w-3 ml-1" />
            )}
          </Button>

          {hasFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X className="h-4 w-4 mr-1" />
              Clear
              {activeFilterCount > 0 && (
                <Badge variant="secondary" className="ml-1">
                  {activeFilterCount}
                </Badge>
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Advanced filters */}
      {showAdvanced && (
        <div className="flex flex-wrap gap-4 p-4 bg-muted/50 rounded-lg">
          {/* Date range */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground whitespace-nowrap">
              From:
            </label>
            <Input
              type="date"
              value={filters.after?.split("T")[0] || ""}
              onChange={(e) => handleDateChange("after", e.target.value)}
              className="w-[150px]"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground whitespace-nowrap">
              To:
            </label>
            <Input
              type="date"
              value={filters.before?.split("T")[0] || ""}
              onChange={(e) => handleDateChange("before", e.target.value)}
              className="w-[150px]"
            />
          </div>

          {/* Amount range */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground whitespace-nowrap">
              Min Amount:
            </label>
            <Input
              type="number"
              placeholder="0"
              min="0"
              step="0.01"
              value={filters.min_amount ?? ""}
              onChange={(e) => handleAmountChange("min_amount", e.target.value)}
              className="w-[100px]"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground whitespace-nowrap">
              Max Amount:
            </label>
            <Input
              type="number"
              placeholder="999"
              min="0"
              step="0.01"
              value={filters.max_amount ?? ""}
              onChange={(e) => handleAmountChange("max_amount", e.target.value)}
              className="w-[100px]"
            />
          </div>
        </div>
      )}
    </div>
  );
}
