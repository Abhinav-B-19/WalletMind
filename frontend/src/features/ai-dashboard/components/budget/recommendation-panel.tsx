import { Lightbulb } from "lucide-react";

import { AIUnavailableCard } from "@/features/ai-dashboard/components/ai-unavailable-card";
import { SectionCard } from "@/features/ai-dashboard/components/section-card";

type RecommendationPanelProps = {
  recommendations: string[];
  aiUnavailable: boolean;
  onRetry: () => void;
};

export function RecommendationPanel({
  recommendations,
  aiUnavailable,
  onRetry,
}: RecommendationPanelProps) {
  return (
    <SectionCard
      title="AI Guidance"
      description="Actionable narrative guidance derived from deterministic budget results."
    >
      {aiUnavailable ? (
        <AIUnavailableCard onRetry={onRetry} />
      ) : recommendations.length === 0 ? (
        <p className="text-sm text-[var(--text-muted)]">
          No AI recommendations are currently available.
        </p>
      ) : (
        <ul className="space-y-3" aria-label="AI recommendations list">
          {recommendations.map((recommendation) => (
            <li
              key={recommendation}
              className="flex gap-3 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-3 shadow-sm"
            >
              <span className="mt-0.5 text-[#4f8df7]">
                <Lightbulb className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
              </span>
              <p className="text-sm text-[var(--text)]">{recommendation}</p>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}
