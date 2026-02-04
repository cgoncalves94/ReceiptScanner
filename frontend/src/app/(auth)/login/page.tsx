"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LoginForm } from "@/components/auth/login-form";
import { useLogin } from "@/hooks";
import { toast } from "sonner";
import { Receipt } from "lucide-react";
import type { LoginCredentials } from "@/types";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const loginMutation = useLogin();
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (credentials: LoginCredentials) => {
    setError(null);
    try {
      await loginMutation.mutateAsync(credentials);
      toast.success("Login successful!");
      const redirect = searchParams.get("redirect");
      const destination =
        redirect && redirect.startsWith("/") && !redirect.startsWith("//")
          ? redirect
          : "/";
      router.push(destination);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Login failed";
      setError(message);
      loginMutation.reset();
    }
  };

  return (
    <Card>
      <CardHeader className="space-y-1 text-center">
        <div className="flex justify-center mb-2">
          <div className="rounded-lg bg-primary/10 p-3">
            <Receipt className="h-6 w-6 text-primary" />
          </div>
        </div>
        <CardTitle className="text-2xl">Welcome back</CardTitle>
        <CardDescription>
          Sign in to your account to continue
        </CardDescription>
      </CardHeader>
      <CardContent>
        <LoginForm
          onSubmit={handleSubmit}
          isPending={loginMutation.isPending}
          error={error}
        />
        <div className="mt-4 text-center text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-primary hover:underline">
            Sign up
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
