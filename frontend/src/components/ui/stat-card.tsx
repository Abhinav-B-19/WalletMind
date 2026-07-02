import { Card, CardContent } from "@/components/ui/card";

type StatCardProps = {
  label: string;
  value: string;
};

export function StatCard({ label, value }: StatCardProps) {
  return (
    <Card>
      <CardContent className="space-y-2 p-4">
        <p className="text-xs uppercase tracking-[0.08em] text-[var(--text-muted)]">
          {label}
        </p>
        <p className="text-lg font-semibold">{value}</p>
      </CardContent>
    </Card>
  );
}
