import { Link } from "react-router-dom";

import { PageWrapper } from "@/components/layout/page-wrapper";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageTitle, SectionTitle } from "@/components/ui/section-title";
import { StatCard } from "@/components/ui/stat-card";

export function HomePage() {
  return (
    <PageWrapper>
      <div className="space-y-6">
        <PageTitle
          title="Welcome to WalletMind"
          subtitle="AI Financial Concierge onboarding flow."
        />

        <section className="grid gap-3 md:grid-cols-3">
          <StatCard label="Experience" value="Onboarding" />
          <StatCard label="Auth" value="Local Session" />
          <StatCard label="Workspace" value="Protected" />
        </section>

        <div className="space-y-3">
          <SectionTitle
            title="Get Started"
            subtitle="Create your WalletMind profile or continue with an existing one."
          />
          <EmptyState
            title="Profile-Based Access"
            description="Registration acts as onboarding for this phase. Workspace access requires a locally stored profile."
          />
          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <Link to="/register">Get Started</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link to="/login">Continue</Link>
            </Button>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}
