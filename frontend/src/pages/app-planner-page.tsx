import { EmptyState } from "@/components/ui/empty-state";
import { PageTitle } from "@/components/ui/section-title";

export function AppPlannerPage() {
  return (
    <div className="space-y-5">
      <PageTitle
        title="Planner"
        subtitle="Goal planning and recommendations will be enabled in later stories."
      />
      <EmptyState
        title="Planner Placeholder"
        description="Planner logic is intentionally not implemented in this correction story."
      />
    </div>
  );
}
