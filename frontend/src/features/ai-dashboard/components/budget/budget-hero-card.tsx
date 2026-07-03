import { Badge } from "@/components/ui/badge";
import { SectionCard } from "@/features/ai-dashboard/components/section-card";

type BudgetHeroCardProps = {
  potentialSavings: string;
  budgetHealth: "Within Budget" | "Near Limit" | "Over Budget";
  aiSummary: string;
  generatedAt: string;
};

const badgeClasses: Record<BudgetHeroCardProps["budgetHealth"], string> = {
  "Within Budget": "bg-[#27c86f]/20 text-[#27c86f]",
  "Near Limit": "bg-[#e3be37]/20 text-[#e3be37]",
  "Over Budget": "bg-[#ff6a82]/20 text-[#ff6a82]",
};

export function BudgetHeroCard({
  potentialSavings,
  budgetHealth,
  aiSummary,
  generatedAt,
}: BudgetHeroCardProps) {
  return (
    <SectionCard
      title="Budget Recommendations"
      description="Interactive budget intelligence from deterministic spending data and AI guidance."
      className="bg-gradient-to-r from-[var(--surface)] to-[var(--surface-soft)] shadow-sm"
      action={
        <Badge className={badgeClasses[budgetHealth]}>{budgetHealth}</Badge>
      }
    >
      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <div className="space-y-3">
          <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
            Potential Monthly Savings
          </p>
          <p className="text-3xl font-semibold text-[#27c86f]">
            {potentialSavings}
          </p>
          <p className="text-sm text-[var(--text-muted)]">{aiSummary}</p>
        </div>

        <div className="space-y-3 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
          <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
            Last Generated
          </p>
          <p className="text-sm font-medium">{generatedAt}</p>
          <p className="text-xs text-[var(--text-muted)]">
            Based on selected statement and deterministic budget analysis.
          </p>
        </div>
      </div>
    </SectionCard>
  );
}
