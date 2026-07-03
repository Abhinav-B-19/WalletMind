import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { HealthScoreGauge } from "@/features/ai-dashboard/components/health-score-gauge";
import { SectionCard } from "@/features/ai-dashboard/components/section-card";
import type { FinancialHealthScore } from "@/features/ai-dashboard/types";

type AIHeroCardProps = {
  data: FinancialHealthScore;
  onAction: () => void;
};

export function AIHeroCard({ data, onAction }: AIHeroCardProps) {
  return (
    <SectionCard
      title="Financial Health Snapshot"
      description="A deterministic score enriched with WalletMind AI guidance."
      action={
        <Button type="button" onClick={onAction}>
          <Sparkles className="mr-2 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
          Ask Assistant
        </Button>
      }
      className="overflow-hidden"
      contentClassName="pt-2"
    >
      <div className="grid gap-5 lg:grid-cols-[auto_1fr] lg:items-center">
        <div className="mx-auto lg:mx-0">
          <HealthScoreGauge score={data.overall_score} grade={data.grade} />
        </div>

        <div className="space-y-3">
          <p className="text-base text-[var(--text-muted)]">
            {data.ai_explanation}
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
              <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
                Top Strength
              </p>
              <p className="mt-1 text-sm font-medium">
                {data.strengths[0] ?? "Healthy spending rhythm."}
              </p>
            </div>
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
              <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
                Priority Fix
              </p>
              <p className="mt-1 text-sm font-medium">
                {data.weaknesses[0] ??
                  "Continue monitoring recurring expenses."}
              </p>
            </div>
          </div>
        </div>
      </div>
    </SectionCard>
  );
}
