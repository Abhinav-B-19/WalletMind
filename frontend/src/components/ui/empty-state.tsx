import type { LucideIcon } from "lucide-react";
import { Inbox } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

type EmptyStateProps = {
  title: string;
  description: string;
  icon?: LucideIcon;
};

export function EmptyState({
  title,
  description,
  icon: Icon = Inbox,
}: EmptyStateProps) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
        <div className="grid h-10 w-10 place-items-center rounded-full bg-[var(--surface-soft)] text-[var(--text-muted)]">
          <Icon className="h-[var(--icon-md)] w-[var(--icon-md)]" />
        </div>
        <h3 className="text-base font-semibold">{title}</h3>
        <p className="max-w-xl text-sm text-[var(--text-muted)]">
          {description}
        </p>
      </CardContent>
    </Card>
  );
}
