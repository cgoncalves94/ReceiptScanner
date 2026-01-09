"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Receipt, Check, ArrowRight } from "lucide-react";
import Link from "next/link";
import type { Receipt as ReceiptType } from "@/types";
import { formatCurrency, formatDate } from "@/lib/format";
import { useCategories } from "@/hooks";

interface ScanResultProps {
  receipt: ReceiptType;
  onScanAnother: () => void;
}

export function ScanResult({ receipt, onScanAnother }: ScanResultProps) {
  const { data: categories } = useCategories();

  // Create a map for quick category lookup
  const categoryMap = new Map(
    categories?.map((c) => [c.id, c.name]) ?? []
  );

  return (
    <div className="space-y-6">
      {/* Success Banner */}
      <div className="flex items-center gap-3 p-4 rounded-lg bg-green-500/10 border border-green-500/20">
        <div className="h-10 w-10 rounded-full bg-green-500/20 flex items-center justify-center">
          <Check className="h-5 w-5 text-green-500" />
        </div>
        <div>
          <p className="font-medium text-green-500">Receipt scanned successfully!</p>
          <p className="text-sm text-muted-foreground">
            {receipt.items.length} items detected
          </p>
        </div>
      </div>

      {/* Receipt Summary */}
      <Card className="bg-card/50 border-border/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <Receipt className="h-5 w-5 text-amber-500" />
              </div>
              <div>
                <CardTitle>{receipt.store_name}</CardTitle>
                <p className="text-sm text-muted-foreground">
                  {formatDate(receipt.purchase_date)}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold">
                {formatCurrency(Number(receipt.total_amount), receipt.currency)}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Separator className="mb-4" />

          {/* Items */}
          <div className="space-y-3">
            {receipt.items.map((item) => {
              const categoryName = item.category_id
                ? categoryMap.get(item.category_id)
                : null;

              return (
                <div
                  key={item.id}
                  className="flex items-center justify-between py-2"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-muted-foreground">{item.quantity}x</span>
                    <span>{item.name}</span>
                    {categoryName && (
                      <Badge variant="secondary" className="text-xs">
                        {categoryName}
                      </Badge>
                    )}
                  </div>
                  <span className="font-medium">
                    {formatCurrency(Number(item.total_price), item.currency)}
                  </span>
                </div>
              );
            })}
          </div>

          <Separator className="my-4" />

          {/* Total */}
          <div className="flex items-center justify-between text-lg font-semibold">
            <span>Total</span>
            <span>{formatCurrency(Number(receipt.total_amount), receipt.currency)}</span>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-3">
        <Button variant="outline" onClick={onScanAnother} className="flex-1">
          Scan Another
        </Button>
        <Button className="flex-1 bg-amber-500 hover:bg-amber-600 text-black" asChild>
          <Link href={`/receipts/${receipt.id}`}>
            View Details
            <ArrowRight className="h-4 w-4 ml-2" />
          </Link>
        </Button>
      </div>
    </div>
  );
}
