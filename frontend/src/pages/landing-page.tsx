import { Link } from "react-router-dom";
import {
  Bot,
  FileUp,
  FolderKanban,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";

import { PageWrapper } from "@/components/layout/page-wrapper";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageTitle, SectionTitle } from "@/components/ui/section-title";

const FEATURES = [
  {
    title: "Upload Statements",
    description: "Supports PDF, CSV, XLS, XLSX, and image-based statements.",
    icon: FileUp,
  },
  {
    title: "Expense Intelligence",
    description:
      "Automatically categorize transactions and identify spending behaviour.",
    icon: TrendingUp,
  },
  {
    title: "Financial Planning",
    description:
      "Generate personalized recommendations and budgeting strategies.",
    icon: Target,
  },
  {
    title: "AI Financial Coach",
    description:
      "Ask questions naturally and receive intelligent financial guidance.",
    icon: Bot,
  },
];

const WORKFLOW_STEPS = [
  "Create Profile",
  "Upload Statements",
  "AI Analysis",
  "Financial Action Plan",
];

export function HomePage() {
  return (
    <div className="space-y-6">
      <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <PageWrapper>
          <div className="space-y-6">
            <PageTitle title="WalletMind" subtitle="AI Financial Concierge" />
            <div className="space-y-3">
              <p className="text-2xl font-semibold tracking-tight md:text-3xl">
                Transform your bank statements into personalized financial
                insights powered by AI.
              </p>
              <p className="max-w-3xl text-sm leading-relaxed text-[var(--text-muted)] md:text-base">
                WalletMind analyzes your financial data, understands your
                spending behaviour, generates intelligent insights, helps plan
                your finances and provides an AI financial coach.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button asChild>
                <Link to="/register">Get Started</Link>
              </Button>
              <Button asChild variant="secondary">
                <Link to="/login">Continue</Link>
              </Button>
            </div>
          </div>
        </PageWrapper>

        <Card className="overflow-hidden bg-[var(--surface)]/95">
          <CardHeader>
            <CardTitle className="text-lg">Workspace Preview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-4">
              <p className="text-sm font-semibold">Welcome back</p>
              <p className="text-xs text-[var(--text-muted)]">
                Your financial workspace is ready.
              </p>
            </div>

            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-[var(--text-muted)]">
                Quick Actions
              </p>
              <div className="grid gap-2 sm:grid-cols-2">
                {[
                  "Upload Statement",
                  "Statement Library",
                  "AI Analysis",
                  "Planner",
                ].map((item) => (
                  <div
                    key={item}
                    className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2 text-xs text-[var(--text-muted)]"
                  >
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-4">
              <div className="flex items-center justify-between text-sm">
                <span className="font-semibold">Recent Statements</span>
                <FolderKanban className="h-[var(--icon-md)] w-[var(--icon-md)] text-[var(--text-muted)]" />
              </div>
              <p className="mt-2 text-xs text-[var(--text-muted)]">
                3 files uploaded • Ready for Analysis
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4">
        <SectionTitle
          title="Features"
          subtitle="A complete financial intelligence platform designed for clarity and action."
        />
        <div className="grid gap-4 md:grid-cols-2">
          {FEATURES.map(({ title, description, icon: Icon }) => (
            <Card key={title}>
              <CardContent className="space-y-3 p-5">
                <div className="inline-flex items-center rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-2.5 py-2">
                  <Icon className="h-[var(--icon-md)] w-[var(--icon-md)] text-[var(--primary)]" />
                </div>
                <h3 className="text-base font-semibold">{title}</h3>
                <p className="text-sm text-[var(--text-muted)]">
                  {description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <SectionTitle
          title="How It Works"
          subtitle="A simple path from raw statements to confident financial action."
        />
        <Card>
          <CardContent className="p-5">
            <div className="grid gap-2 md:grid-cols-4 md:items-center">
              {WORKFLOW_STEPS.map((step, index) => (
                <div key={step} className="flex items-center gap-2">
                  <div className="grid h-7 w-7 place-items-center rounded-full bg-[var(--primary-soft)] text-xs font-semibold text-[var(--text)]">
                    {index + 1}
                  </div>
                  <span className="text-sm">{step}</span>
                  {index < WORKFLOW_STEPS.length - 1 ? (
                    <Sparkles className="ml-auto hidden h-[var(--icon-sm)] w-[var(--icon-sm)] text-[var(--text-muted)] md:block" />
                  ) : null}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
