import { PiggyBank } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

type RecommendationCardProps = {
  title: string;
  category: string;
  priority: "low" | "medium" | "high";
  estimatedSaving: number;
};

export function RecommendationCard({
  title,
  category,
  priority,
  estimatedSaving,
}: RecommendationCardProps) {
  return (
    <Card>
      <CardContent className="space-y-3 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="inline-flex items-center gap-2 text-sm font-semibold">
            <PiggyBank className="h-[var(--icon-sm)] w-[var(--icon-sm)] text-[var(--primary)]" />
            {category}
          </div>
          <Badge variant="muted" className="uppercase">
            {priority}
          </Badge>
        </div>
        <p className="text-sm font-medium">{title}</p>
        <p className="text-sm text-[var(--text-muted)]">
          Estimated monthly saving: {estimatedSaving.toFixed(2)}
        </p>
      </CardContent>
    </Card>
  );
}
