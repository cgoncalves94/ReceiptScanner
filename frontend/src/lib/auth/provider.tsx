"use client";

import { useEffect, useState, type ReactNode } from "react";
import { AuthContext, type AuthContextValue } from "./context";
import { api } from "@/lib/api";
import type { User, LoginCredentials, RegisterCredentials } from "@/types";

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load user from token on mount
  useEffect(() => {
    const loadUser = async () => {
      const token = api.getToken();

      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const currentUser = await api.getCurrentUser();
        setUser(currentUser);
      } catch {
        // Token is invalid or expired, remove it
        api.removeToken();
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    await api.login(credentials);
    // Token is automatically stored by api.login
    const currentUser = await api.getCurrentUser();
    setUser(currentUser);
  };

  const register = async (credentials: RegisterCredentials) => {
    await api.register(credentials);
    // After registration, automatically log in
    await login({
      email: credentials.email,
      password: credentials.password,
    });
  };

  const logout = () => {
    api.logout();
    setUser(null);
  };

  const value: AuthContextValue = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
