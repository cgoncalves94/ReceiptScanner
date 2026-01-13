import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { convertAmount, convertAndSum, codeToSymbol } from "@/hooks";
import type { ExchangeRates } from "@/hooks";

interface CategoryItemsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  categoryName?: string;
  periodLabel: string;
  items: Array<{
    id: number;
    name: string;
    quantity: number;
    unit_price: string;
    total_price: string;
    currency: string;
  }>;
  isLoading: boolean;
  displayCurrency: string;
  currencySymbol: string;
  exchangeRates?: ExchangeRates;
}

export function CategoryItemsModal({
  open,
  onOpenChange,
  categoryName,
  periodLabel,
  items,
  isLoading,
  displayCurrency,
  currencySymbol,
  exchangeRates,
}: CategoryItemsModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{categoryName} Items</DialogTitle>
          <DialogDescription>
            {periodLabel} • {items.length} item{items.length !== 1 ? "s" : ""}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2 pt-4">
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : items.length === 0 ? (
            <p className="text-center text-muted-foreground py-4">
              No items in this category for {periodLabel}
            </p>
          ) : (
            items.map((item) => {
              const convertedPrice = convertAmount(
                Number(item.total_price),
                item.currency,
                displayCurrency,
                exchangeRates
              );
              const isConverted = item.currency !== displayCurrency;
              return (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-accent/50"
                >
                  <div>
                    <p className="font-medium">{item.name}</p>
                    <p className="text-sm text-muted-foreground">
                      Qty: {item.quantity} × {codeToSymbol(item.currency)}{Number(item.unit_price).toFixed(2)}
                    </p>
                  </div>
                  <div className="text-right">
                    <Badge variant="secondary" className="font-semibold">
                      {currencySymbol}{convertedPrice.toFixed(2)}
                    </Badge>
                    {isConverted && (
                      <p className="text-xs text-muted-foreground mt-1">
                        ({codeToSymbol(item.currency)}{Number(item.total_price).toFixed(2)})
                      </p>
                    )}
                  </div>
                </div>
              );
            })
          )}
          {items.length > 0 && (
            <div className="pt-4 border-t flex justify-between items-center">
              <span className="font-medium">Total</span>
              <span className="font-bold text-amber-500">
                {currencySymbol}
                {convertAndSum(
                  items.map((i) => ({
                    amount: Number(i.total_price),
                    currency: i.currency,
                  })),
                  displayCurrency,
                  exchangeRates
                ).toFixed(2)}
              </span>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
