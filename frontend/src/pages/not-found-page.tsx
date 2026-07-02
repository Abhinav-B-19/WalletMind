import { Link } from "react-router-dom";

import { PageWrapper } from "@/components/layout/page-wrapper";
import { Button } from "@/components/ui/button";
import { PageTitle } from "@/components/ui/section-title";

export function NotFoundPage() {
  return (
    <PageWrapper>
      <div className="space-y-5">
        <PageTitle
          title="Page Not Found"
          subtitle="The route does not exist in the current WalletMind shell."
        />
        <Button asChild variant="secondary">
          <Link to="/">Back to Home</Link>
        </Button>
      </div>
    </PageWrapper>
  );
}
