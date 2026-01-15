"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Listens for auth-error events dispatched by the API client
 * and redirects to login using Next.js router for smoother UX.
 */
export function AuthErrorHandler() {
  const router = useRouter();

  useEffect(() => {
    const handleAuthError = () => {
      router.push("/login");
    };

    window.addEventListener("auth-error", handleAuthError);
    return () => window.removeEventListener("auth-error", handleAuthError);
  }, [router]);

  return null;
}
