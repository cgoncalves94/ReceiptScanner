"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Category, CategoryCreate, CategoryUpdate } from "@/types";

const CATEGORIES_KEY = ["categories"];

export function useCategories() {
  return useQuery({
    queryKey: CATEGORIES_KEY,
    queryFn: () => api.getCategories(),
  });
}

export function useCategory(id: number) {
  return useQuery({
    queryKey: [...CATEGORIES_KEY, id],
    queryFn: () => api.getCategory(id),
    enabled: !!id,
  });
}

export function useCreateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CategoryCreate) => api.createCategory(data),
    onSuccess: (newCategory) => {
      queryClient.setQueryData<Category[]>(CATEGORIES_KEY, (old) =>
        old ? [...old, newCategory] : [newCategory]
      );
    },
  });
}

export function useUpdateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: CategoryUpdate }) =>
      api.updateCategory(id, data),
    onSuccess: (updated) => {
      queryClient.setQueryData<Category[]>(CATEGORIES_KEY, (old) =>
        old?.map((c) => (c.id === updated.id ? updated : c))
      );
      queryClient.setQueryData([...CATEGORIES_KEY, updated.id], updated);
    },
  });
}

export function useDeleteCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.deleteCategory(id),
    onSuccess: (_, deletedId) => {
      queryClient.setQueryData<Category[]>(CATEGORIES_KEY, (old) =>
        old?.filter((c) => c.id !== deletedId)
      );
      queryClient.removeQueries({ queryKey: [...CATEGORIES_KEY, deletedId] });
    },
  });
}

export function useCategoryItems(categoryId: number | null) {
  return useQuery({
    queryKey: [...CATEGORIES_KEY, categoryId, "items"],
    queryFn: () => api.getCategoryItems(categoryId!),
    enabled: categoryId !== null,
  });
}
