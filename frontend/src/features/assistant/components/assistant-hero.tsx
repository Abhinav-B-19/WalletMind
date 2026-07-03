import { Badge } from "@/components/ui/badge";
import { SectionCard } from "@/features/ai-dashboard/components/section-card";

type AssistantHeroProps = {
  status: "Ready" | "Generating";
  selectedStatementLabel: string;
};

export function AssistantHero({
  status,
  selectedStatementLabel,
}: AssistantHeroProps) {
  return (
    <SectionCard
      title="AI Financial Assistant"
      description="Ask grounded questions about your selected statement with transaction-backed answers."
      action={<Badge variant="muted">{status}</Badge>}
    >
      <div className="grid gap-2 text-sm text-[var(--text-muted)]">
        <p>Conversation status: {status}</p>
        <p>Statement: {selectedStatementLabel}</p>
      </div>
    </SectionCard>
  );
}
