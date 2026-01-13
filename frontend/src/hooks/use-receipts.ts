"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Receipt, ReceiptUpdate, ReceiptItemCreate, ReceiptItemUpdate, ReceiptFilters } from "@/types";

const RECEIPTS_KEY = ["receipts"];

export function useReceipts(filters?: ReceiptFilters) {
  // Include filters in query key so queries with different filters are cached separately
  const queryKey = filters
    ? [...RECEIPTS_KEY, "filtered", filters]
    : RECEIPTS_KEY;

  return useQuery({
    queryKey,
    queryFn: () => api.getReceipts(filters),
  });
}

export function useReceipt(id: number) {
  return useQuery({
    queryKey: [...RECEIPTS_KEY, id],
    queryFn: () => api.getReceipt(id),
    enabled: !!id,
  });
}

export function useScanReceipt() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => api.scanReceipt(file),
    onSuccess: (newReceipt) => {
      // Add to cache
      queryClient.setQueryData<Receipt[]>(RECEIPTS_KEY, (old) =>
        old ? [newReceipt, ...old] : [newReceipt]
      );
    },
  });
}

export function useUpdateReceipt() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ReceiptUpdate }) =>
      api.updateReceipt(id, data),
    onSuccess: (updated) => {
      // Update in list cache
      queryClient.setQueryData<Receipt[]>(RECEIPTS_KEY, (old) =>
        old?.map((r) => (r.id === updated.id ? updated : r))
      );
      // Update individual cache
      queryClient.setQueryData([...RECEIPTS_KEY, updated.id], updated);
    },
  });
}

export function useDeleteReceipt() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.deleteReceipt(id),
    onMutate: async (id) => {
      // Cancel and remove queries BEFORE delete to prevent refetch race
      await queryClient.cancelQueries({ queryKey: [...RECEIPTS_KEY, id] });
      queryClient.removeQueries({ queryKey: [...RECEIPTS_KEY, id] });
      // Optimistically remove from list
      queryClient.setQueryData<Receipt[]>(RECEIPTS_KEY, (old) =>
        old?.filter((r) => r.id !== id)
      );
    },
  });
}

export function useUpdateReceiptItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      receiptId,
      itemId,
      data,
    }: {
      receiptId: number;
      itemId: number;
      data: ReceiptItemUpdate;
    }) => api.updateReceiptItem(receiptId, itemId, data),
    onSuccess: (updated) => {
      queryClient.setQueryData<Receipt[]>(RECEIPTS_KEY, (old) =>
        old?.map((r) => (r.id === updated.id ? updated : r))
      );
      queryClient.setQueryData([...RECEIPTS_KEY, updated.id], updated);
    },
  });
}

export function useCreateReceiptItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      receiptId,
      data,
    }: {
      receiptId: number;
      data: ReceiptItemCreate;
    }) => api.createReceiptItem(receiptId, data),
    onSuccess: (updated) => {
      // Update the receipts list cache
      queryClient.setQueryData<Receipt[]>(RECEIPTS_KEY, (old) =>
        old?.map((r) => (r.id === updated.id ? updated : r))
      );
      // Update the individual receipt cache
      queryClient.setQueryData([...RECEIPTS_KEY, updated.id], updated);
    },
  });
}

export function useDeleteReceiptItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ receiptId, itemId }: { receiptId: number; itemId: number }) =>
      api.deleteReceiptItem(receiptId, itemId),
    onMutate: async ({ receiptId, itemId }) => {
      // Cancel any outgoing refetches to prevent overwriting optimistic update
      await queryClient.cancelQueries({ queryKey: [...RECEIPTS_KEY, receiptId] });

      // Snapshot the previous value
      const previousReceipt = queryClient.getQueryData<Receipt>([
        ...RECEIPTS_KEY,
        receiptId,
      ]);

      // Optimistically update the receipt by removing the item
      if (previousReceipt) {
        const deletedItem = previousReceipt.items.find((i) => i.id === itemId);
        // Round to 2 decimal places to avoid floating-point precision issues
        const newTotal = deletedItem
          ? Math.round((previousReceipt.total_amount - deletedItem.total_price) * 100) / 100
          : previousReceipt.total_amount;

        const updatedReceipt: Receipt = {
          ...previousReceipt,
          total_amount: newTotal,
          items: previousReceipt.items.filter((i) => i.id !== itemId),
        };

        queryClient.setQueryData([...RECEIPTS_KEY, receiptId], updatedReceipt);

        // Also update the list cache
        queryClient.setQueryData<Receipt[]>(RECEIPTS_KEY, (old) =>
          old?.map((r) => (r.id === receiptId ? updatedReceipt : r))
        );
      }

      return { previousReceipt };
    },
    onError: (_err, { receiptId }, context) => {
      // Rollback on error
      if (context?.previousReceipt) {
        queryClient.setQueryData(
          [...RECEIPTS_KEY, receiptId],
          context.previousReceipt
        );
        queryClient.setQueryData<Receipt[]>(RECEIPTS_KEY, (old) =>
          old?.map((r) => (r.id === receiptId ? context.previousReceipt! : r))
        );
      }
    },
    onSuccess: (updated) => {
      // Update with the server response to ensure consistency
      queryClient.setQueryData<Receipt[]>(RECEIPTS_KEY, (old) =>
        old?.map((r) => (r.id === updated.id ? updated : r))
      );
      queryClient.setQueryData([...RECEIPTS_KEY, updated.id], updated);
    },
  });
}
