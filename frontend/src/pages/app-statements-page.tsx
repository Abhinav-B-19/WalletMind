import { EmptyState } from "@/components/ui/empty-state";
import { PageTitle } from "@/components/ui/section-title";

export function AppStatementsPage() {
  return (
    <div className="space-y-5">
      <PageTitle
        title="Statement Library"
        subtitle="All uploaded statements will appear here in future stories."
      />
      <EmptyState
        title="No Statements Yet"
        description="Upload Statement remains a placeholder in this story."
      />
    </div>
  );
}
