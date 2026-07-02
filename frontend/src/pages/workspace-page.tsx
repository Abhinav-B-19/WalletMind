import { EmptyState } from "@/components/ui/empty-state";
import { PageTitle } from "@/components/ui/section-title";
import { getStoredUser } from "@/lib/auth/storage";

export function WorkspacePage() {
  const user = getStoredUser();

  return (
    <div className="space-y-5">
      <PageTitle
        title="Home"
        subtitle={`Welcome${user ? `, ${user.name}` : ""}. Your WalletMind workspace modules are structured and ready for upcoming stories.`}
      />
      <EmptyState
        title="Workspace Home"
        description="Statement Upload, Planner, Dashboard, AI Chat, Analytics, Gemini, Parser, and Budgets remain placeholders by design in this story."
      />
    </div>
  );
}
