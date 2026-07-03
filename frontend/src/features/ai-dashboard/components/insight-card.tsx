import { Lightbulb } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type InsightCardProps = {
  title: string;
  description: string;
  priority: "low" | "medium" | "high";
};

const priorityClassMap: Record<InsightCardProps["priority"], string> = {
  low: "text-[#27c86f] border-[#27c86f]/40",
  medium: "text-[#e3be37] border-[#e3be37]/40",
  high: "text-[#ff6a82] border-[#ff6a82]/40",
};

export function InsightCard({
  title,
  description,
  priority,
}: InsightCardProps) {
  return (
    <Card>
      <CardContent className="space-y-3 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="inline-flex items-center gap-2 text-sm font-semibold">
            <Lightbulb className="h-[var(--icon-sm)] w-[var(--icon-sm)] text-[var(--primary)]" />
            {title}
          </div>
          <Badge
            variant="muted"
            className={cn("uppercase", priorityClassMap[priority])}
          >
            {priority}
          </Badge>
        </div>
        <p className="text-sm text-[var(--text-muted)]">{description}</p>
      </CardContent>
    </Card>
  );
}
