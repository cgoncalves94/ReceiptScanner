import { BarChart3, FolderOpen } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { convertCurrencyAmounts, codeToSymbol } from "@/hooks";
import type { ExchangeRates } from "@/hooks";
import type { CurrencyAmount } from "@/types";

interface CategoryBreakdownItem {
  category_id: number;
  category_name: string;
  item_count: number;
  totals_by_currency: CurrencyAmount[];
}

interface CategoryBreakdownListProps {
  categories: CategoryBreakdownItem[];
  isLoading: boolean;
  displayCurrency: string;
  exchangeRates: ExchangeRates | undefined;
  periodLabel: string;
  categoryTotalSpent: number;
  onCategoryClick: (categoryId: number) => void;
}

export function CategoryBreakdownList({
  categories,
  isLoading,
  displayCurrency,
  exchangeRates,
  periodLabel,
  categoryTotalSpent,
  onCategoryClick,
}: CategoryBreakdownListProps) {
  const currencySymbol = codeToSymbol(displayCurrency);

  return (
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
        ) : !categories.length ? (
          <div className="text-center py-12 text-muted-foreground">
            <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No category data for {periodLabel}</p>
            <p className="text-sm">Scan receipts to see breakdown</p>
          </div>
        ) : (
          <div className="space-y-3">
            {categories.map((cat) => {
              const catTotal = convertCurrencyAmounts(cat.totals_by_currency, displayCurrency, exchangeRates);
              const percentage = categoryTotalSpent > 0 ? (catTotal / categoryTotalSpent) * 100 : 0;
              return (
                <button
                  type="button"
                  key={cat.category_id}
                  onClick={() => onCategoryClick(cat.category_id)}
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
  );
}
