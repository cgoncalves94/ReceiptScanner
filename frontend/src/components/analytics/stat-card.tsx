import { ReactNode } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface StatCardProps {
  title: string;
  value: ReactNode;
  icon: ReactNode;
  isLoading?: boolean;
  iconClassName?: string;
  valueClassName?: string;
}

export function StatCard({
  title,
  value,
  icon,
  isLoading = false,
  iconClassName = "h-4 w-4 text-muted-foreground",
  valueClassName = "text-2xl font-bold",
}: StatCardProps) {
  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className={iconClassName}>{icon}</div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-8 w-24" />
        ) : (
          <div className={valueClassName}>{value}</div>
        )}
      </CardContent>
    </Card>
  );
}
