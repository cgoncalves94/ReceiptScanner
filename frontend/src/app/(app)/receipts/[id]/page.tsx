"use client";

import { use, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ArrowLeft,
  Receipt,
  Calendar,
  Store,
  ImageIcon,
  Trash2,
  Pencil,
  FileText,
  Tag,
  CreditCard,
  DollarSign,
  Plus,
} from "lucide-react";
import {
  useReceipt,
  useDeleteReceipt,
  useUpdateReceipt,
  useUpdateReceiptItem,
  useDeleteReceiptItem,
  useReconcileReceipt,
  useCategories,
} from "@/hooks";
import { AddItemDialog } from "@/components/receipts/add-item-dialog";
import { formatCurrency, formatDate } from "@/lib/format";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import type {
  ReceiptItem,
  ReceiptReconcileSuggestion,
  ReceiptUpdate,
} from "@/types";
import { PAYMENT_METHOD_LABELS } from "@/types";
import { MetadataForm } from "@/components/receipts/metadata-form";

interface PageProps {
  params: Promise<{ id: string }>;
}

const roundCurrency = (value: number) =>
  Math.round((value + Number.EPSILON) * 100) / 100;

export default function ReceiptDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const receiptId = parseInt(id, 10);
  const router = useRouter();

  const { data: receipt, isLoading, error } = useReceipt(receiptId);
  const { data: categories } = useCategories();
  const deleteMutation = useDeleteReceipt();
  const updateMutation = useUpdateReceipt();
  const updateItemMutation = useUpdateReceiptItem();
  const reconcileMutation = useReconcileReceipt();
  const deleteItemMutation = useDeleteReceiptItem();

  // Create a map for quick category lookup
  const categoryMap = new Map(
    categories?.map((c) => [c.id, c.name]) ?? []
  );

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [metadataDialogOpen, setMetadataDialogOpen] = useState(false);
  const [addItemDialogOpen, setAddItemDialogOpen] = useState(false);
  const [imagePreviewOpen, setImagePreviewOpen] = useState(false);
  const [reconcileDialogOpen, setReconcileDialogOpen] = useState(false);
  const [reconcileSuggestion, setReconcileSuggestion] =
    useState<ReceiptReconcileSuggestion | null>(null);
  const [aiAnalyzedFingerprint, setAiAnalyzedFingerprint] = useState<
    string | null
  >(null);
  const [isReconciling, setIsReconciling] = useState(false);
  const [editingItem, setEditingItem] = useState<ReceiptItem | null>(null);
  const [itemToDelete, setItemToDelete] = useState<ReceiptItem | null>(null);
  const [isDeleteConfirmationOpen, setDeleteConfirmationOpen] = useState(false);
  const [editName, setEditName] = useState("");
  const [editCategoryId, setEditCategoryId] = useState<string>("");
  const [editQuantity, setEditQuantity] = useState("");
  const [editUnitPrice, setEditUnitPrice] = useState("");

  const { receiptTotal, itemsTotal, delta, hasMismatch } = useMemo(() => {
    if (!receipt) {
      return { receiptTotal: 0, itemsTotal: 0, delta: 0, hasMismatch: false };
    }

    const receiptValue = roundCurrency(Number(receipt.total_amount));
    const itemsValue = roundCurrency(
      receipt.items.reduce((sum, item) => sum + Number(item.total_price), 0)
    );
    const difference = roundCurrency(itemsValue - receiptValue);
    return {
      receiptTotal: receiptValue,
      itemsTotal: itemsValue,
      delta: difference,
      hasMismatch: Math.abs(difference) > 0.05,
    };
  }, [receipt]);

  const itemById = useMemo(() => {
    return new Map(receipt?.items.map((item) => [item.id, item]) ?? []);
  }, [receipt]);

  const receiptStateFingerprint = useMemo(() => {
    if (!receipt) return "";
    const itemsSignature = [...receipt.items]
      .sort((a, b) => a.id - b.id)
      .map(
        (item) =>
          `${item.id}:${item.quantity}:${Number(item.unit_price)}:${Number(item.total_price)}`
      )
      .join("|");
    return `${receipt.id}:${Number(receipt.total_amount)}:${itemsSignature}`;
  }, [receipt]);

  const isAiAlreadyAnalyzed =
    aiAnalyzedFingerprint !== null && aiAnalyzedFingerprint === receiptStateFingerprint;
  useEffect(() => {
    if (aiAnalyzedFingerprint && aiAnalyzedFingerprint !== receiptStateFingerprint) {
      setReconcileSuggestion(null);
    }
  }, [aiAnalyzedFingerprint, receiptStateFingerprint]);

  const openEditItem = (item: ReceiptItem) => {
    setEditingItem(item);
    setEditName(item.name);
    setEditCategoryId(item.category_id?.toString() ?? "");
    setEditQuantity(item.quantity ?? item.quantity === 0 ? String(item.quantity) : "");
    setEditUnitPrice(item.unit_price ?? item.unit_price === 0 ? String(item.unit_price) : "");
  };

  const handleUpdateItem = async () => {
    if (!editingItem) return;

    const quantityValue = editQuantity.trim();
    const unitPriceValue = editUnitPrice.trim();
    const quantity =
      quantityValue === "" ? undefined : Number.parseInt(quantityValue, 10);
    const unitPrice =
      unitPriceValue === "" ? undefined : Number.parseFloat(unitPriceValue);

    if (quantityValue !== "" && Number.isNaN(quantity)) {
      toast.error("Quantity must be a whole number");
      return;
    }

    if (unitPriceValue !== "" && Number.isNaN(unitPrice)) {
      toast.error("Unit price must be a number");
      return;
    }

    try {
      await updateItemMutation.mutateAsync({
        receiptId,
        itemId: editingItem.id,
        data: {
          name: editName.trim() || undefined,
          category_id: editCategoryId ? parseInt(editCategoryId) : undefined,
          quantity,
          unit_price: unitPrice,
        },
      });
      toast.success("Item updated");
      setEditingItem(null);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to update item"
      );
      updateItemMutation.reset();
    }
  };

  const handleRunAiReconcile = async () => {
    if (isAiAlreadyAnalyzed) {
      return;
    }
    try {
      const suggestion = await reconcileMutation.mutateAsync(receiptId);
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
    if (!receipt) {
      toast.error("Receipt data not loaded");
      return;
    }

    setIsReconciling(true);
    try {
      for (const adjustment of reconcileSuggestion.adjustments) {
        await deleteItemMutation.mutateAsync({
          receiptId,
          itemId: adjustment.item_id,
        });
      }
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

  const handleSetReceiptTotal = async () => {
    try {
      await updateMutation.mutateAsync({
        id: receiptId,
        data: { total_amount: itemsTotal },
      });
      toast.success("Receipt total updated");
      setReconcileDialogOpen(false);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to update receipt total"
      );
      updateMutation.reset();
    }
  };

  const handleUpdateMetadata = async (data: ReceiptUpdate) => {
    try {
      await updateMutation.mutateAsync({ id: receiptId, data });
      toast.success("Details updated");
      setMetadataDialogOpen(false);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to update details"
      );
      updateMutation.reset();
    }
  };

  const handleDeleteItem = async () => {
    if (!itemToDelete) return;

    try {
      await deleteItemMutation.mutateAsync({ receiptId, itemId: itemToDelete.id });
      toast.success("Item deleted");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to delete item"
      );
      deleteItemMutation.reset();
    } finally {
      setDeleteConfirmationOpen(false);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(receiptId);
      toast.success("Receipt deleted");
      router.push("/receipts");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to delete receipt"
      );
      deleteMutation.reset();
      setDeleteDialogOpen(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <Skeleton className="h-10 w-32" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error || !receipt) {
    return (
      <div className="max-w-5xl mx-auto">
        <Card className="bg-card/50 border-border/50">
          <CardContent className="py-12 text-center">
            <Receipt className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
            <p className="text-lg font-medium">Receipt not found</p>
            <p className="text-muted-foreground mb-4">
              This receipt may have been deleted
            </p>
            <Button variant="outline" asChild>
              <Link href="/receipts">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Receipts
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Back Button */}
      <Button variant="ghost" asChild className="-ml-2">
        <Link href="/receipts">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Receipts
        </Link>
      </Button>

      {/* Receipt Header */}
      <Card className="bg-card/50 border-border/50">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-xl bg-amber-500/10 flex items-center justify-center">
                <Receipt className="h-7 w-7 text-amber-500" />
              </div>
              <div>
                <CardTitle className="text-2xl">{receipt.store_name}</CardTitle>
                <div className="flex items-center gap-4 mt-1 text-muted-foreground">
                  <div className="flex items-center gap-1.5">
                    <Calendar className="h-4 w-4" />
                    <span>{formatDate(receipt.purchase_date)}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Store className="h-4 w-4" />
                    <span>{receipt.items.length} items</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold tabular-nums">
                {formatCurrency(receiptTotal, receipt.currency)}
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
      </Card>

      {/* Items */}
      <Card className="bg-card/50 border-border/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Items</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAddItemDialogOpen(true)}
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Item
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {receipt.items.map((item, index) => {
              const categoryName = item.category_id
                ? categoryMap.get(item.category_id)
                : null;

              return (
                <div key={item.id}>
                  {index > 0 && <Separator className="my-3" />}
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{item.name}</span>
                        {categoryName && (
                          <Badge variant="secondary" className="text-xs">
                            {categoryName}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {item.quantity} × {formatCurrency(Number(item.unit_price), item.currency)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold tabular-nums">
                        {formatCurrency(Number(item.total_price), item.currency)}
                      </span>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => openEditItem(item)}
                        aria-label="Edit item"
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-destructive hover:text-destructive"
                        onClick={() => {
                          setItemToDelete(item);
                          setDeleteConfirmationOpen(true);
                        }}
                        aria-label="Delete item"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
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
              <span className="tabular-nums">
                {formatCurrency(receiptTotal, receipt.currency)}
              </span>
            </div>

            {hasMismatch && (
              <>
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span>Items total</span>
                  <span className="tabular-nums">
                    {formatCurrency(itemsTotal, receipt.currency)}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Difference</span>
                  <span className="tabular-nums text-amber-500">
                    {(delta >= 0 ? "+" : "-") +
                      formatCurrency(Math.abs(delta), receipt.currency)}
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

      {/* Details / Metadata */}
      <Card className="bg-card/50 border-border/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Details</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setMetadataDialogOpen(true)}
            >
              <Pencil className="h-4 w-4 mr-2" />
              Edit Details
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Notes */}
            <div className="space-y-1.5 md:col-span-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <FileText className="h-4 w-4" />
                <span>Notes</span>
              </div>
              <p className="text-sm">
                {receipt.notes || (
                  <span className="text-muted-foreground italic">No notes</span>
                )}
              </p>
            </div>

            {/* Tags */}
            <div className="space-y-1.5 md:col-span-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Tag className="h-4 w-4" />
                <span>Tags</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {receipt.tags.length > 0 ? (
                  receipt.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                    </Badge>
                  ))
                ) : (
                  <span className="text-sm text-muted-foreground italic">
                    No tags
                  </span>
                )}
              </div>
            </div>

            {/* Payment Method */}
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <CreditCard className="h-4 w-4" />
                <span>Payment Method</span>
              </div>
              <p className="text-sm">
                {receipt.payment_method ? (
                  PAYMENT_METHOD_LABELS[receipt.payment_method]
                ) : (
                  <span className="text-muted-foreground italic">Not specified</span>
                )}
              </p>
            </div>

            {/* Tax Amount */}
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <DollarSign className="h-4 w-4" />
                <span>Tax Amount</span>
              </div>
              <p className="text-sm">
                {receipt.tax_amount !== null ? (
                  formatCurrency(receipt.tax_amount, receipt.currency)
                ) : (
                  <span className="text-muted-foreground italic">Not specified</span>
                )}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Receipt Image */}
      {receipt.image_path && (
        <Card className="bg-card/50 border-border/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <ImageIcon className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Receipt Image</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <button
              type="button"
              onClick={() => setImagePreviewOpen(true)}
              className="w-full rounded-lg overflow-hidden border border-border/50 bg-muted/20 cursor-zoom-in hover:border-amber-500/50 transition-colors"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`/api/receipts/${receipt.id}/image`}
                alt="Receipt"
                className="w-full max-h-150 object-contain"
              />
            </button>
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogTrigger asChild>
            <Button
              variant="outline"
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Receipt
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Receipt</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete this receipt? This action cannot
                be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                {deleteMutation.isPending ? "Deleting..." : "Delete"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>

      {/* Edit Item Dialog */}
      <Dialog
        open={!!editingItem}
        onOpenChange={(open) => !open && setEditingItem(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Item</DialogTitle>
            <DialogDescription>
              Update item details
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-item-name">Name</Label>
              <Input
                id="edit-item-name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-item-category">Category</Label>
              <Select value={editCategoryId} onValueChange={setEditCategoryId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a category" />
                </SelectTrigger>
                <SelectContent>
                  {categories?.map((category) => (
                    <SelectItem key={category.id} value={category.id.toString()}>
                      {category.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="edit-item-quantity">Quantity</Label>
                <Input
                  id="edit-item-quantity"
                  type="number"
                  min="0"
                  step="1"
                  value={editQuantity}
                  onChange={(e) => setEditQuantity(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-item-unit-price">Unit Price</Label>
                <Input
                  id="edit-item-unit-price"
                  type="number"
                  min="0"
                  step="0.01"
                  value={editUnitPrice}
                  onChange={(e) => setEditUnitPrice(e.target.value)}
                />
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setEditingItem(null)}>
              Cancel
            </Button>
            <Button
              onClick={handleUpdateItem}
              disabled={updateItemMutation.isPending}
              className="bg-amber-500 hover:bg-amber-600 text-black"
            >
              {updateItemMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Item Confirmation Dialog */}
      <AlertDialog
        open={isDeleteConfirmationOpen}
        onOpenChange={setDeleteConfirmationOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Item</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete &quot;{itemToDelete?.name}&quot;? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteItem}
              disabled={deleteItemMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteItemMutation.isPending ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Edit Metadata Dialog */}
      <MetadataForm
        receipt={receipt}
        open={metadataDialogOpen}
        onOpenChange={setMetadataDialogOpen}
        onSave={handleUpdateMetadata}
        isPending={updateMutation.isPending}
      />

      {/* Add Item Dialog */}
      <AddItemDialog
        open={addItemDialogOpen}
        onOpenChange={setAddItemDialogOpen}
        receiptId={receiptId}
        currency={receipt.currency}
      />

      {/* Reconcile Totals Dialog */}
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
                <span className="tabular-nums">
                  {formatCurrency(receiptTotal, receipt.currency)}
                </span>
              </div>
              <div className="flex items-center justify-between text-muted-foreground">
                <span>Items total</span>
                <span className="tabular-nums">
                  {formatCurrency(itemsTotal, receipt.currency)}
                </span>
              </div>
              <div className="flex items-center justify-between font-medium">
                <span>Difference</span>
                <span className="tabular-nums text-amber-500">
                  {(delta >= 0 ? "+" : "-") +
                    formatCurrency(Math.abs(delta), receipt.currency)}
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
                    disabled={updateMutation.isPending}
                  >
                    {updateMutation.isPending ? "Applying..." : "Apply"}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Image Preview Dialog */}
      {receipt.image_path && (
        <Dialog open={imagePreviewOpen} onOpenChange={setImagePreviewOpen}>
          <DialogContent className="max-w-5xl max-h-[90vh] p-0 overflow-hidden">
            <DialogHeader className="sr-only">
              <DialogTitle>Receipt Image</DialogTitle>
              <DialogDescription>Full size receipt image</DialogDescription>
            </DialogHeader>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`/api/receipts/${receipt.id}/image`}
              alt="Receipt"
              className="w-full h-full max-h-[85vh] object-contain"
            />
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
