import { AlertTriangle, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

type ErrorCardProps = {
  title: string;
  message: string;
  onRetry?: () => void;
  ariaLabel?: string;
};

export function ErrorCard({
  title,
  message,
  onRetry,
  ariaLabel,
}: ErrorCardProps) {
  return (
    <Card className="border-[var(--danger)]/40" aria-label={ariaLabel}>
      <CardContent className="space-y-3 p-5">
        <div className="flex items-center gap-2 text-[var(--danger)]">
          <AlertTriangle className="h-[var(--icon-md)] w-[var(--icon-md)]" />
          <h3 className="text-sm font-semibold">{title}</h3>
        </div>
        <p className="text-sm text-[var(--text-muted)]">{message}</p>
        {onRetry ? (
          <Button type="button" variant="secondary" onClick={onRetry}>
            <RefreshCw className="mr-2 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
            Retry
          </Button>
        ) : null}
      </CardContent>
    </Card>
  );
}
