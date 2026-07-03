import { PageTitle } from "@/components/ui/section-title";
import { AIUnavailableCard } from "@/features/ai-dashboard/components/ai-unavailable-card";

export function AppChatPage() {
  return (
    <div className="space-y-5">
      <PageTitle
        title="AI Assistant"
        subtitle="Conversational guidance is being prepared. Deterministic analysis remains available in dashboard and health views."
      />
      <AIUnavailableCard onRetry={() => window.location.reload()} />
    </div>
  );
}
