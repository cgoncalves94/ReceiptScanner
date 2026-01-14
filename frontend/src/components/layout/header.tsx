"use client";

import { usePathname, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Scan, Menu, LogOut } from "lucide-react";
import Link from "next/link";
import { useUIStore } from "@/lib/store";
import { useUser, useLogout } from "@/hooks/use-auth";

const pageTitles: Record<string, string> = {
  "/": "Dashboard",
  "/scan": "Scan Receipt",
  "/receipts": "Receipts",
  "/categories": "Categories",
  "/analytics": "Analytics",
};

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const { toggleSidebar } = useUIStore();
  const { data: user } = useUser();
  const logoutMutation = useLogout();

  // Get title, handle dynamic routes like /receipts/[id]
  const title = pageTitles[pathname] ||
    (pathname.startsWith("/receipts/") ? "Receipt Details" : "Receipt Scanner");

  const handleLogout = async () => {
    await logoutMutation.mutateAsync();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border/50 bg-background/80 backdrop-blur-sm px-6">
      <div className="flex items-center gap-4">
        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="md:hidden"
        >
          <Menu className="h-5 w-5" />
        </Button>
        <h1 className="text-xl font-semibold">{title}</h1>
      </div>

      <div className="flex items-center gap-3">
        <Button className="bg-amber-500 hover:bg-amber-600 text-black" asChild>
          <Link href="/scan">
            <Scan className="h-4 w-4 mr-2" />
            Scan
          </Link>
        </Button>
        {user && (
          <>
            <span className="text-sm text-muted-foreground hidden sm:inline">
              {user.email}
            </span>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              disabled={logoutMutation.isPending}
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </>
        )}
      </div>
    </header>
  );
}
