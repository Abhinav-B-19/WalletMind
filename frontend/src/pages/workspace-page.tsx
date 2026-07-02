import {
  Calendar,
  FileUp,
  FolderKanban,
  Sparkles,
  Target,
  Wallet,
} from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { PageTitle, SectionTitle } from "@/components/ui/section-title";
import { getStoredUser } from "@/lib/auth/storage";

const QUICK_ACTIONS = [
  { title: "Upload Statement", icon: FileUp, href: "/app/statements", comingSoon: false },
  { title: "View Statements", icon: FolderKanban, href: "/app/statements", comingSoon: false },
  { title: "AI Analysis", icon: Sparkles, href: "/app/chat", comingSoon: true },
  { title: "Planner", icon: Target, href: "/app/planner", comingSoon: true },
];

const UPCOMING_FEATURES = [
  "Expense Intelligence",
  "Financial Planner",
  "AI Financial Coach",
  "Smart Budgeting",
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
        subtitle="Your personal digital wallet workspace foundation is ready."
      />

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Welcome back, {user?.name ?? "User"}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
              <p className="text-xs text-[var(--text-muted)]">Occupation</p>
              <p className="text-sm font-semibold">{user?.occupation ?? "Not set"}</p>
            </div>
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
              <p className="text-xs text-[var(--text-muted)]">Monthly Income</p>
              <p className="text-sm font-semibold">{user?.monthly_income ?? "Not set"}</p>
            </div>
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
              <p className="text-xs text-[var(--text-muted)]">Currency</p>
              <p className="text-sm font-semibold">USD</p>
            </div>
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3">
              <p className="text-xs text-[var(--text-muted)]">Primary Financial Goal</p>
              <p className="text-sm font-semibold">Financial Planning</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Financial Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center justify-between rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
              <span className="text-[var(--text-muted)]">Name</span>
              <span>{user?.name ?? "Not set"}</span>
            </div>
            <div className="flex items-center justify-between rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
              <span className="text-[var(--text-muted)]">Occupation</span>
              <span>{user?.occupation ?? "Not set"}</span>
            </div>
            <div className="flex items-center justify-between rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
              <span className="text-[var(--text-muted)]">Income</span>
              <span>{user?.monthly_income ?? "Not set"}</span>
            </div>
            <div className="flex items-center justify-between rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
              <span className="text-[var(--text-muted)]">Currency</span>
              <span>USD</span>
            </div>
            <div className="flex items-center justify-between rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
              <span className="text-[var(--text-muted)]">Goal</span>
              <span>Financial Planning</span>
            </div>
            <div className="flex items-center justify-between rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2">
              <span className="inline-flex items-center gap-2 text-[var(--text-muted)]">
                <Calendar className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
                Registration Date
              </span>
              <span>{registrationDate}</span>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4">
        <SectionTitle
          title="Quick Actions"
          subtitle="Move quickly through your wallet workspace."
        />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {QUICK_ACTIONS.map(({ title, icon: Icon, href, comingSoon }) => (
            <Card key={title} className="transition-transform hover:translate-y-[-1px]">
              <CardContent className="space-y-3 p-4">
                <div className="inline-flex items-center rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-2.5 py-2">
                  <Icon className="h-[var(--icon-md)] w-[var(--icon-md)] text-[var(--primary)]" />
                </div>
                <p className="text-sm font-semibold">{title}</p>
                <Button asChild size="sm" variant="secondary" className="w-full">
                  <Link to={href}>{comingSoon ? "Coming Soon" : "Open"}</Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Statements</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <EmptyState
              title="No statements uploaded yet."
              description="Start by uploading your first bank statement to build your wallet timeline."
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
              title="No analysis queue yet"
              description="Your uploaded bank statements will appear here and become ready for AI analysis."
            />
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4">
        <SectionTitle
          title="Upcoming Features"
          subtitle="Your next set of intelligent wallet capabilities."
        />
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          {UPCOMING_FEATURES.map((feature) => (
            <Card key={feature}>
              <CardContent className="space-y-2 p-4">
                <p className="text-sm font-semibold">{feature}</p>
                <p className="inline-flex items-center gap-2 text-xs text-[var(--text-muted)]">
                  <Wallet className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
                  Coming Soon
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
