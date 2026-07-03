import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

type MetricCardProps = {
  label: string;
  value: string;
  icon: LucideIcon;
  toneClassName?: string;
};

export function MetricCard({
  label,
  value,
  icon: Icon,
  toneClassName,
}: MetricCardProps) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between gap-3 p-4 md:p-5">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
            {label}
          </p>
          <p className="mt-2 truncate text-xl font-semibold md:text-2xl">
            {value}
          </p>
        </div>
        <div
          className={`grid h-10 w-10 flex-shrink-0 place-items-center rounded-full border border-[var(--border)] bg-[var(--surface-soft)] ${toneClassName ?? ""}`}
        >
          <Icon
            className="h-[var(--icon-md)] w-[var(--icon-md)]"
            aria-hidden="true"
          />
        </div>
      </CardContent>
    </Card>
  );
}
