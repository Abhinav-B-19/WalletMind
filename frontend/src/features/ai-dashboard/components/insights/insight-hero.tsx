import { Bot, Clock3, Gauge } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { SectionCard } from "@/features/ai-dashboard/components/section-card";

type InsightHeroProps = {
  summary: string;
  confidenceLabel: string;
  generatedAtLabel: string;
};

export function InsightHero({
  summary,
  confidenceLabel,
  generatedAtLabel,
}: InsightHeroProps) {
  return (
    <SectionCard
      title="AI Spending Insights"
      description="Narrative intelligence generated from deterministic transaction analysis."
      className="bg-gradient-to-r from-[var(--surface)] to-[var(--surface-soft)]"
      action={<Badge variant="muted">Insight Engine</Badge>}
    >
      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-1 text-xs text-[var(--text-muted)]">
            <Bot className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
            AI Summary
          </div>
          <p className="text-sm leading-relaxed text-[var(--text)]">
            {summary}
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-3">
            <div className="mb-2 inline-flex items-center gap-2 text-xs uppercase tracking-wide text-[var(--text-muted)]">
              <Gauge className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
              Insight Confidence
            </div>
            <p className="text-lg font-semibold">{confidenceLabel}</p>
          </div>

          <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-3">
            <div className="mb-2 inline-flex items-center gap-2 text-xs uppercase tracking-wide text-[var(--text-muted)]">
              <Clock3 className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
              Generation Timestamp
            </div>
            <p className="text-sm font-medium">{generatedAtLabel}</p>
          </div>
        </div>
      </div>
    </SectionCard>
  );
}
