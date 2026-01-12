"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
import type { Receipt, PaymentMethod, ReceiptUpdate } from "@/types";
import { PAYMENT_METHOD_LABELS } from "@/types";

interface MetadataFormProps {
  receipt: Receipt;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (data: ReceiptUpdate) => Promise<void>;
  isPending?: boolean;
}

const PAYMENT_METHODS: PaymentMethod[] = [
  "cash",
  "credit_card",
  "debit_card",
  "mobile_payment",
  "other",
];

export function MetadataForm({
  receipt,
  open,
  onOpenChange,
  onSave,
  isPending,
}: MetadataFormProps) {
  const [notes, setNotes] = useState(receipt.notes ?? "");
  const [tagsInput, setTagsInput] = useState(receipt.tags.join(", "));
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod | "">(
    receipt.payment_method ?? ""
  );
  const [taxAmount, setTaxAmount] = useState(
    receipt.tax_amount?.toString() ?? ""
  );

  // Reset form when dialog opens with new receipt data
  const handleOpenChange = (newOpen: boolean) => {
    if (newOpen) {
      setNotes(receipt.notes ?? "");
      setTagsInput(receipt.tags.join(", "));
      setPaymentMethod(receipt.payment_method ?? "");
      setTaxAmount(receipt.tax_amount?.toString() ?? "");
    }
    onOpenChange(newOpen);
  };

  const handleSubmit = async () => {
    // Parse tags from comma-separated input
    const tags = tagsInput
      .split(",")
      .map((tag) => tag.trim())
      .filter((tag) => tag.length > 0);

    const data: ReceiptUpdate = {
      notes: notes.trim() || null,
      tags,
      payment_method: paymentMethod || null,
      tax_amount: taxAmount ? parseFloat(taxAmount) : null,
    };

    await onSave(data);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Receipt Details</DialogTitle>
          <DialogDescription>
            Update notes, tags, payment method, and tax information.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              placeholder="Add notes about this receipt..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              maxLength={1000}
              rows={3}
            />
            <p className="text-xs text-muted-foreground text-right">
              {notes.length}/1000
            </p>
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <Label htmlFor="tags">Tags</Label>
            <Input
              id="tags"
              placeholder="groceries, weekly, household"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Separate tags with commas
            </p>
          </div>

          {/* Payment Method */}
          <div className="space-y-2">
            <Label htmlFor="payment-method">Payment Method</Label>
            <Select
              value={paymentMethod}
              onValueChange={(value) =>
                setPaymentMethod(value as PaymentMethod | "")
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Select payment method" />
              </SelectTrigger>
              <SelectContent>
                {PAYMENT_METHODS.map((method) => (
                  <SelectItem key={method} value={method}>
                    {PAYMENT_METHOD_LABELS[method]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Tax Amount */}
          <div className="space-y-2">
            <Label htmlFor="tax-amount">Tax Amount</Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                {receipt.currency}
              </span>
              <Input
                id="tax-amount"
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
                value={taxAmount}
                onChange={(e) => setTaxAmount(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isPending}
            className="bg-amber-500 hover:bg-amber-600 text-black"
          >
            {isPending ? "Saving..." : "Save"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
