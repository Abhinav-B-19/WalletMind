import { Card, CardContent, CardHeader } from "@/components/ui/card";

type LoadingCardProps = {
  ariaLabel: string;
  lines?: number;
  compact?: boolean;
};

export function LoadingCard({
  ariaLabel,
  lines = 3,
  compact = false,
}: LoadingCardProps) {
  return (
    <Card aria-label={ariaLabel} role="status">
      <CardHeader className="pb-4">
        <div className="h-5 w-40 animate-pulse rounded bg-[var(--surface-soft)]" />
      </CardHeader>
      <CardContent className={compact ? "space-y-2" : "space-y-3"}>
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={index}
            className="h-4 animate-pulse rounded bg-[var(--surface-soft)]"
            style={{ width: `${100 - index * 8}%` }}
          />
        ))}
      </CardContent>
    </Card>
  );
}
