"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { RegisterForm } from "@/components/auth/register-form";
import { useRegister, useLogin } from "@/hooks";
import { toast } from "sonner";
import { Receipt } from "lucide-react";
import type { RegisterCredentials } from "@/types";

export default function RegisterPage() {
  const router = useRouter();
  const registerMutation = useRegister();
  const loginMutation = useLogin();
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (credentials: RegisterCredentials) => {
    setError(null);
    try {
      // Register the user
      await registerMutation.mutateAsync(credentials);
      toast.success("Account created successfully!");

      // Auto-login after successful registration
      await loginMutation.mutateAsync({
        email: credentials.email,
        password: credentials.password,
      });
      router.push("/");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Registration failed";
      setError(message);
      registerMutation.reset();
      loginMutation.reset();
    }
  };

  const isLoading = registerMutation.isPending || loginMutation.isPending;

  return (
    <Card>
      <CardHeader className="space-y-1 text-center">
        <div className="flex justify-center mb-2">
          <div className="rounded-lg bg-primary/10 p-3">
            <Receipt className="h-6 w-6 text-primary" />
          </div>
        </div>
        <CardTitle className="text-2xl">Create an account</CardTitle>
        <CardDescription>
          Enter your details to get started
        </CardDescription>
      </CardHeader>
      <CardContent>
        <RegisterForm
          onSubmit={handleSubmit}
          isPending={isLoading}
          error={error}
        />
        <div className="mt-4 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
