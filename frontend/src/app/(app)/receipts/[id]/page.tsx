"use client";

import { use, useState } from "react";
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
import { useReceipt, useDeleteReceipt, useUpdateReceipt, useUpdateReceiptItem, useDeleteReceiptItem, useCategories } from "@/hooks";
import { AddItemDialog } from "@/components/receipts/add-item-dialog";
import { formatCurrency, formatDate } from "@/lib/format";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import type { ReceiptItem, ReceiptUpdate } from "@/types";
import { PAYMENT_METHOD_LABELS } from "@/types";
import { MetadataForm } from "@/components/receipts/metadata-form";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ReceiptDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const receiptId = parseInt(id, 10);
  const router = useRouter();

  const { data: receipt, isLoading, error } = useReceipt(receiptId);
  const { data: categories } = useCategories();
  const deleteMutation = useDeleteReceipt();
  const updateMutation = useUpdateReceipt();
  const updateItemMutation = useUpdateReceiptItem();
  const deleteItemMutation = useDeleteReceiptItem();

  // Create a map for quick category lookup
  const categoryMap = new Map(
    categories?.map((c) => [c.id, c.name]) ?? []
  );

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [metadataDialogOpen, setMetadataDialogOpen] = useState(false);
  const [addItemDialogOpen, setAddItemDialogOpen] = useState(false);
  const [imagePreviewOpen, setImagePreviewOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<ReceiptItem | null>(null);
  const [itemToDelete, setItemToDelete] = useState<ReceiptItem | null>(null);
  const [isDeleteConfirmationOpen, setDeleteConfirmationOpen] = useState(false);
  const [editName, setEditName] = useState("");
  const [editCategoryId, setEditCategoryId] = useState<string>("");

  const openEditItem = (item: ReceiptItem) => {
    setEditingItem(item);
    setEditName(item.name);
    setEditCategoryId(item.category_id?.toString() ?? "");
  };

  const handleUpdateItem = async () => {
    if (!editingItem) return;

    try {
      await updateItemMutation.mutateAsync({
        receiptId,
        itemId: editingItem.id,
        data: {
          name: editName.trim() || undefined,
          category_id: editCategoryId ? parseInt(editCategoryId) : undefined,
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
              <p className="text-3xl font-bold">
                {formatCurrency(Number(receipt.total_amount), receipt.currency)}
              </p>
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
                      <span className="font-semibold">
                        {formatCurrency(Number(item.total_price), item.currency)}
                      </span>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => openEditItem(item)}
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

          <div className="flex items-center justify-between text-lg font-semibold">
            <span>Total</span>
            <span>{formatCurrency(Number(receipt.total_amount), receipt.currency)}</span>
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
                src={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/${receipt.image_path}`}
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
              src={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/${receipt.image_path}`}
              alt="Receipt"
              className="w-full h-full max-h-[85vh] object-contain"
            />
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
