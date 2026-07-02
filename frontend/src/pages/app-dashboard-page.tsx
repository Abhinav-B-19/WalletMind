import { EmptyState } from "@/components/ui/empty-state";
import { PageTitle } from "@/components/ui/section-title";

export function AppDashboardPage() {
  return (
    <div className="space-y-5">
      <PageTitle
        title="Dashboard"
        subtitle="Portfolio and financial health summaries will be added later."
      />
      <EmptyState
        title="Dashboard Placeholder"
        description="Analytics and visual insights remain out of scope for this story."
      />
    </div>
  );
}
