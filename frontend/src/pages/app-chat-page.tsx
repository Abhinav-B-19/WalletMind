import { EmptyState } from "@/components/ui/empty-state";
import { PageTitle } from "@/components/ui/section-title";

export function AppChatPage() {
  return (
    <div className="space-y-5">
      <PageTitle
        title="AI Assistant"
        subtitle="Conversational financial guidance will be connected in future stories."
      />
      <EmptyState
        title="AI Assistant Placeholder"
        description="AI chat integration is intentionally excluded from this story."
      />
    </div>
  );
}
