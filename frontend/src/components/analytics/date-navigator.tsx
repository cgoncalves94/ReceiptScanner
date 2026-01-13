"use client";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { MONTHS } from "@/lib/constants";

interface DateNavigatorProps {
  selectedMonth: string;
  selectedYear: number;
  onMonthChange: (month: string) => void;
  onYearChange: (year: number) => void;
  onPrevious: () => void;
  onNext: () => void;
  availableYears: number[];
  showTodayButton?: boolean;
  onToday?: () => void;
}

export function DateNavigator({
  selectedMonth,
  selectedYear,
  onMonthChange,
  onYearChange,
  onPrevious,
  onNext,
  availableYears,
  showTodayButton = false,
  onToday,
}: DateNavigatorProps) {
  return (
    <div className="flex items-center gap-2">
      <Button variant="outline" size="icon" onClick={onPrevious}>
        <ChevronLeft className="h-4 w-4" />
      </Button>
      <div className="flex items-center gap-2">
        <Select value={selectedMonth} onValueChange={onMonthChange}>
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
        <Select value={selectedYear.toString()} onValueChange={(v) => onYearChange(parseInt(v))}>
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
      <Button variant="outline" size="icon" onClick={onNext}>
        <ChevronRight className="h-4 w-4" />
      </Button>
      {showTodayButton && onToday && (
        <Button variant="ghost" size="sm" onClick={onToday}>
          Today
        </Button>
      )}
    </div>
  );
}
