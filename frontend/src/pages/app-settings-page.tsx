import { EmptyState } from "@/components/ui/empty-state";
import { PageTitle } from "@/components/ui/section-title";

export function AppSettingsPage() {
  return (
    <div className="space-y-5">
      <PageTitle
        title="Settings"
        subtitle="Profile and personalization settings will expand in future stories."
      />
      <EmptyState
        title="Settings Placeholder"
        description="Only layout-level routing is implemented in this story."
      />
    </div>
  );
}
