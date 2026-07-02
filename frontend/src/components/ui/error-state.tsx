import { AlertTriangle } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

type ErrorStateProps = {
  title: string;
  description?: string;
};

export function ErrorState({ title, description }: ErrorStateProps) {
  return (
    <Card className="border-[var(--danger)]/40">
      <CardContent className="space-y-2 p-5">
        <div className="flex items-center gap-2 text-[var(--danger)]">
          <AlertTriangle className="h-[var(--icon-md)] w-[var(--icon-md)]" />
          <p className="text-sm font-semibold">{title}</p>
        </div>
        {description ? (
          <p className="text-sm text-[var(--text-muted)]">{description}</p>
        ) : null}
      </CardContent>
    </Card>
  );
}
