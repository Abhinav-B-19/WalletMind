import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

type InsightCardProps = {
  title: string;
  value: string;
  description: string;
  icon: LucideIcon;
};

export function InsightCard({
  title,
  value,
  description,
  icon: Icon,
}: InsightCardProps) {
  return (
    <Card className="h-full border-[var(--border)] bg-[var(--surface)]">
      <CardContent className="space-y-2 p-4">
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm font-medium text-[var(--text-muted)]">
            {title}
          </p>
          <div className="grid h-8 w-8 place-items-center rounded-full bg-[var(--surface-soft)] text-[var(--primary)]">
            <Icon className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
          </div>
        </div>
        <p className="text-xl font-semibold">{value}</p>
        <p className="text-xs text-[var(--text-muted)]">{description}</p>
      </CardContent>
    </Card>
  );
}
