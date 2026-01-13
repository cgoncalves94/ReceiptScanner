import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Store } from "lucide-react";
import { convertCurrencyAmounts, codeToSymbol } from "@/hooks";
import type { StoreVisit } from "@/types";

interface TopStoresListProps {
  stores?: StoreVisit[];
  isLoading: boolean;
  displayCurrency: string;
  exchangeRates?: Record<string, number>;
  periodLabel: string;
}

export function TopStoresList({
  stores,
  isLoading,
  displayCurrency,
  exchangeRates,
  periodLabel,
}: TopStoresListProps) {
  const currencySymbol = codeToSymbol(displayCurrency);

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Store className="h-5 w-5" />
          Top Stores
        </CardTitle>
        <CardDescription>Where you spend the most in {periodLabel}</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        ) : !stores?.length ? (
          <div className="text-center py-12 text-muted-foreground">
            <Store className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No store data for {periodLabel}</p>
            <p className="text-sm">Scan receipts to see your top stores</p>
          </div>
        ) : (
          <div className="space-y-3">
            {stores.map((store, index) => {
              const storeTotal = convertCurrencyAmounts(store.totals_by_currency, displayCurrency, exchangeRates);
              const avgPerVisit = store.visit_count > 0 ? storeTotal / store.visit_count : 0;
              return (
                <div
                  key={store.store_name}
                  className="flex items-center justify-between p-4 rounded-lg bg-accent/50"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                      <span className="text-amber-500 font-bold">#{index + 1}</span>
                    </div>
                    <div>
                      <p className="font-medium">{store.store_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {store.visit_count} visit{store.visit_count !== 1 ? "s" : ""}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-amber-500">
                      {currencySymbol}{storeTotal.toFixed(2)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      avg {currencySymbol}{avgPerVisit.toFixed(2)}/visit
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
