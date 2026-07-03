import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

type SavingsOpportunityCardProps = {
  title: string;
  category: string;
  priority: "low" | "medium" | "high";
  estimatedSaving: string;
};

const priorityClasses: Record<SavingsOpportunityCardProps["priority"], string> =
  {
    low: "bg-[#27c86f]/20 text-[#27c86f]",
    medium: "bg-[#e3be37]/20 text-[#e3be37]",
    high: "bg-[#ff6a82]/20 text-[#ff6a82]",
  };

export function SavingsOpportunityCard({
  title,
  category,
  priority,
  estimatedSaving,
}: SavingsOpportunityCardProps) {
  return (
    <Card className="border-[var(--border)] bg-[var(--surface)] shadow-sm">
      <CardContent className="space-y-3 p-4">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-sm font-semibold">{title}</h3>
          <Badge variant="muted" className={priorityClasses[priority]}>
            {priority}
          </Badge>
        </div>
        <p className="text-sm text-[var(--text-muted)]">Category: {category}</p>
        <p className="text-lg font-semibold text-[#27c86f]">
          {estimatedSaving}/mo
        </p>
      </CardContent>
    </Card>
  );
}
