import type { LucideIcon } from "lucide-react";
import { ArrowUpRight, Inbox } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

type EmptyStateCardProps = {
  title: string;
  description: string;
  ctaLabel?: string;
  ctaHref?: string;
  icon?: LucideIcon;
  ariaLabel?: string;
};

export function EmptyStateCard({
  title,
  description,
  ctaLabel,
  ctaHref,
  icon: Icon = Inbox,
  ariaLabel,
}: EmptyStateCardProps) {
  return (
    <Card aria-label={ariaLabel}>
      <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
        <div className="grid h-12 w-12 place-items-center rounded-full bg-[var(--surface-soft)] text-[var(--text-muted)]">
          <Icon className="h-[var(--icon-lg)] w-[var(--icon-lg)]" />
        </div>
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="max-w-xl text-sm text-[var(--text-muted)]">
          {description}
        </p>
        {ctaLabel && ctaHref ? (
          <Button asChild>
            <Link to={ctaHref}>
              {ctaLabel}
              <ArrowUpRight className="ml-2 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
            </Link>
          </Button>
        ) : null}
      </CardContent>
    </Card>
  );
}
