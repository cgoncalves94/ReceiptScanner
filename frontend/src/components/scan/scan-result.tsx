"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { Receipt, Check, ArrowRight, Loader2, Trash2 } from "lucide-react";
import Link from "next/link";
import type {
  Receipt as ReceiptType,
  ReceiptItemCreate,
  ReceiptReconcileSuggestion,
  ScanRemovedItem,
} from "@/types";
import { formatCurrency, formatDate } from "@/lib/format";
import { toast } from "sonner";
import {
  useCategories,
  useCreateReceiptItem,
  useDeleteReceiptItem,
  useUpdateReceipt,
  useReconcileReceipt,
} from "@/hooks";

interface ScanResultProps {
  receipt: ReceiptType;
  onScanAnother: () => void;
}

export function ScanResult({ receipt, onScanAnother }: ScanResultProps) {
  const { data: categories } = useCategories();
  const updateReceiptMutation = useUpdateReceipt();
  const createItemMutation = useCreateReceiptItem();
  const deleteItemMutation = useDeleteReceiptItem();
  const reconcileMutation = useReconcileReceipt();
  const [currentReceipt, setCurrentReceipt] = useState(receipt);
  const [reconcileDialogOpen, setReconcileDialogOpen] = useState(false);
  const [reconcileSuggestion, setReconcileSuggestion] =
    useState<ReceiptReconcileSuggestion | null>(null);
  const [aiAnalyzedFingerprint, setAiAnalyzedFingerprint] = useState<
    string | null
  >(null);
  const [isReconciling, setIsReconciling] = useState(false);
  const [removingItemId, setRemovingItemId] = useState<number | null>(null);
  const [isRestoringRemoved, setIsRestoringRemoved] = useState(false);
  const [removedDetailsOpen, setRemovedDetailsOpen] = useState(false);
  const [autoRemovedItems, setAutoRemovedItems] = useState<ScanRemovedItem[]>(
    receipt.scan_removed_items ?? []
  );

  // Create a map for quick category lookup
  const categoryMap = useMemo(
    () => new Map(categories?.map((c) => [c.id, c.name]) ?? []),
    [categories]
  );

  const itemById = useMemo(
    () => new Map(currentReceipt.items.map((item) => [item.id, item])),
    [currentReceipt]
  );

  const receiptStateFingerprint = useMemo(() => {
    const itemsSignature = [...currentReceipt.items]
      .sort((a, b) => a.id - b.id)
      .map(
        (item) =>
          `${item.id}:${item.quantity}:${Number(item.unit_price)}:${Number(item.total_price)}`
      )
      .join("|");
    return `${currentReceipt.id}:${Number(currentReceipt.total_amount)}:${itemsSignature}`;
  }, [currentReceipt]);

  const isAiAlreadyAnalyzed = aiAnalyzedFingerprint === receiptStateFingerprint;
  useEffect(() => {
    setCurrentReceipt(receipt);
    setAutoRemovedItems(receipt.scan_removed_items ?? []);
    if (receipt.id !== currentReceipt.id) {
      setAiAnalyzedFingerprint(null);
      setReconcileSuggestion(null);
    }
  }, [receipt, currentReceipt.id]);

  useEffect(() => {
    if (aiAnalyzedFingerprint && aiAnalyzedFingerprint !== receiptStateFingerprint) {
      setReconcileSuggestion(null);
    }
  }, [aiAnalyzedFingerprint, receiptStateFingerprint]);

  const roundCurrency = (value: number) =>
    Math.round((value + Number.EPSILON) * 100) / 100;

  const { receiptTotal, itemsTotal, delta, hasMismatch } = useMemo(() => {
    const receiptValue = roundCurrency(Number(currentReceipt.total_amount));
    const itemsValue = roundCurrency(
      currentReceipt.items.reduce((sum, item) => sum + Number(item.total_price), 0)
    );
    const difference = roundCurrency(itemsValue - receiptValue);
    return {
      receiptTotal: receiptValue,
      itemsTotal: itemsValue,
      delta: difference,
      hasMismatch: Math.abs(difference) > 0.05,
    };
  }, [currentReceipt]);


  const handleRunAiReconcile = async () => {
    if (isAiAlreadyAnalyzed) {
      return;
    }
    try {
      const suggestion = await reconcileMutation.mutateAsync(currentReceipt.id);
      setReconcileSuggestion(suggestion);
      setAiAnalyzedFingerprint(receiptStateFingerprint);
      if (suggestion.adjustments.length === 0) {
        toast.info("AI did not find any safe adjustments");
      }
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to run AI reconcile"
      );
      reconcileMutation.reset();
    }
  };

  const handleApplyAiSuggestions = async () => {
    if (!reconcileSuggestion || reconcileSuggestion.adjustments.length === 0) {
      toast.error("No AI adjustments to apply");
      return;
    }

    setIsReconciling(true);
    try {
      let updatedReceipt = currentReceipt;
      for (const adjustment of reconcileSuggestion.adjustments) {
        updatedReceipt = await deleteItemMutation.mutateAsync({
          receiptId: currentReceipt.id,
          itemId: adjustment.item_id,
        });
      }
      setCurrentReceipt(updatedReceipt);
      toast.success("Applied AI adjustments");
      setReconcileDialogOpen(false);
      setReconcileSuggestion(null);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to apply AI adjustments"
      );
      deleteItemMutation.reset();
    } finally {
      setIsReconciling(false);
    }
  };

  const handleRemoveItem = async (itemId: number) => {
    setRemovingItemId(itemId);
    try {
      const updatedReceipt = await deleteItemMutation.mutateAsync({
        receiptId: currentReceipt.id,
        itemId,
      });
      setCurrentReceipt(updatedReceipt);
      toast.success("Item removed");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to remove item"
      );
      deleteItemMutation.reset();
    } finally {
      setRemovingItemId(null);
    }
  };

  const handleSetReceiptTotal = async () => {
    try {
      const updatedReceipt = await updateReceiptMutation.mutateAsync({
        id: currentReceipt.id,
        data: { total_amount: itemsTotal },
      });
      setCurrentReceipt(updatedReceipt);
      toast.success("Receipt total updated");
      setReconcileDialogOpen(false);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to update receipt total"
      );
      updateReceiptMutation.reset();
    }
  };

  const handleUndoAutoRemoved = async () => {
    if (autoRemovedItems.length === 0) {
      return;
    }

    setIsRestoringRemoved(true);
    try {
      let updatedReceipt = currentReceipt;
      for (const removed of autoRemovedItems) {
        const itemData: ReceiptItemCreate = {
          name: removed.name,
          quantity: removed.quantity,
          unit_price: Number(removed.unit_price),
          currency: removed.currency,
          category_id: removed.category_id ?? undefined,
        };

        updatedReceipt = await createItemMutation.mutateAsync({
          receiptId: currentReceipt.id,
          data: itemData,
        });
      }
      setCurrentReceipt(updatedReceipt);
      setAutoRemovedItems([]);
      setRemovedDetailsOpen(false);
      toast.success("Restored auto-removed items");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to restore items"
      );
      createItemMutation.reset();
    } finally {
      setIsRestoringRemoved(false);
    }
  };

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
            {currentReceipt.items.length} items detected
          </p>
          {autoRemovedItems.length > 0 && (
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <Badge
                variant="outline"
                className="border-amber-500/40 text-amber-500"
              >
                Auto-removed {autoRemovedItems.length} suspected duplicate line
                {autoRemovedItems.length > 1 ? "s" : ""}
              </Badge>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={() => setRemovedDetailsOpen(true)}
              >
                Why?
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={handleUndoAutoRemoved}
                disabled={isRestoringRemoved}
              >
                {isRestoringRemoved ? "Restoring..." : "Undo"}
              </Button>
            </div>
          )}
          {hasMismatch && (
            <p className="text-sm text-amber-500">
              Items don&apos;t match total by{" "}
              {(delta >= 0 ? "+" : "-") +
                formatCurrency(Math.abs(delta), currentReceipt.currency)}
            </p>
          )}
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
                <CardTitle>{currentReceipt.store_name}</CardTitle>
                <p className="text-sm text-muted-foreground">
                  {formatDate(currentReceipt.purchase_date)}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold">
                {formatCurrency(receiptTotal, currentReceipt.currency)}
              </p>
              {hasMismatch && (
                <div className="mt-2 flex justify-end">
                  <Badge
                    variant="outline"
                    className="border-amber-500/40 text-amber-500 text-xs"
                  >
                    Items don&apos;t match
                  </Badge>
                </div>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Separator className="mb-4" />

          {/* Items */}
          <div className="space-y-3">
            {currentReceipt.items.map((item) => {
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
                  <div className="flex items-center gap-2">
                    <span className="font-medium">
                      {formatCurrency(Number(item.total_price), item.currency)}
                    </span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-destructive hover:text-destructive"
                      onClick={() => handleRemoveItem(item.id)}
                      disabled={removingItemId === item.id}
                      aria-label={`Remove ${item.name}`}
                    >
                      {removingItemId === item.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>

          <Separator className="my-4" />

          <div className="space-y-2">
            <div className="flex items-center justify-between text-lg font-semibold">
              <div className="flex items-center gap-2">
                <span>Receipt total</span>
                {hasMismatch && (
                  <Badge
                    variant="outline"
                    className="border-amber-500/40 text-amber-500 text-xs"
                  >
                    Items don&apos;t match
                  </Badge>
                )}
              </div>
              <span>{formatCurrency(receiptTotal, currentReceipt.currency)}</span>
            </div>

            {hasMismatch && (
              <>
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span>Items total</span>
                  <span>{formatCurrency(itemsTotal, currentReceipt.currency)}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Difference</span>
                  <span className="text-amber-500">
                    {(delta >= 0 ? "+" : "-") +
                      formatCurrency(Math.abs(delta), currentReceipt.currency)}
                  </span>
                </div>
                <div className="flex justify-end">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setReconcileDialogOpen(true)}
                  >
                    Fix mismatch
                  </Button>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-3">
        <Button variant="outline" onClick={onScanAnother} className="flex-1">
          Scan Another
        </Button>
        <Button className="flex-1 bg-amber-500 hover:bg-amber-600 text-black" asChild>
          <Link href={`/receipts/${currentReceipt.id}`}>
            View Details
            <ArrowRight className="h-4 w-4 ml-2" />
          </Link>
        </Button>
      </div>

      <Dialog
        open={reconcileDialogOpen}
        onOpenChange={setReconcileDialogOpen}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Fix total mismatch</DialogTitle>
            <DialogDescription>
              Items don&apos;t match the receipt total. Choose how to reconcile.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="rounded-md border border-border/60 p-3 text-sm space-y-2">
              <div className="flex items-center justify-between text-muted-foreground">
                <span>Receipt total</span>
                <span>{formatCurrency(receiptTotal, currentReceipt.currency)}</span>
              </div>
              <div className="flex items-center justify-between text-muted-foreground">
                <span>Items total</span>
                <span>{formatCurrency(itemsTotal, currentReceipt.currency)}</span>
              </div>
              <div className="flex items-center justify-between font-medium">
                <span>Difference</span>
                <span className="text-amber-500">
                  {(delta >= 0 ? "+" : "-") +
                    formatCurrency(Math.abs(delta), currentReceipt.currency)}
                </span>
              </div>
            </div>

            <div className="space-y-3">
              <div className="rounded-md border border-border/60 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">AI reconcile items</p>
                    <p className="text-xs text-muted-foreground">
                      Removes likely duplicate/noise item lines.
                    </p>
                  </div>
                  {reconcileSuggestion === null && (
                    <Button
                      size="sm"
                      className="bg-amber-500 hover:bg-amber-600 text-black"
                      onClick={handleRunAiReconcile}
                      disabled={
                        reconcileMutation.isPending ||
                        isReconciling ||
                        isAiAlreadyAnalyzed
                      }
                    >
                      {reconcileMutation.isPending ? "Running..." : "Run AI"}
                    </Button>
                  )}
                </div>
                {reconcileSuggestion && (
                  <div className="mt-3 space-y-2 text-xs text-muted-foreground">
                    {reconcileSuggestion.adjustments.length === 0 ? (
                      <p>No removable lines suggested.</p>
                    ) : (
                      <div className="space-y-2">
                        <p className="text-muted-foreground">
                          Suggested removals: {reconcileSuggestion.adjustments.length} line
                          {reconcileSuggestion.adjustments.length > 1 ? "s" : ""}:
                        </p>
                        {reconcileSuggestion.adjustments.map((adjustment) => {
                          const item = itemById.get(adjustment.item_id);
                          if (!item) return null;

                          return (
                            <div
                              key={adjustment.item_id}
                              className="rounded-md border border-border/40 p-2"
                            >
                              <div className="font-medium text-foreground">
                                {item.name}
                              </div>
                              {adjustment.reason && (
                                <div className="mt-1">{adjustment.reason}</div>
                              )}
                            </div>
                          );
                        })}
                        <div className="flex justify-end">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={handleApplyAiSuggestions}
                            disabled={isReconciling}
                          >
                            {isReconciling ? "Applying..." : "Apply"}
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="rounded-md border border-border/60 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">Set receipt total to items sum</p>
                    <p className="text-xs text-muted-foreground">
                      Keeps item lines unchanged and updates only the receipt total.
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleSetReceiptTotal}
                    disabled={updateReceiptMutation.isPending}
                  >
                    {updateReceiptMutation.isPending ? "Applying..." : "Apply"}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={removedDetailsOpen} onOpenChange={setRemovedDetailsOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Auto-removed duplicate lines</DialogTitle>
            <DialogDescription>
              These lines were auto-removed because item totals exceeded the
              receipt total and duplicates were detected.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            {autoRemovedItems.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No auto-removed lines.
              </p>
            ) : (
              autoRemovedItems.map((item, index) => (
                <div
                  key={`${item.name}-${item.total_price}-${index}`}
                  className="flex items-center justify-between rounded-md border border-border/60 px-3 py-2 text-sm"
                >
                  <span>
                    {item.quantity}x {item.name}
                  </span>
                  <span className="font-medium">
                    {formatCurrency(Number(item.total_price), item.currency)}
                  </span>
                </div>
              ))
            )}
          </div>
          {autoRemovedItems.length > 0 && (
            <div className="flex justify-end">
              <Button
                type="button"
                variant="outline"
                onClick={handleUndoAutoRemoved}
                disabled={isRestoringRemoved}
              >
                {isRestoringRemoved ? "Restoring..." : "Undo removals"}
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
