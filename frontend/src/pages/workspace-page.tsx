import {
  ArrowRight,
  FileUp,
  FolderKanban,
  Landmark,
  Map,
  PiggyBank,
  Sparkles,
  Target,
  WalletCards,
} from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { PageTitle, SectionTitle } from "@/components/ui/section-title";
import { StatCard } from "@/components/ui/stat-card";
import { getStoredUser } from "@/lib/auth/storage";

const QUICK_ACTIONS = [
  {
    title: "Upload Statement",
    description: "Add a new bank statement to your secure wallet library.",
    icon: FileUp,
    href: "/app/statements",
    comingSoon: false,
  },
  {
    title: "Statement Library",
    description: "Browse, manage, and organize uploaded financial statements.",
    icon: FolderKanban,
    href: "/app/statements",
    comingSoon: false,
  },
  { title: "AI Analysis", icon: Sparkles, href: "/app/chat", comingSoon: true },
  { title: "Planner", icon: Target, href: "/app/planner", comingSoon: true },
];

const UPCOMING_FEATURES = [
  { title: "Expense Intelligence", icon: WalletCards },
  { title: "Financial Planner", icon: Map },
  { title: "AI Financial Coach", icon: Sparkles },
  { title: "Smart Budgeting", icon: PiggyBank },
];

export function WorkspacePage() {
  const user = getStoredUser();
  const registrationDate = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date());

  return (
    <div className="space-y-6">
      <PageTitle
        title="Home"
        subtitle="Your WalletMind workspace is ready for focused financial action."
      />

      <section>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              Welcome back, {user?.name ?? "User"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-[var(--text-muted)]">
              Let&apos;s continue building your financial future.
            </p>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Monthly Income"
          value={user?.monthly_income ? `${user.monthly_income}` : "Not set"}
        />
        <StatCard label="Currency" value="USD" />
        <StatCard label="Primary Financial Goal" value="Financial Planning" />
        <StatCard label="Registered Since" value={registrationDate} />
      </section>

      <section className="space-y-4">
        <SectionTitle
          title="Quick Actions"
          subtitle="Move quickly through your wallet workspace."
        />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {QUICK_ACTIONS.map(
            ({ title, description, icon: Icon, href, comingSoon }) => (
              <Card
                key={title}
                className="h-full transition-transform hover:translate-y-[-1px]"
              >
                <CardContent className="flex h-full flex-col gap-4 p-5">
                  <div className="inline-flex items-center self-start rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-2.5 py-2">
                    <Icon className="h-[var(--icon-lg)] w-[var(--icon-lg)] text-[var(--primary)]" />
                  </div>
                  <div className="space-y-2">
                    <p className="text-base font-semibold">{title}</p>
                    <p className="text-sm text-[var(--text-muted)]">
                      {description ??
                        "Feature will be available in an upcoming release."}
                    </p>
                  </div>
                  <Button
                    asChild
                    size="sm"
                    variant="secondary"
                    className="mt-auto w-full justify-between"
                  >
                    <Link to={href}>
                      {comingSoon ? "Coming Soon" : "Open"}
                      <ArrowRight className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            ),
          )}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Statements</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <EmptyState
              title="No statements in your library yet"
              description="Upload your first statement to begin your WalletMind timeline and unlock smart insights."
              icon={Landmark}
            />
            <Button asChild>
              <Link to="/app/statements">Upload your first statement</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Ready For Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <EmptyState
              title="Nothing queued for AI analysis"
              description="Once statements are uploaded, they will appear here as ready-to-analyze files for WalletMind AI."
              icon={Sparkles}
            />
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4">
        <SectionTitle
          title="Upcoming Features"
          subtitle="Compact roadmap for upcoming wallet capabilities."
        />
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          {UPCOMING_FEATURES.map(({ title, icon: Icon }) => (
            <Card key={title}>
              <CardContent className="flex items-center justify-between gap-3 p-4">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold">{title}</p>
                  <Badge variant="muted" className="mt-2">
                    Coming Soon
                  </Badge>
                </div>
                <Icon className="h-[var(--icon-md)] w-[var(--icon-md)] flex-shrink-0 text-[var(--text-muted)]" />
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
