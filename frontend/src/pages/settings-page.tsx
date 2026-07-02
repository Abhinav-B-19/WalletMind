import { PageWrapper } from "@/components/layout/page-wrapper";
import { EmptyState } from "@/components/ui/empty-state";
import { PageTitle } from "@/components/ui/section-title";

export function SettingsPage() {
  return (
    <PageWrapper>
      <div className="space-y-5">
        <PageTitle
          title="Settings"
          subtitle="Theme and profile settings will be wired in future stories."
        />
        <EmptyState
          title="Settings Placeholder"
          description="Design system-compliant shell page with no business logic."
        />
      </div>
    </PageWrapper>
  );
}
