import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

type SourceCardProps = {
  merchant: string;
  amount: string;
  date: string;
  confidenceLabel: string;
};

export function SourceCard({
  merchant,
  amount,
  date,
  confidenceLabel,
}: SourceCardProps) {
  return (
    <Card className="border-[var(--border)] bg-[var(--surface-soft)]">
      <CardContent className="space-y-2 p-3">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-semibold">{merchant}</p>
          <Badge variant="muted">{confidenceLabel}</Badge>
        </div>
        <div className="grid gap-1 text-xs text-[var(--text-muted)]">
          <p>Amount: {amount}</p>
          <p>Date: {date}</p>
        </div>
      </CardContent>
    </Card>
  );
}
