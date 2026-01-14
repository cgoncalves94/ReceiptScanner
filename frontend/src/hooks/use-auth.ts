"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { User, LoginCredentials, RegisterCredentials } from "@/types";

const AUTH_KEY = ["auth", "user"];

export function useUser() {
  return useQuery({
    queryKey: AUTH_KEY,
    queryFn: () => api.getCurrentUser(),
    retry: false,
    enabled: !!api.getToken(),
  });
}

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (credentials: LoginCredentials) => api.login(credentials),
    onSuccess: async () => {
      // Fetch user data after successful login
      try {
        const user = await api.getCurrentUser();
        queryClient.setQueryData<User>(AUTH_KEY, user);
      } catch {
        // If getCurrentUser fails after login succeeds, clean up the stored token
        // to maintain consistent state
        api.logout();
        throw new Error("Failed to fetch user data after login");
      }
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: (credentials: RegisterCredentials) => api.register(credentials),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => {
      api.logout();
      return Promise.resolve();
    },
    onSuccess: () => {
      queryClient.setQueryData<User | null>(AUTH_KEY, null);
      queryClient.removeQueries({ queryKey: AUTH_KEY });
      // Clear all queries on logout
      queryClient.clear();
    },
  });
}
